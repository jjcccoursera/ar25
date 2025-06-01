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
    "PPD/PSD.CDS-PP": ['PPD+CDS+IL+CH'],
    "PS": ['L+BE+PCP+PAN+PS'],
    "CH": ['PPD+CDS+IL+CH'],
    "IL": ['PPD+CDS+IL+CH'],
    "L": ['L+BE+PCP+PAN+PS'],
    "B.E.": ['L+BE+PCP+PAN+PS'],
    "ADN": ['ADN'],
    "PAN": ['L+BE+PCP+PAN+PS'],
    "PCP-PEV": ['L+BE+PCP+PAN+PS'],
    "PCTP/MRPP": ['PCTP/MRPP'],
    "R.I.R.": ['R.I.R.'],
    "VP": ['VP'],
    "E": ['E'],
    "ND": ['ND'],
    "NC": ['NC'],
    "PPM": ['PPM'],
    "JPP": ['JPP'],
    "PLS": ['PLS'],
    "PTP": ['PTP'],
    "MPT": ['MPT'],
    "PPD/PSD.CDS-PP.PPM": ['PPD+CDS+IL+CH']
}

def allocate_mandates_hondt(district_name, df):

    """
    Allocates mandates to parties and groups of parties in a district using the Hondt method.
    
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

    # Initialize
    results = {
        'by_party': defaultdict(int),
        'by_label': defaultdict(int)
    }
    
    district_data = df[df['distrito'] == district_name]
    total_mandates = district_data['mandatos'].sum()
    print(f"\nMANDATOS DE {district_name}:")
    
    # Party-level calculation
    # Get parties and their votes - ROBUST exclusion of blanks/nulls
    valid_parties = district_data[
        # Case-insensitive check for blank/null votes
        (~district_data['partido'].str.lower().str.contains('branco|nulo', na=False)) &
        # Ensure votes are positive numbers
        (district_data['votos'] > 0)
    ]

     # Convert to {party: votes} dictionary
    parties = valid_parties.set_index('partido')['votos'].to_dict()

    party_mandates = {p:0 for p in parties}
    
    for _ in range(total_mandates):
        quotients = {p:v/(party_mandates[p]+1) for p,v in parties.items()}
        winner = max(quotients.items(), key=lambda x: x[1])[0]
        party_mandates[winner] += 1
    
    # Label-level calculation (separate Hondt!)
    label_votes = defaultdict(int)
    for party, votes in parties.items():
        if party in PARTIDOS:
            label = PARTIDOS[party][0]  # Get the label string (e.g., 'E')
        else:
            print(f"Warning: No label defined for party '{party}'")
        label_votes[label] += votes
            
    label_mandates = {l:0 for l in label_votes}
    for _ in range(total_mandates):
        quotients = {l:v/(label_mandates[l]+1) for l,v in label_votes.items()}
        winner = max(quotients.items(), key=lambda x: x[1])[0]
        label_mandates[winner] += 1
    
    # Update results
    print("POR PARTIDO:")
    for party, count in party_mandates.items():
        results['by_party'][party] += count
        if count > 0:
            print("   ", party, count)
        
    print("POR AGRUPAMENTO:")
    for label, count in label_mandates.items():
        results['by_label'][label] += count
        if count > 0:
            print("   ", label, count)

    return results


client = bigquery.Client(project=PROJECTO)
query = f"""
SELECT codigo, distrito, partido, votos, mandatos, timestamp
FROM {PROJECTO}.{DATASET}.{TABELA}
"""
election_data = client.query(query).to_dataframe()

# Initialize tracking dictionaries
deps = {
    'parties': defaultdict(int),
    'labels': defaultdict(int)  # Single dimension
}

# Get all unique labels (assuming 1 label per party here)
# grupos = {labels[0] for labels in PARTIDOS.values()}  # Using set comprehension
    
# Process each district
for distrito in DISTRITOS:
    mandate_allocation = allocate_mandates_hondt(distrito, election_data)
    # print(distrito, mandate_allocation)

    for party, mandates in mandate_allocation['by_party'].items():
        if mandates > 0:
            # Update party totals
            deps['parties'][party] += mandates

    for label, mandates in mandate_allocation['by_label'].items():
        if mandates > 0:        
            # Update label totals 
            deps['labels'][label] += mandates

# Convert to regular dicts for output
final_results = {
    'by_party': dict(deps['parties']),
    'by_label': dict(deps['labels'])
}

# Final national totals
print("\nTOTAIS NACIONAIS")
print("============================")
print("\nPOR PARTIDO:")
for party, count in sorted(final_results['by_party'].items(), key=lambda x: -x[1]):
    print(f"   {party}: {count}")

print("POR AGRUPAMENTO:")
for label, count in sorted(final_results['by_label'].items(), key=lambda x: -x[1]):
    print(f"   {label}: {count}")

