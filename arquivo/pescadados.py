import requests
from google.cloud import bigquery
from google.oauth2 import service_account
import time
from datetime import datetime, UTC

# Configuration
BASE_URL = "https://www.legislativas2025.mai.gov.pt/frontend/data/TerritoryResults"
# District mapping
DISTRICT_MAPPING = {
    "LOCAL-010000": "Aveiro",
    "LOCAL-020000": "Beja",
    "LOCAL-030000": "Braga",
    "LOCAL-040000": "Bragança",
    "LOCAL-050000": "Castelo Branco",
    "LOCAL-060000": "Coimbra",
    "LOCAL-070000": "Évora",
    "LOCAL-080000": "Faro",
    "LOCAL-090000": "Guarda",
    "LOCAL-100000": "Leiria",
    "LOCAL-110000": "Lisboa",
    "LOCAL-120000": "Portalegre",
    "LOCAL-130000": "Porto",
    "LOCAL-140000": "Santarém",
    "LOCAL-150000": "Setúbal",
    "LOCAL-160000": "Viana do Castelo",
    "LOCAL-170000": "Vila Real",
    "LOCAL-180000": "Viseu",
    "LOCAL-300000": "Madeira",
    "LOCAL-400000": "Açores",
    "FOREIGN-800000": "Europa",
    "FOREIGN-900000": "Resto do Mundo"
}
TERRITORY_CODES = list(DISTRICT_MAPPING.keys())
BQ_PROJECT = "apps-448519"
BQ_DATASET = "AR25"
BQ_TABLE = "resultadosporcirculo"
# SERVICE_ACCOUNT_FILE = "path/to/your/service-account.json"

def fetch_territory_data(territory_code):
    """Fetch election data for a specific territory"""
    try:
        response = requests.get(
            BASE_URL,
            params={"territoryKey": territory_code, "electionId": "AR"},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {territory_code}: {e}")
        return None

def process_territory_data(territory_code, data):
    """Process territory data into rows for BigQuery"""
    if not data or 'currentResults' not in data:
        return []

    current = data['currentResults']
    timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')  # Updated to timezone-aware
    rows = []
    district_name = DISTRICT_MAPPING.get(territory_code, "Unknown")

    # Special cases for blank/null votes
    rows.extend([
        {
            "codigo": territory_code,
            "distrito": district_name,
            "partido": "Votos em branco",
            "votos": current.get("blankVotes", 0),
            "mandatos": 0,
            "timestamp": timestamp
        },
        {
            "codigo": territory_code,
            "distrito": district_name,
            "partido": "Votos nulos",
            "votos": current.get("nullVotes", 0),
            "mandatos": 0,
            "timestamp": timestamp
        }
    ])

    # Process each party
    for party in current.get("resultsParty", []):
        rows.append({
            "codigo": territory_code,
            "distrito": district_name,
            "partido": party.get("acronym"),  # Using same as acronym
            "votos": party.get("votes", 0),
            "mandatos": party.get("mandates", 0),
            "timestamp": timestamp
        })

    return rows

def save_to_bigquery(rows):
    """Save all data to BigQuery in one operation"""
    """ credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    ) """
    
    client = bigquery.Client(project=BQ_PROJECT)
    table_ref = client.dataset(BQ_DATASET).table(BQ_TABLE)
    
    # Create table if needed (schema will be auto-detected)
    try:
        client.get_table(table_ref)
    except Exception:
        schema = [
            bigquery.SchemaField("codigo", "STRING"),
            bigquery.SchemaField("distrito", "STRING", description="District name (e.g., Aveiro)"),
            bigquery.SchemaField("partido", "STRING"),
            bigquery.SchemaField("votos", "INTEGER"),
            bigquery.SchemaField("mandatos", "INTEGER"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
        ]
        table = bigquery.Table(table_ref, schema=schema)
        client.create_table(table)
    
    errors = client.insert_rows_json(table_ref, rows)
    if errors:
        print(f"Encountered errors: {errors}")
    else:
        print(f"Successfully loaded {len(rows)} rows")

def main():
    all_rows = []
    
    print(f"Processing {len(TERRITORY_CODES)} districts...")
    for territory_code in TERRITORY_CODES:
        print(f"Fetching {DISTRICT_MAPPING.get(territory_code)}...", end=" ", flush=True)
        data = fetch_territory_data(territory_code)
        if data:
            rows = process_territory_data(territory_code, data)
            # print(rows)
            all_rows.extend(rows)
            print(f"Found {len(rows)} parties")
        else:
            print("Failed")
        time.sleep(0.5)  # Respectful delay
    
    if all_rows:
        print(f"\nTotal rows to insert: {len(all_rows)}")
        print(all_rows)
        save_to_bigquery(all_rows)
    else:
        print("No data collected")

if __name__ == "__main__":
    main()