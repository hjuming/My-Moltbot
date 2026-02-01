import csv
import json
import urllib.request
import urllib.parse
from pathlib import Path

# --- Configuration ---
ENV_FILE = Path("/Users/MING/Sites/My-Moltbot/moltbot設定/ZEABUR_ENV_SECRETS.env")
CSV_FILE = Path("/Users/MING/Sites/My-Moltbot/research/map/台南大內尋飽圖_GoogleMap匯入清單.csv")

def load_secrets():
    secrets = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    secrets[k] = v
    return secrets

def main():
    print("🚀 Quick Importing Danei Food List (No-API mode)...")
    secrets = load_secrets()
    supa_url = secrets.get("SUPABASE_URL")
    supa_key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supa_url or not CSV_FILE.exists():
        print("Error: Missing config or CSV file.")
        return

    # 1. Read CSV
    places = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("店名")
            addr_kw = row.get("地址關鍵字")
            
            # Construct Google Search Link
            query = f"{name} {addr_kw}"
            google_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"
            
            place = {
                "name": name,
                "category": "food",
                "address": addr_kw, # Placeholder
                "google_url": google_url,
                "metadata": {
                    "tags": ["大內美食", "台南尋飽"],
                    "description": f"位於{addr_kw}的在地美食。",
                    "original_description": f"{name} {addr_kw}"
                },
                # No location (lat/lng) yet, so PostGIS col will be null
            }
            places.append(place)

    print(f"Prepared {len(places)} items.")

    # 2. Upload to Supabase
    api_url = f"{supa_url}/rest/v1/places"
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal" # standard insert
    }
    
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(api_url, data=json.dumps(places).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            print("✅ Successfully imported 48 Danei Food items!")
    except Exception as e:
        print(f"❌ Upload Error: {e}")

if __name__ == "__main__":
    main()
