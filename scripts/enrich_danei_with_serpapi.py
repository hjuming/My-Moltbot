import csv
import json
import urllib.request
import urllib.parse
from pathlib import Path
import time

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

def search_serpapi(api_key, query):
    # Search Google Maps via SerpApi
    params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "api_key": api_key,
        "hl": "zh-TW",
        "gl": "tw",
        "limit": 1 # We only need the top match
    }
    qs = urllib.parse.urlencode(params)
    url = f"https://serpapi.com/search?{qs}"
    
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(url, context=ctx) as r:
            data = json.loads(r.read().decode())
            # Usually 'local_results' has the list
            if "local_results" in data and len(data["local_results"]) > 0:
                return data["local_results"][0]
            # specific 'place_results' if direct match
            if "place_results" in data:
                return data["place_results"]
            return None
    except Exception as e:
        print(f"❌ SerpApi Error for {query}: {e}")
        return None

def upsert_place(supa_url, supa_key, place_data):
    api_url = f"{supa_url}/rest/v1/places?on_conflict=name" # simplistic matching
    # Ideally we match by name, but we might create dupes if name differs slightly.
    # Let's try to update based on name we scraped.
    
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal,resolution=merge-duplicates"
    }
    
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(api_url, data=json.dumps(place_data).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            pass
    except Exception as e:
        print(f"❌ Update Error: {e}")

def main():
    print("🚀 Enriching Danei Food with SerpApi...")
    secrets = load_secrets()
    serp_key = secrets.get("SERPAPI_API_KEY") # Correct Key Name
    supa_url = secrets.get("SUPABASE_URL")
    supa_key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")

    if not serp_key:
        print("Error: Missing SERPAPI_API_KEY")
        return

    # 1. Read List
    tasks = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(f"{row.get('店名')} {row.get('地址關鍵字')}")

    print(f"Found {len(tasks)} places to enrich.")
    
    # 2. Process
    # SerpApi is fast but let's be gentle.
    count = 0
    for query in tasks:
        print(f"🔍 Searching: {query}...")
        result = search_serpapi(serp_key, query)
        
        if result:
            # Construct rich object
            lat = result.get("gps_coordinates", {}).get("latitude")
            lng = result.get("gps_coordinates", {}).get("longitude")
            
            enrich_data = {
                "name": result.get("title").split(" - ")[0], # Sometimes title has suffix
                "category": "food", 
                "address": result.get("address"),
                "rating": result.get("rating"),
                "google_url": f"https://www.google.com/maps/place/?q=place_id:{result.get('place_id')}",
                # "location": f"POINT({lng} {lat})" if lat and lng else None, 
                # Be careful, we need to match the row we just inserted.
                # Since we don't have ID mapped, we rely on Name matching for UPSERT.
                # If name from SerpApi differs from CSV name, we might create a duplicate. 
                # Strategy: Use the CSV Name as the primary 'name' for matching, store SerpApi Name in metadata?
                "name": query.split()[0], # Use original CSV name to hit the UPSERT update
                "metadata": {
                    "official_name": result.get("title"),
                    "tags": ["大內美食", "SerpApi Verified"],
                    "phone": result.get("phone"),
                    "description": result.get("description") or result.get("snippet") or f"{result.get('address')} 的人氣店家。",
                    "thumbnail": result.get("thumbnail"),
                    "reviews": result.get("reviews")
                }
            }
            if lat and lng:
                # enrich_data["location"] = ... (Skipping to fix 400 error)
                enrich_data["metadata"]["lat"] = lat
                enrich_data["metadata"]["lng"] = lng

            upsert_place(supa_url, supa_key, enrich_data)
            count += 1
        
        # Rate limit?
        # time.sleep(0.1) 

    print(f"✨ Enriched {count} items!")

if __name__ == "__main__":
    main()
