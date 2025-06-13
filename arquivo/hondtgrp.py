import pandas as pd
from math import floor
from google.cloud import bigquery
from collections import defaultdict


"""
    Allocates mandates to parties and groups of parties in all districts of Portugal using the Hondt method.
"""

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
    https://chat.deepseek.com/a/chat/s/4d868fe5-2ae4-4177-aac5-184c61792f59
    
    Args:
        district_name (str): Name of the district to analyze
        df (pd.DataFrame): DataFrame containing election data with columns:
                           - distrito: district name
                           - partido: party name
                           - votos: votes received
                           - mandatos: mandates actually allocated
    
    Returns:
        results (dict): A dictionary with parties as keys and allocated mandates as values
        label_votes (dict): A dictionary with labels as keys and votes as values
        parties (dict): A dictionary with parties as keys and votes as values
    """

    # Initialize the results dict
    results = {
        'by_party': defaultdict(int),
        'by_label': defaultdict(int)
    }
    
    district_data = df[df['distrito'] == district_name] # a panda dataframe
    total_mandates = district_data['mandatos'].sum()
    print(f"\nMANDATOS DE {district_name}:")
    
    # Party-level calculation
    # Get parties and their votes - ROBUST exclusion of blanks/nulls
    valid_parties = district_data[
        # Case-insensitive check for blank/null votes
        (~district_data['partido'].str.lower().str.contains('branco|nulo', na=False)) &
        # Ensure votes are positive numbers
        (district_data['votos'] > 0)
    ] # valid_parties is a panda dataframe

     # Convert valid_parties to panda series and then to {party: votes} dictionary
    parties = valid_parties.set_index('partido')['votos'].to_dict()

    # Create a dict with parties as keys and 0 as values
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
            print("   ", party, count, parties[party])
        
    print("POR AGRUPAMENTO:")
    for label, count in label_mandates.items():
        results['by_label'][label] += count
        if count > 0:
            print("   ", label, count, label_votes[label])

    return parties, label_votes, results


# Get election data from BigQuery table
client = bigquery.Client(project=PROJECTO)
query = f"""
SELECT codigo, distrito, partido, votos, mandatos, timestamp
FROM {PROJECTO}.{DATASET}.{TABELA}
"""
election_data = client.query(query).to_dataframe()

# Initialize tracking dicts
deps = {
    'parties': defaultdict(int),
    'labels': defaultdict(int)  # Single dimension
}
votes = { 
    'parties': defaultdict(int),
    'labels': defaultdict(int)
}
    
# Process each district
for distrito in DISTRITOS:
    party_votes, label_votes, mandate_allocation = allocate_mandates_hondt(distrito, election_data)
    
    for party, mandates in mandate_allocation['by_party'].items():
        if mandates > 0:
            # Update party totals
            deps['parties'][party] += mandates

    for label, mandates in mandate_allocation['by_label'].items():
        if mandates > 0:        
            # Update label totals 
            deps['labels'][label] += mandates

    for label, v in label_votes.items():
        votes['labels'][label] += v

    for party, v in party_votes.items():
        votes['parties'][party] += v


# Convert to regular dicts for output
# to raise KeyError for invalid keys, serialize (e.g., JSON) or share results
final_results = {
    'by_party': dict(deps['parties']),
    'by_label': dict(deps['labels'])
}
final_votes = {
    'by_party': dict(votes['parties']),
    'by_label': dict(votes['labels'])
}



# Final national totals
print("\nTOTAIS NACIONAIS")
print("============================")
print("\nPOR PARTIDO:")
total_votes = sum(final_votes['by_party'].values())
significantes = 0
for party, count in sorted(final_results['by_party'].items(), key=lambda x: -x[1]):
    print(f"   {party}: {count}, {final_votes['by_party'][party]}, {final_votes['by_party'][party]/total_votes}")
    significantes += final_votes['by_party'][party]
print(f"Sem mandatos: {total_votes - significantes}, {(total_votes - significantes)/total_votes}")

total_votes = sum(final_votes['by_label'].values())
significantes = 0
print("POR AGRUPAMENTO:")
for label, count in sorted(final_results['by_label'].items(), key=lambda x: -x[1]):
    print(f"   {label}: {count}, {final_votes['by_label'][label]}, {final_votes['by_label'][label]/total_votes}")
    significantes += final_votes['by_label'][label]
print(f"Sem mandatos: {total_votes - significantes}, {(total_votes - significantes)/total_votes}")

