import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path

# --- Configuration ---
ENV_FILE = Path("/Users/MING/Sites/My-Moltbot/moltbot設定/ZEABUR_ENV_SECRETS.env")

# --- Helper Functions ---

def load_secrets():
    secrets = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    secrets[key.strip()] = value.strip()
    return secrets

def clean_html(text):
    if not text: return ""
    # Remove <br>, <div>, etc
    clean = re.sub(r'<[^>]*>', ' ', text)
    # Remove HTML entities
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
    # Collapse multiple spaces
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def extract_metadata(row):
    """
    Intelligent extraction from raw description
    Returns a dict of updates
    """
    raw_desc = row['metadata'].get('original_description', '') or ''
    clean_desc = clean_html(raw_desc)
    
    updates = {
        'metadata': row['metadata']
    }
    
    # 1. Address Extraction
    # Look for common Taiwan address patterns (city+district+road) or just long string after phone removal
    # Pattern: 3 digits postal code? + City + District...
    # Regex for Taiwan postal code + City is handy
    addr_match = re.search(r'(\d{3})?[\u4e00-\u9fa5]+[縣市][\u4e00-\u9fa5]+[區鄉鎮市][\u4e00-\u9fa5]+[路街].+號(\w*)', clean_desc)
    if not row.get('address') and addr_match:
        updates['address'] = addr_match.group(0)
    elif not row.get('address') and "號" in clean_desc:
        # Fallback simplistic extraction: find string containing "號"
         pass

    # 2. Phone Extraction
    # Pattern: +886 9..., 02-..., (02)...
    phone_match = re.search(r'(\+886|0)\s?[\d\-\s]{8,}', clean_desc)
    if phone_match:
        updates['metadata']['phone'] = phone_match.group(0).strip()
        # Remove phone from desc to clean it up? Maybe not, keep context.

    # 3. Geo Extraction (for Dive sites buried in text)
    # Pattern: 22°41'17.2"N 121°28'20.2"E
    geo_match = re.search(r'(\d{1,3})[°|:|\s](\d{1,2})[\'|:|\s](\d{1,2}(\.\d+)?)"?[N|n]\s*,?\s*(\d{1,3})[°|:|\s](\d{1,2})[\'|:|\s](\d{1,2}(\.\d+)?)"?[E|e]', raw_desc)
    if geo_match:
        # Convert DMS to Decimal if needed, OR just store for review.
        # But PostGIS needs decimal.
        # Let's just flag it for now.
        updates['metadata']['extracted_geo_raw'] = geo_match.group(0)

    # 4. YouTube Link Extraction
    yt_match = re.search(r'(https?://(www\.)?(youtube\.com|youtu\.be)/[^\s]+)', raw_desc)
    if yt_match:
        updates['metadata']['video_url'] = yt_match.group(0)

    # 5. Clean Description (Update the field itself to be readable)
    # We create a new 'description' field for display, keeping 'original_description' for backup
    display_desc = clean_desc
    # Remove the extracted URL/Phone from display text to make it cleaner?
    if yt_match: display_desc = display_desc.replace(yt_match.group(0), '')
    if phone_match: display_desc = display_desc.replace(phone_match.group(0), '')
    
    updates['metadata']['description'] = display_desc.strip()
    
    return updates

def update_supabase(url, key, row_id, updates):
    if not updates: return
    
    api_url = f"{url}/rest/v1/places?id=eq.{row_id}"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # PATCH request
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(api_url, data=json.dumps(updates).encode('utf-8'), headers=headers, method='PATCH')
    try:
        with urllib.request.urlopen(req, context=ctx) as r:
            pass # Success
    except Exception as e:
        print(f"❌ Failed to update {row_id}: {e}")

def main():
    print("🧹 Starting Map Data Cleaning (Phase A)...")
    secrets = load_secrets()
    supa_url = secrets.get("SUPABASE_URL")
    supa_key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supa_url:
        print("Error: Config missing")
        return

    # 1. Fetch all places
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}",
    }
    
    req = urllib.request.Request(f"{supa_url}/rest/v1/places?select=*", headers=headers)
    with urllib.request.urlopen(req, context=ctx) as response:
        rows = json.loads(response.read().decode())

    print(f"Adding cleaning logic to {len(rows)} items...")
    
    count = 0
    for row in rows:
        updates = extract_metadata(row)
        if updates:
            update_supabase(supa_url, supa_key, row['id'], updates)
            count += 1
            if count % 50 == 0: print(f"Cleaned {count} items...")

    print(f"✨ Cleaning complete. Processed {count} items.")

if __name__ == "__main__":
    main()
