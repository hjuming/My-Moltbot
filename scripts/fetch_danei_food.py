import os
import json
import urllib.request
import urllib.parse
from pathlib import Path

# --- Configuration ---
ENV_FILE = Path("/Users/MING/Sites/My-Moltbot/moltbot設定/ZEABUR_ENV_SECRETS.env")
SEARCH_QUERY = "台南大內區 美食"
LOCATION = "Danei District, Tainan City, Taiwan"

def load_secrets():
    secrets = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    secrets[k] = v
    return secrets

def fetch_serpapi_places(api_key, query, location):
    print(f"🔍 Searching SerpApi for: {query} in {location}...")
    params = {
        "engine": "google_maps",
        "q": query,
        "ll": "@23.119,120.356,14z", # Approximate center of Danei
        "type": "search",
        "api_key": api_key,
        "hl": "zh-TW",
        "gl": "tw"
    }
    qs = urllib.parse.urlencode(params)
    url = f"https://serpapi.com/search?{qs}"
    
    try:
        with urllib.request.urlopen(url) as r:
            data = json.loads(r.read().decode())
            return data.get("local_results", [])
    except Exception as e:
        print(f"❌ SerpApi Error: {e}")
        return []

def upsert_to_supabase(url, key, places):
    print(f"📤 Uploading {len(places)} places to Supabase...")
    
    formatted_rows = []
    for p in places:
        # Map SerpApi result to our Schema
        # SerpApi: title, place_id, gps_coordinates, address, phone, rating
        
        row = {
            "name": p.get("title"),
            "category": "food", # Assuming food search
            "location": f"POINT({p['gps_coordinates']['longitude']} {p['gps_coordinates']['latitude']})" if p.get('gps_coordinates') else None,
            "address": p.get("address"),
            "google_url": f"https://www.google.com/maps/place/?q=place_id:{p.get('place_id')}" if p.get("place_id") else None,
            "rating": p.get("rating"),
            "metadata": {
                "place_id": p.get("place_id"),
                "phone": p.get("phone"),
                "total_ratings": p.get("reviews"),
                "thumbnail": p.get("thumbnail"),
                "description": p.get("description"), # SerpApi sometimes gives snippets
                "tags": [t for t in [p.get("type")] if t],
                "price": p.get("price")
            }
        }
        
        # ID generation? Supabase can auto-gen if we don't provide.
        # But we need on_conflict logic.
        # Let's use place_id as a unique key if we can, but our 'id' is UUID.
        # We'll use name+lat as basic conflict avoidance or just Let Supabase create new ones.
        # For this script, we just INSERT. If duplicates, we might want to clean later.
        
        formatted_rows.append(row)

    # Batch Insert
    api_url = f"{url}/rest/v1/places"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal" 
    }
    
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(api_url, data=json.dumps(formatted_rows).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            print("✅ Success!")
    except Exception as e:
        print(f"❌ Upload Error: {e}")

def main():
    secrets = load_secrets()
    serp_key = secrets.get("SERPAPI_KEY") # Check if you have this key in env
    supa_url = secrets.get("SUPABASE_URL")
    supa_key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")

    if not serp_key:
        print("⚠️ Missing SERPAPI_KEY. Please add it to your .env file.")
        # Mocking for now if key missing? No, user wants real data.
        return

    places = fetch_serpapi_places(serp_key, SEARCH_QUERY, LOCATION)
    if places:
        upsert_to_supabase(supa_url, supa_key, places)
    else:
        print("No results found.")

if __name__ == "__main__":
    main()
