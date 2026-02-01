import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path

# --- Configuration ---
ENV_FILE = Path("/Users/MING/Sites/My-Moltbot/moltbot設定/ZEABUR_ENV_SECRETS.env")

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
    clean = re.sub(r'<[^>]*>', ' ', text)
    clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&quot;', '"')
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def extract_metadata(row):
    raw_desc = row['metadata'].get('original_description', '') or ''
    # Fallback to current description if original is missing
    if not raw_desc: raw_desc = row['metadata'].get('description', '')
    
    clean_desc = clean_html(raw_desc)
    
    updates = {}
    should_delete = False
    
    # --- Category Specific Logic ---
    
    # 1. PET: Delete if low quality
    if row['category'] == 'pet':
        # Condition: If title contains "歇業" OR (no phone AND no address)
        if "歇業" in row['name'] or (not row.get('address') and not row['metadata'].get('phone')):
            # Strict cleaning: For now, let's just flag empty ones. 
            # User said: "如果該地圖連結沒有資訊，也可以把資訊篩除" (If invalid link).
            # But checking link validity requires I/O. 
            # Let's delete if description is extremely short/empty (< 5 chars)
            if len(clean_desc) < 5:
                should_delete = True

    # 2. DIVE: Clean prefixes and formatting
    if row['category'] == 'dive':
        # Remove prefixes like "特點：", "生態：", "適合：", "等級："
        # Use regex to replace "Header:" with just newlines or space
        patterns = [r'特點\s*[：|:]', r'生態\s*[：|:]', r'適合\s*[：|:]', r'等級\s*[：|:]', r'位置\s*[：|:]']
        for p in patterns:
            clean_desc = re.sub(p, '', clean_desc)
        
        # Clean up coordinates string from valid description text
        # (Coordinate usually at the end or beginning, let's try to keep it but format it?)
        # User wants: "一段簡單敘述，並加上座標、標籤"
        # We will extract coord for UI, but keeping it in text is fine if cleaned.
        # Actually, let's remove the raw coordinate string from description if we successfully extracted it?
        # Pattern: 22°41'17.2"N 121°28'20.2"E
        geo_str = re.search(r'(\d{1,3}[°|:|\s]\d{1,2}[\'|:|\s]\d{1,2}(\.\d+)?"?[N|n]\s*,?\s*\d{1,3}[°|:|\s]\d{1,2}[\'|:|\s]\d{1,2}(\.\d+)?"?[E|e])', clean_desc)
        if geo_str:
            clean_desc = clean_desc.replace(geo_str.group(0), '') # Remove from text
            # Add it back in a structured way to metadata if not there?
            # actually let's just leave it out of text, we will display location via PostGIS or separate field.
            
    # Remove YouTube links from text (move to video_url)
    yt_match = re.search(r'(https?://(www\.)?(youtube\.com|youtu\.be)/[^\s]+)', clean_desc)
    if yt_match:
        clean_desc = clean_desc.replace(yt_match.group(0), '')
        
    # Collapse lines
    # Replace multiple newlines/spaces with single space
    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()

    # --- Construct Updates ---
    new_metadata = row['metadata'].copy()
    new_metadata['description'] = clean_desc
    
    if should_delete:
        return {'_action': 'delete', 'id': row['id']}
        
    updates['metadata'] = new_metadata
    
    # Return processed row
    processed_row = row.copy()
    processed_row.update(updates)
    return processed_row

def main():
    print("🚀 Batch Cleaning Map Data (Phase A Fast)...")
    secrets = load_secrets()
    supa_url = secrets.get("SUPABASE_URL")
    supa_key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supa_url: return

    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal,resolution=merge-duplicates" # CRITICAL fix for UPSERT
    }
    
    # 1. Fetch
    req = urllib.request.Request(f"{supa_url}/rest/v1/places?select=*", headers=headers)
    with urllib.request.urlopen(req, context=ctx) as response:
        rows = json.loads(response.read().decode())
    
    # 2. Process
    upsert_rows = []
    delete_ids = []
    
    for row in rows:
        processed = extract_metadata(row)
        if processed.get('_action') == 'delete':
            delete_ids.append(processed['id'])
        else:
            upsert_rows.append(processed)
        
    print(f"Stats: {len(upsert_rows)} to update, {len(delete_ids)} to delete.")

    # 3. Batch Delete
    if delete_ids:
        # Delete chunk logic
        del_url = f"{supa_url}/rest/v1/places"
        # DELETE filter: id.in.(1,2,3)
        # Limit URL length, chunk deletions
        # Simplest is loop for now or small chunks
        chunk_size = 20
        for i in range(0, len(delete_ids), chunk_size):
            chunk = delete_ids[i:i + chunk_size]
            filter_str = f"id=in.({','.join(chunk)})"
            req = urllib.request.Request(f"{del_url}?{filter_str}", headers=headers, method='DELETE')
            try:
                with urllib.request.urlopen(req, context=ctx) as r:
                    print(f"🗑️ Deleted chunk {i // chunk_size + 1}")
            except Exception as e:
                print(f"❌ Error deleting chunk: {e}")

    # 4. Batch Upsert
    api_url = f"{supa_url}/rest/v1/places?on_conflict=id"
    
    # Send in chunks of 50
    chunk_size = 50
    for i in range(0, len(upsert_rows), chunk_size):
        chunk = upsert_rows[i:i + chunk_size]
        req = urllib.request.Request(api_url, data=json.dumps(chunk).encode('utf-8'), headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, context=ctx) as r:
                print(f"✅ Upserted chunk {i // chunk_size + 1}")
        except Exception as e:
            print(f"❌ Error upserting chunk: {e}")

    print("✨ Mission Complete.")

if __name__ == "__main__":
    main()
