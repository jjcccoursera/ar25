from flask import Flask, request, jsonify, abort, render_template, send_file
import pandas as pd
import math
from collections import defaultdict
import os


"""
    Allocates mandates to parties and groups of parties in all districts of Portugal using the Hondt method.

    Implantada no GAE em 250613

    A portar para Webdock
    https://copilot.microsoft.com/chats/X5X2VMkruAjhU2Gza5xug
    
"""

app = Flask(__name__, static_folder='static', static_url_path='/ar25/static')

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
    "Votos em branco": ['Votos em branco'],
    "Votos nulos": ['Votos nulos'],
    "PPD/PSD.CDS-PP": ['PPD+CDS+IL'],
    "PS": ['PS'],
    "CH": ['CH'],
    "IL": ['PPD+CDS+IL'],
    "L": ['L+BE+PCP+PAN'],
    "B.E.": ['L+BE+PCP+PAN'],
    "ADN": ['ADN'],
    "PAN": ['L+BE+PCP+PAN'],
    "PCP-PEV": ['L+BE+PCP+PAN'],
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
    "PPD/PSD.CDS-PP.PPM": ['PPD+CDS+IL']
}

# Get election data from csv file
election_data = pd.read_csv('resultadosporcirculo.csv')


# ======================
# 1. DATA PREPARATION
# ======================

# Build party-to-group mapping (more efficient lookup)
party_to_group = {}
for party_name, group_labels in PARTIDOS.items():
    # Each party maps to its group label (first/only item in list)
    group_name = group_labels[0]
    party_to_group[party_name] = group_name

# Initialize data structures with clear naming
raw_district_results = defaultdict(lambda: defaultdict(lambda: {'votos': 0, 'mandatos': 0}))
grouped_district_results = defaultdict(lambda: defaultdict(lambda: {'votos': 0, 'mandatos': 0}))

# ======================
# 2. PROCESS RAW DATA
# ======================

for _, row in election_data.iterrows():
    district_name = row['distrito']
    party_name = row['partido']
    votos = row['votos']
    mandatos = row.get('mandatos', 0)  # Using get() for safety
    
    # Store raw party results
    raw_district_results[district_name][party_name]['votos'] = votos
    raw_district_results[district_name][party_name]['mandatos'] = mandatos
    
    # Skip blank/null votos for group calculations
    # if party_name in ['Votos em branco', 'Votos nulos']:
    #    continue
    
    # Find which group this party belongs to
    group_name = party_to_group.get(party_name, party_name)  # Default to party if ungrouped
    
    # Aggregate votos for the group
    grouped_district_results[district_name][group_name]['votos'] += votos
    

# ======================
# 3. CALCULATE GROUP mandatos (D'HONDT)
# ======================

for district_name in grouped_district_results:
    # Get total mandatos to allocate in this district
    total_mandatos_in_district = sum(
        party_data['mandatos']
        for party_data in raw_district_results[district_name].values()
    )
    
    # Get eligible groups (exclude blanks/nulls)
    eligible_groups = {
        group_name: group_data['votos']
        for group_name, group_data in grouped_district_results[district_name].items()
        if group_name not in ['Votos em branco', 'Votos nulos']
    }
    
    # Initialize seat allocation
    group_mandatos = {group: 0 for group in eligible_groups}
    
    # D'Hondt allocation
    for _ in range(total_mandatos_in_district):
        # Calculate current quotients
        current_quotients = {
            group: votos / (group_mandatos[group] + 1)
            for group, votos in eligible_groups.items()
        }
        
        # Award seat to group with highest quotient
        winning_group = max(current_quotients.items(), key=lambda x: x[1])[0]
        group_mandatos[winning_group] += 1
    
    # Store results
    for group_name, mandatos in group_mandatos.items():
        grouped_district_results[district_name][group_name]['mandatos'] = mandatos

# ------------------------------------
#
# Sort parties by votes within each district

for district in raw_district_results:
    # Convert to list of (party, votes) tuples and sort by votes (descending)
    sorted_parties = sorted(
        raw_district_results[district].items(),
        key=lambda x: x[1]['votos'],
        reverse=True
    )
    
    # Create new ordered dictionary for this district
    ordered_parties = {}
    for party, votes in sorted_parties:
        ordered_parties[party] = votes
    
    # Update the district data
    raw_district_results[district] = ordered_parties

# Sort groups by votes within each district

for district in grouped_district_results:
    # Convert to list of (party, votes) tuples and sort by votes (descending)
    sorted_groups = sorted(
        grouped_district_results[district].items(),
        key=lambda x: x[1]['votos'],
        reverse=True
    )

    # Create new ordered dictionary for this district
    ordered_groups = {}
    for group, votes in sorted_groups:
        ordered_groups[group] = votes
    
    # Update the district data
    grouped_district_results[district] = ordered_groups

#
# ------------------------------------


# ======================
# 4. NATIONAL TOTALS
# ======================

# Initialize national totals as if they were a party
raw_district_results['Total Nacional'] = defaultdict(lambda: {'votos': 0, 'mandatos': 0})
grouped_district_results['Total Nacional'] = defaultdict(lambda: {'votos': 0, 'mandatos': 0})

