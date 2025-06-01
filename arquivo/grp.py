import pandas as pd
from math import floor
from google.cloud import bigquery
from collections import defaultdict

# Configuração
PROJECTO = "apps-448519"
DATASET = "AR25"
TABELA = "resultadosporcirculo"

DISTRITOS = [
    "Aveiro",
    "Beja",
    "Braga",
    "Bragança",
    "Castelo Branco",
    "Coimbra",
    "Évora",
    "Faro",
    "Guarda",
    "Leiria",
    "Lisboa",
    "Portalegre",
    "Porto",
    "Santarém",
    "Setúbal",
    "Viana do Castelo",
    "Vila Real",
    "Viseu",
    "Madeira",
    "Açores",
    "Europa",
    "Resto do Mundo"
]

PARTIDOS = {
    "Votos em branco": ['Outros'],
    "Votos nulos": ['Outros'],
    "PPD/PSD.CDS-PP": ['D'],
    "PS": ['E'],
    "CH": ['D'],
    "IL": ['D'],
    "L": ['E'],
    "B.E.": ['E'],
    "ADN": ['Outros'],
    "PAN": ['E'],
    "PCP-PEV": ['E'],
    "PCTP/MRPP": ['Outros'],
    "R.I.R.": ['Outros'],
    "VP": ['Outros'],
    "E": ['Outros'],
    "ND": ['Outros'],
    "NC": ['Outros'],
    "PPM": ['Outros'],
    "JPP": ['Outros'],
    "PLS": ['Outros'],
    "PTP": ['Outros'],
    "MPT": ['Outros'],
    "PPD/PSD.CDS-PP.PPM": ['D']
}


def allocate_mandates_hondt(district_name, df):
    """
    Allocates mandates to parties in a district using the Hondt method.
    
    Args:
        district_name (str): Name of the district to analyze
        df (pd.DataFrame): DataFrame containing election data with columns:
                           - distrito: district name
                           - partido: party name
                           - votos: votes received
                           - mandatos: mandates to allocate (will be summed)
    
    Returns:
        dict: A dictionary with parties as keys and allocated mandates as values
    """
    
    # --- Validation ---
    label_lengths = {len(labels) for labels in PARTIDOS.values()}
    if len(label_lengths) != 1:
        raise ValueError("All parties must have the same number of labels")
    n_dimensions = label_lengths.pop()
    
    # --- Standard party-level Hondt ---
    district_data = df[df['distrito'] == district_name]
    total_mandates = district_data['mandatos'].sum()
    
    # Get parties and their votes - ROBUST exclusion of blanks/nulls
    valid_parties = district_data[
        # Case-insensitive check for blank/null votes
        (~district_data['partido'].str.lower().str.contains('branco|nulo', na=False)) &
        # Ensure votes are positive numbers
        (district_data['votos'] > 0)
    ]

     # Convert to {party: votes} dictionary
    parties = valid_parties.set_index('partido')['votos'].to_dict()
    
    party_mandates = {p: 0 for p in parties}
    for _ in range(total_mandates):
        quotients = {p: v/(party_mandates[p]+1) for p,v in parties.items()}
        winner = max(quotients.items(), key=lambda x: x[1])[0]
        party_mandates[winner] += 1
    
    # --- Dynamic grouping calculations ---
    results = {'POR PARTIDO': party_mandates}
    
    for dim in range(n_dimensions):
        dim_votes = {}
        for party, mandates in party_mandates.items():
            label = PARTIDOS[party][dim]
            dim_votes[label] = dim_votes.get(label, 0) + mandates
        
        dim_mandates = {l:0 for l in dim_votes}
        for _ in range(total_mandates):
            quotients = {l:v/(dim_mandates[l]+1) for l,v in dim_votes.items()}
            winner = max(quotients.items(), key=lambda x: x[1])[0]
            dim_mandates[winner] += 1
        
        results[f'AGRUPAMENTO {dim+1}'] = dim_mandates
        
    return results



client = bigquery.Client(project=PROJECTO)
query = f"""
SELECT codigo, distrito, partido, votos, mandatos, timestamp
FROM {PROJECTO}.{DATASET}.{TABELA}
"""
election_data = client.query(query).to_dataframe()

# Initialize tracking dictionaries
deps = {
    'parties': defaultdict(int),          # Tracks party totals
    'labels': [defaultdict(int) for _ in range(len(next(iter(PARTIDOS.values()))))]  # One per label dimension
}

for district_name in DISTRITOS:
    # Get district results (using your existing function)
    mandate_allocation = allocate_mandates_hondt(district_name, election_data)
    
    print(f"\nMANDATOS DE {district_name}:")
    # 1. Process party-level mandates
    print("POR PARTIDO:")
    for party, mandates in mandate_allocation['POR PARTIDO'].items():
        if mandates > 0:
            deps['parties'][party] += mandates
            print(f"   {party}: {mandates} mandatos")
    # 2. Process label-level mandates (if needed)
    print("POR AGRUPAMENTO:")
    for dim in range(len(next(iter(PARTIDOS.values())))):
        print(f"AGRUPAMENTO {dim+1}:")
        for party, mandates in mandate_allocation[f'AGRUPAMENTO {dim+1}'].items():
            if mandates > 0:
                deps['labels'][dim][party] += mandates
                print(f"   {party}: {mandates} mandatos")
    
# Final national totals
print("\nTOTAIS NACIONAIS")
print("============================")
print("\nPOR PARTIDO:")
for party, count in sorted(deps['parties'].items(), key=lambda x: -x[1]):
    print(f"   {party}: {count}")

print("POR AGRUPAMENTO:")
for dim, label_counts in enumerate(deps['labels']):
    print(f"AGRUPAMENTO {dim+1}:")  # Customize dimension names
    for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
        print(f"   {label}: {count}")