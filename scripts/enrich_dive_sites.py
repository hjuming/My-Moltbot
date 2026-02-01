#!/usr/bin/env python3
"""
🤿 潛水點資料補強腳本
用途：將自建的潛水點資料用 Google Maps 補強
格式：簡單介紹 + 精確座標 + 關鍵字標籤 + Google Maps 連結
"""

import json
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
import time

# ==========================================
# 環境設定
# ==========================================
ENV_FILE = Path("/Users/MING/Sites/My-Moltbot/moltbot設定/ZEABUR_ENV_SECRETS.env")

def load_secrets():
    """載入環境變數"""
    secrets = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    secrets[k] = v
    return secrets


# ==========================================
# Google Maps 搜尋（補充資料）
# ==========================================
def search_dive_site_info(api_key: str, site_name: str, region: str = "台灣"):
    """
    搜尋潛點附近的參考資訊
    注意：大部分潛點在 Google Maps 上沒有直接資料
    """
    query = f"{site_name} 潛水 {region}"
    
    params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "api_key": api_key,
        "hl": "zh-TW",
        "gl": "tw",
        "limit": 3  # 取前 3 筆參考
    }
    
    url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(url, context=ctx, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if "local_results" in data and len(data["local_results"]) > 0:
                return data["local_results"]
            
            return None
            
    except Exception as e:
        print(f"      ⚠️  搜尋錯誤：{e}")
        return None


# ==========================================
# Supabase 操作
# ==========================================
def fetch_dive_sites(supa_url: str, supa_key: str):
    """讀取所有潛水點資料"""
    api_url = f"{supa_url}/rest/v1/places?category=eq.dive&select=*"
    
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}"
    }
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"❌ 讀取資料庫失敗：{e}")
        return []


def update_dive_site(supa_url: str, supa_key: str, place_id: int, enriched_data: dict):
    """更新潛點資料"""
    api_url = f"{supa_url}/rest/v1/places?id=eq.{place_id}"
    
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            api_url,
            data=json.dumps(enriched_data).encode('utf-8'),
            headers=headers,
            method='PATCH'
        )
        with urllib.request.urlopen(req, context=ctx):
            pass
        return True
    except Exception as e:
        print(f"      ⚠️  更新失敗：{e}")
        return False


# ==========================================
# 座標格式轉換
# ==========================================
def parse_coordinates(location_str: str):
    """
    解析各種座標格式
    - POINT(121.234 23.456)
    - 23.456, 121.234
    - 23°45'12.3"N 121°28'19.4"E
    """
    if not location_str:
        return None, None
    
    # PostGIS POINT 格式
    if "POINT" in location_str:
        import re
        match = re.search(r'POINT\(([^ ]+) ([^ ]+)\)', location_str)
        if match:
            return float(match.group(2)), float(match.group(1))  # lat, lng
    
    # 度分秒格式
    if "°" in location_str and "'" in location_str:
        # 簡化處理：直接提取數字
        import re
        parts = re.findall(r'(\d+)°(\d+)\'([\d.]+)"([NS])\s+(\d+)°(\d+)\'([\d.]+)"([EW])', location_str)
        if parts:
            lat_d, lat_m, lat_s, lat_dir, lng_d, lng_m, lng_s, lng_dir = parts[0]
            lat = float(lat_d) + float(lat_m)/60 + float(lat_s)/3600
            lng = float(lng_d) + float(lng_m)/60 + float(lng_s)/3600
            if lat_dir == 'S': lat = -lat
            if lng_dir == 'W': lng = -lng
            return lat, lng
    
    # 逗號分隔格式
    if "," in location_str:
        parts = location_str.split(",")
        try:
            return float(parts[0].strip()), float(parts[1].strip())
        except:
            pass
    
    return None, None


