import os
import zipfile
import json
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse
from pathlib import Path

# --- Configuration ---
ENV_FILE = Path("/Users/MING/Sites/My-Moltbot/moltbot設定/ZEABUR_ENV_SECRETS.env")
MAP_DIR = Path("/Users/MING/Sites/My-Moltbot/research/map")

FILES_TO_IMPORT = [
    {
        "filename": "台灣潛水地圖 DIVE SITE.kmz",
        "category": "dive",
        "dataset_type": "proprietary", # Type B
        "default_tags": ["台灣潛點", "Diving"]
    },
    {
        "filename": "台灣寵物地圖.kmz",
        "category": "pet",
        "dataset_type": "enriched",    # Type C
        "default_tags": ["寵物友善", "Pet Friendly"]
    }
]

# --- Helper Functions ---

def load_secrets():
    """Manually parse .env file to avoid dependency on python-dotenv"""
    secrets = {}
    if not ENV_FILE.exists():
        print(f"❌ Error: Secrets file not found at {ENV_FILE}")
        return None
        
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                secrets[key.strip()] = value.strip()
    return secrets

def parse_kmz(filepath):
    """Extract Placemarks from KMZ (Zipped KML)"""
    places = []
    try:
        with zipfile.ZipFile(filepath, 'r') as z:
            # Find the first .kml file
            kml_files = [f for f in z.namelist() if f.endswith('.kml')]
            if not kml_files:
                print(f"⚠️  No KML found inside {filepath.name}")
                return []
            
            with z.open(kml_files[0]) as f:
                # Parse XML
                tree = ET.parse(f)
                root = tree.getroot()
                
                # Namespace handling is annoying in XML, assume default KML namespace or ignore
                # We'll search by tag name ending in "Placemark" to be safe
                for vid in root.iter():
                    if vid.tag.endswith('Placemark'):
                        name = vid.find('.//{*}name')
                        coords = vid.find('.//{*}coordinates')
                        desc = vid.find('.//{*}description')
                        
                        # Handle namespaces (brute force search for children)
                        if name is None:
                            for child in vid:
                                if child.tag.endswith('name'): name = child
                        if coords is None:
                            for child in vid: # Point -> coordinates
                                if child.tag.endswith('Point'):
                                    for grandchild in child:
                                        if grandchild.tag.endswith('coordinates'):
                                            coords = grandchild
                        
                        if name is not None and coords is not None:
                            p_name = name.text.strip()
                            # KML Coords: lon,lat,alt
                            c_text = coords.text.strip().split(',')
                            lon = float(c_text[0])
                            lat = float(c_text[1])
                            
                            p_desc = desc.text.strip() if desc is not None else ""
                            
                            places.append({
                                "name": p_name,
                                "lon": lon,
                                "lat": lat,
                                "description": p_desc
                            })
    except Exception as e:
        print(f"❌ Failed to parse {filepath.name}: {e}")
    
    return places

def upload_to_supabase(url, key, data_batch):
    """Batch insert to Supabase"""
    if not data_batch:
        return

    api_url = f"{url}/rest/v1/places"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal" # Don't return all inserted rows to save bandwidth
    }
    
    # Prepare JSON body
    req = urllib.request.Request(api_url, data=json.dumps(data_batch).encode('utf-8'), headers=headers, method='POST')
    
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=ctx) as response:
            if response.status in [200, 201]:
                print(f"✅ Successfully inserted {len(data_batch)} places.")
            else:
                print(f"⚠️  Upload status: {response.status}")
    except urllib.error.HTTPError as e:
        print(f"❌ Upload Error: {e.code} - {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"❌ Network Error: {e}")

# --- Main Execution ---

def main():
    print("🚀 Starting Map Import to Supabase...")
    secrets = load_secrets()
    if not secrets:
        return

    supa_url = secrets.get("SUPABASE_URL")
    supa_key = secrets.get("SUPABASE_SERVICE_ROLE_KEY") # Use Service Role to bypass RLS policies if needed, or to be super admin
    
    if not supa_url or not supa_key:
        print("❌ Missing Supabase credentials in .env")
        return

    total_imported = 0

    for file_info in FILES_TO_IMPORT:
        f_path = MAP_DIR / file_info["filename"]
        if not f_path.exists():
            print(f"⚠️  File not found: {f_path}")
            continue
            
        print(f"\n📂 Processing {file_info['filename']}...")
        places = parse_kmz(f_path)
        print(f"   found {len(places)} items.")
        
        # Transform to Database Schema (Batching in chunks of 50)
        batch = []
        for p in places:
            # Construct row
            row = {
                "name": p["name"],
                "category": file_info["category"],
                "dataset_type": file_info["dataset_type"],
                
                # PostGIS Geometry: "POINT(lon lat)" string allows auto-casting in Supabase if setup right,
                # BUT standard Supabase API prefers GeoJSON-like or just WKT.
                # Let's use ST_SetSRID(ST_MakePoint(lon, lat), 4326) logic? 
                # No, via REST API, simply passing the WKT string often works if column is geography.
                # Format: "POINT(lon lat)"
                "location": f"POINT({p['lon']} {p['lat']})",
                
                "metadata": {
                    "original_description": p["description"],
                    "tags": file_info["default_tags"],
                    "imported_from": file_info["filename"]
                }
            }
            batch.append(row)
            
            if len(batch) >= 50:
                upload_to_supabase(supa_url, supa_key, batch)
                total_imported += len(batch)
                batch = []
        
        # Flush remaining
        if batch:
            upload_to_supabase(supa_url, supa_key, batch)
            total_imported += len(batch)

    print(f"\n✨ Import Complete! Total {total_imported} places added to Supabase.")

if __name__ == "__main__":
    main()
