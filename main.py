from flask import Flask, request, jsonify, abort, render_template
from google.cloud import bigquery
import os
from collections import defaultdict
from operator import itemgetter

app = Flask(__name__, static_folder='static')

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

# Get election data from BigQuery table
client = bigquery.Client(project=PROJECTO)
query = f"""
SELECT codigo, distrito, partido, votos, mandatos, timestamp
FROM {PROJECTO}.{DATASET}.{TABELA}
"""
election_data = client.query(query).to_dataframe()

# Initialize with nested defaultdict that creates {'votos': 0, 'mandatos': 0} for new parties
votes_by_district = defaultdict(lambda: defaultdict(lambda: {'votos': 0, 'mandatos': 0}))

# Obter votos por distrito e partido
for _, row in election_data.iterrows():
    distrito = row['distrito']
    partido = row['partido']
    votes_by_district[distrito][partido]['votos'] = row['votos']
    votes_by_district[distrito][partido]['mandatos'] = row.get('mandatos', 0)  # Using get() in case mandatos is missing

# Sort parties by votes within each district
for district in votes_by_district:
    # Convert to list of (party, votes) tuples and sort by votes (descending)
    sorted_parties = sorted(
        votes_by_district[district].items(),
        key=lambda x: x[1]['votos'],
        reverse=True
    )
    
    # Create new ordered dictionary for this district
    ordered_parties = {}
    for party, votes in sorted_parties:
        ordered_parties[party] = votes
    
    # Update the district data
    votes_by_district[district] = ordered_parties

national_totals = defaultdict(lambda: {'votos': 0, 'mandatos': 0})
for district_data in votes_by_district.values():
    for party, data in district_data.items():
        national_totals[party]['votos'] += data['votos']
        national_totals[party]['mandatos'] += data['mandatos']

votes_by_district['Total nacional'] = dict(national_totals)
votes_by_district['Total nacional']['TOTAL'] = {
    'votos': sum(data['votos'] for data in national_totals.values()),
    'mandatos': sum(data['mandatos'] for data in national_totals.values())
}

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

blank_votes = national_totals.get('Votos em branco', {'votos': 0})['votos']
null_votes = national_totals.get('Votos nulos', {'votos': 0})['votos']

partidos = PARTIDOS



@app.route('/')
def serve_index():
    return render_template(
        'index.html', 
        partidos=PARTIDOS, 
        partidos_sorted=sorted_parties,
        blank_votes=blank_votes,
        null_votes=null_votes,
        total_valid=votes_by_district['Total nacional']['TOTAL']['votos'],
        total_mandates=votes_by_district['Total nacional']['TOTAL']['mandatos'],
        total_all=votes_by_district['Total nacional']['TOTAL']['votos'] + blank_votes + null_votes,
        distritos=DISTRITOS,
        votos=votes_by_district
    )

@app.route('/api/partidos')
def get_partidos():
    return jsonify(PARTIDOS)

# WSGI entry point
def create_app():
    return app

if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
    port = int(os.environ.get('PORT', 8080))  # GAE uses 8080 by default
    app.run(host='0.0.0.0', port=port)  
