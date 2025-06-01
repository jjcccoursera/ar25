import pandas as pd
from math import floor
from google.cloud import bigquery

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

PARTIDOS = [
    "Votos em branco",
    "Votos nulos",
    "PPD/PSD.CDS-PP",
    "PS",
    "CH",
    "IL",
    "L",
    "B.E.",
    "ADN",
    "PAN",
    "PCP-PEV",
    "PCTP/MRPP",
    "R.I.R.",
    "VP",
    "E",
    "ND",
    "NC",
    "PPM",
    "JPP",
    "PLS",
    "PTP",
    "MPT",
    "PPD/PSD.CDS-PP.PPM"
]


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
    # Filter data for the specified district
    district_data = df[df['distrito'] == district_name].copy()
    
    if district_data.empty:
        raise ValueError(f"No data found for district: {district_name}")
    
    # Calculate total mandates to allocate (sum of all mandatos in the district)
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
    
    # Initialize mandates for each party
    mandates = {party: 0 for party in parties.keys()}
    
    # Apply Hondt method
    for _ in range(total_mandates):
        # Calculate quotients for each party
        quotients = {
            party: votes / (mandates[party] + 1)
            for party, votes in parties.items()
        }
        
        # Find party with highest quotient
        winning_party = max(quotients.items(), key=lambda x: x[1])[0]
        
        # Allocate one mandate to this party
        mandates[winning_party] += 1
    
    return mandates


client = bigquery.Client(project=PROJECTO)
query = f"""
SELECT codigo, distrito, partido, votos, mandatos, timestamp
FROM {PROJECTO}.{DATASET}.{TABELA}
"""
election_data = client.query(query).to_dataframe()

deps = {partido: 0 for partido in PARTIDOS}

for district_name in DISTRITOS:
    mandate_allocation = allocate_mandates_hondt(district_name, election_data)
    print(f"Mandate allocation for {district_name}:")
    for party, mandates in mandate_allocation.items():
        if mandates > 0:
            deps[party] += mandates
            print(f"{party}: {mandates} mandates")
    print(deps)