# Calculate nationwide sums for each party/group
for district_name, groups in grouped_district_results.items():
    if district_name == 'Total Nacional': 
        continue

    for group_name, data in groups.items():
        grouped_district_results['Total Nacional'][group_name]['votos'] += data['votos']
        grouped_district_results['Total Nacional'][group_name]['mandatos'] += data['mandatos']

# ------------------------------------
#
national_totals = defaultdict(lambda: {'votos': 0, 'mandatos': 0})
for district_data in raw_district_results.values():
    for party, data in district_data.items():
        national_totals[party]['votos'] += data['votos']
        national_totals[party]['mandatos'] += data['mandatos']

# Filter out special categories and sort
valid_parties = [
    {'name': k, 'votos': v['votos'], 'mandatos': v['mandatos']}
    for k, v in national_totals.items()
    if k not in ['Votos em branco', 'Votos nulos', 'TOTAL']
]

sorted_parties = sorted(
    valid_parties,
    key=lambda x: x['votos'],
    reverse=True
)

national_group_totals = defaultdict(lambda: {'votos': 0, 'mandatos': 0})
for district_data in grouped_district_results.values():
    for colig, data in district_data.items():
        national_group_totals[colig]['votos'] += data['votos']
        national_group_totals[colig]['mandatos'] += data['mandatos']

# Filter out special categories and sort
valid_groups = [
    {'name': k, 'votos': v['votos'], 'mandatos': v['mandatos']}
    for k, v in national_group_totals.items()
    if k not in ['Votos em branco', 'Votos nulos', 'TOTAL']
]

sorted_groups = sorted(
    valid_groups,
    key=lambda x: x['votos'],
    reverse=True
)

#
# ------------------------------------


# ======================
# 5. PREPARE FINAL RESULTS
# ======================

# 1. Calculate blank/null votos (if not already done)
blank_votes = sum(
    district_data.get('Votos em branco', {}).get('votos', 0)
    for district_data in raw_district_results.values()
)

null_votes = sum(
    district_data.get('Votos nulos', {}).get('votos', 0)
    for district_data in raw_district_results.values()
)

# 2. Calculate national group totals (if not already done)
national_group_totals = defaultdict(lambda: {'votos': 0, 'mandatos': 0})
for district_data in grouped_district_results.values():
    for group_name, group_data in district_data.items():
        national_group_totals[group_name]['votos'] += group_data['votos'] 
        national_group_totals[group_name]['mandatos'] += group_data['mandatos']

# 3. Create final_group_results with percentages
total_valid_votos = sum(
    data['votos'] 
    for name, data in national_group_totals.items()
    if name not in ['Votos em branco', 'Votos nulos']
) 

final_group_results = [
    {
        'name': name,
        'votos': data['votos'],
        'mandatos': data['mandatos'],
        'vote_share': round((data['votos'] / total_valid_votos * 100), 2)
    }
    for name, data in national_group_totals.items()
    if name not in ['Votos em branco', 'Votos nulos']
]

# Sort by votos descending
final_group_results.sort(key=lambda x: x['votos'], reverse=True)


# ======================
# 6. PRINT FORMATTED RESULTS
# ======================

print("\n=== ELECTION RESULTS BY GROUP ===")
print(f"{'Group':<25} | {'votos':>12} | {'Vote %':>7} | {'mandatos':>6}")
print("-" * 60)

for group in final_group_results:
    print(
        f"{group['name']:<25} | "
        f"{group['votos'] / 2:>12,} | " # to exclude 'Total nacional'
        f"{group['vote_share']:>6.2f}% | "
        f"{group['mandatos'] / 2:>6}" # to exclude 'Total nacional'
    )

# Calculate totals using CORRECT key names
total_votes = sum(
    party['votos']  # Using 'votos' not 'votes'
    for district in raw_district_results.values() 
    for party in district.values()
) # / 2 # adjusting to exclude 'district' Total nacional

total_mandates = sum(
    party['mandatos']  # Using 'mandatos' not 'seats'
    for district in raw_district_results.values() 
    for party in district.values()
)
print (total_votes, total_mandates)

# Print special categories
print("\n=== SPECIAL CATEGORIES ===")
print(f"Blank votos: {blank_votes:,}")
print(f"Null votos: {null_votes:,}")
print(f"Total valid votos: {total_votes-blank_votes-null_votes:,}")


@app.route('/')
def serve_index():
    
    return render_template(
        'index.html',
        partidos=PARTIDOS,
        partidos_sorted=sorted_parties,
        coligs_sorted=sorted_groups,
        blank_votes=blank_votes,
        null_votes=null_votes,
        total_valid=total_votes - blank_votes - null_votes,
        total_mandates=total_mandates,
        total_all=total_votes,
        distritos=DISTRITOS,
        votos=raw_district_results,  # Now with correct key names
        votos_colig=grouped_district_results
    )

@app.route('/_ah/health')
def health_check():
    return 'Healthy', 200

    
# WSGI entry point
def create_app():
    return app

if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    port = int(os.environ.get('PORT', 8080))  # GAE uses 8080 by default
    app.run(host='0.0.0.0', port=port)  