def format_coordinates_dms(lat: float, lng: float) -> str:
    """
    將十進位座標轉換為度分秒格式
    例：22°39'24.7"N 121°28'19.4"E
    """
    def decimal_to_dms(decimal, is_latitude):
        direction = ""
        if is_latitude:
            direction = "N" if decimal >= 0 else "S"
        else:
            direction = "E" if decimal >= 0 else "W"
        
        decimal = abs(decimal)
        degrees = int(decimal)
        minutes_decimal = (decimal - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        
        return f"{degrees}°{minutes}'{seconds:.1f}\"{direction}"
    
    lat_dms = decimal_to_dms(lat, True)
    lng_dms = decimal_to_dms(lng, False)
    
    return f"{lat_dms} {lng_dms}"


# ==========================================
# 生成潛點介紹
# ==========================================
def generate_dive_description(site_name: str, metadata: dict, google_results: list = None) -> str:
    """
    生成簡潔的潛點介紹
    參考格式：📍 小丑島 Clown Island
    """
    intro_parts = []
    
    # 基本描述（從 metadata 提取）
    if metadata.get("description"):
        intro_parts.append(metadata["description"][:100])
    
    # 深度資訊
    if metadata.get("max_depth"):
        intro_parts.append(f"最大深度約 {metadata['max_depth']} 米")
    
    # 難度
    if metadata.get("difficulty"):
        difficulty_map = {
            "beginner": "初級潛點",
            "intermediate": "中級潛點",
            "advance": "進階潛點"
        }
        intro_parts.append(difficulty_map.get(metadata["difficulty"], ""))
    
    # 入水方式
    if metadata.get("entry_type"):
        entry_map = {
            "boat": "船潛",
            "shore": "岸潛",
            "both": "船潛/岸潛"
        }
        intro_parts.append(entry_map.get(metadata["entry_type"], ""))
    
    # 特色（從別名或筆記提取關鍵字）
    if metadata.get("notes"):
        notes = metadata["notes"][:80]
        intro_parts.append(notes)
    
    return "。".join([p for p in intro_parts if p])


# ==========================================
# 主補強邏輯
# ==========================================
def enrich_dive_sites(api_key: str, supa_url: str, supa_key: str):
    """
    補強潛水點資料
    """
    
    print("🤿 開始補強潛水點資料...")
    print("=" * 60)
    print("策略：自建資料 + Google Maps 補充")
    print("格式：介紹 + 座標 + 標籤 + 連結\n")
    
    # 1. 讀取所有潛水點
    sites = fetch_dive_sites(supa_url, supa_key)
    print(f"📖 找到 {len(sites)} 個潛水點\n")
    
    if not sites:
        print("✅ 沒有資料需要補強")
        return
    
    # 統計
    stats = {
        "total": len(sites),
        "enriched": 0,
        "skipped": 0,
        "failed": 0
    }
    
    # 2. 逐個補強
    for idx, site in enumerate(sites, 1):
        site_id = site.get("id")
        name = site.get("name")
        metadata = site.get("metadata", {})
        
        print(f"[{idx}/{len(sites)}] 🤿 補強：{name}")
        
        # 解析現有座標
        lat, lng = parse_coordinates(site.get("location"))
        
        # 如果沒有座標，嘗試從 metadata 取得
        if not lat or not lng:
            lat = metadata.get("lat")
            lng = metadata.get("lng")
        
        if not lat or not lng:
            print(f"      ⚠️  缺少座標資訊，跳過")
            stats["skipped"] += 1
            continue
        
        # 生成介紹
        description = generate_dive_description(name, metadata)
        
        # 生成座標字串（度分秒格式）
        coords_dms = format_coordinates_dms(lat, lng)
        
        # 提取標籤
        tags = metadata.get("tags", [])
        if metadata.get("difficulty"):
            tags.append(metadata["difficulty"])
        if metadata.get("entry_type"):
            tags.append(metadata["entry_type"])
        
        # Google Maps 連結（使用座標）
        google_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        
        # 組合更新資料
        enriched_metadata = {
            **metadata,  # 保留原有資料
            "description": description,
            "coordinates_dms": coords_dms,
            "lat": lat,
            "lng": lng,
            "tags": list(set(tags)),  # 去重
            "enriched_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        update_data = {
            "google_url": google_url,
            "location": f"POINT({lng} {lat})",  # PostGIS 格式
            "metadata": json.dumps(enriched_metadata, ensure_ascii=False)
        }
        
        if update_dive_site(supa_url, supa_key, site_id, update_data):
            print(f"      ✅ 已補強")
            print(f"         📍 座標：{coords_dms}")
            print(f"         🔗 {google_url}")
            if description:
                print(f"         💬 {description[:60]}...")
            stats["enriched"] += 1
        else:
            stats["failed"] += 1
        
        # 禮貌性延遲
        time.sleep(0.3)
    
    # 3. 輸出統計
    print("\n" + "=" * 60)
    print("🎉 潛水點補強完成！")
    print(f"   📊 總計：{stats['total']} 個")
    print(f"   ✅ 已補強：{stats['enriched']} 個")
    print(f"   ⏭️  跳過：{stats['skipped']} 個")
    print(f"   ⚠️  失敗：{stats['failed']} 個")


# ==========================================
# 程式進入點
# ==========================================
if __name__ == "__main__":
    secrets = load_secrets()
    
    api_key = secrets.get("SERPAPI_API_KEY")
    supa_url = secrets.get("SUPABASE_URL")
    supa_key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not all([api_key, supa_url, supa_key]):
        print("❌ 環境變數不完整！請檢查：")
        print(f"   SERPAPI_API_KEY: {'✅' if api_key else '❌'}")
        print(f"   SUPABASE_URL: {'✅' if supa_url else '❌'}")
        print(f"   SUPABASE_SERVICE_ROLE_KEY: {'✅' if supa_key else '❌'}")
        exit(1)
    
    enrich_dive_sites(api_key, supa_url, supa_key)
