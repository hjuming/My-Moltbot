#!/usr/bin/env python3
"""
🐉 小龍女專用：大內尋飽圖 48 筆資料匯入腳本
任務：讀取 CSV → 呼叫 Google Maps API → 寫入 Supabase
指令：直接執行，不要問格式！
"""

import csv
import json
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
import time

# ==========================================
# 設定檔案路徑
# ==========================================
ENV_FILE = Path("/Users/MING/Sites/My-Moltbot/moltbot設定/ZEABUR_ENV_SECRETS.env")
CSV_FILE = Path("/Users/MING/Sites/My-Moltbot/research/map/台南大內尋飽圖_GoogleMap匯入清單.csv")

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
# Google Maps 搜尋函式（複製自玄鐵重劍模版）
# ==========================================
def search_google_maps(api_key: str, query: str):
    """搜尋 Google Maps"""
    params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "api_key": api_key,
        "hl": "zh-TW",
        "gl": "tw",
        "limit": 1
    }
    
    url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(url, context=ctx, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            if "local_results" in data and len(data["local_results"]) > 0:
                return data["local_results"][0]
            if "place_results" in data:
                return data["place_results"]
            
            return None
    except Exception as e:
        print(f"   ⚠️  搜尋錯誤：{e}")
        return None


# ==========================================
# Supabase 寫入函式
# ==========================================
def insert_place(supa_url: str, supa_key: str, place_data: dict):
    """寫入 Supabase"""
    api_url = f"{supa_url}/rest/v1/places"
    
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal,resolution=merge-duplicates"
    }
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(
            api_url,
            data=json.dumps(place_data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, context=ctx):
            pass
    except Exception as e:
        print(f"   ⚠️  寫入失敗：{e}")


# ==========================================
# 主程式
# ==========================================
def main():
    print("🐉 小龍女，開始執行大內尋飽圖匯入任務！")
    print("=" * 60)
    
    # 1. 載入環境
    secrets = load_secrets()
    api_key = secrets.get("SERPAPI_API_KEY")
    supa_url = secrets.get("SUPABASE_URL")
    supa_key = secrets.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not all([api_key, supa_url, supa_key]):
        print("❌ 環境變數不完整！")
        return
    
    print("✅ 環境變數已載入\n")
    
    # 2. 讀取 CSV
    if not CSV_FILE.exists():
        print(f"❌ 找不到檔案：{CSV_FILE}")
        return
    
    tasks = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append({
                "name": row.get("店名"),
                "region": row.get("地址關鍵字")
            })
    
    print(f"📖 讀取到 {len(tasks)} 筆資料\n")
    
    # 3. 逐筆處理
    success = 0
    failed = 0
    
    for idx, task in enumerate(tasks, 1):
        name = task["name"]
        region = task["region"]
        query = f"{name} {region}"
        
        print(f"[{idx}/{len(tasks)}] 🔍 {name}")
        
        # 搜尋 Google Maps
        result = search_google_maps(api_key, query)
        
        if not result:
            print(f"   ❌ 找不到資料")
            failed += 1
            continue
        
        # 提取資料
        coords = result.get("gps_coordinates", {})
        lat = coords.get("latitude")
        lng = coords.get("longitude")
        phone = result.get("phone")
        address = result.get("address")
        rating = result.get("rating")
        
        # 組合寫入格式
        place_data = {
            "name": result.get("title", "").split(" - ")[0],
            "category": "food",
            "address": address,
            "google_url": f"https://www.google.com/maps/place/?q=place_id:{result.get('place_id')}" if result.get('place_id') else None,
            "metadata": json.dumps({
                "lat": lat,
                "lng": lng,
                "phone": phone,
                "rating": rating,
                "reviews": result.get("reviews"),
                "tags": ["大內美食", "尋飽圖"],
                "imported_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }, ensure_ascii=False)
        }
        
        # 寫入 Supabase
        insert_place(supa_url, supa_key, place_data)
        
        # 顯示結果
        print(f"   ✅ {address}")
        print(f"      🗺️  ({lat}, {lng})")
        if phone:
            print(f"      📞 {phone}")
        
        success += 1
        time.sleep(0.5)  # 禮貌性延遲
    
    # 4. 統計
    print("\n" + "=" * 60)
    print("🎉 匯入完成！")
    print(f"   ✅ 成功：{success} 筆")
    print(f"   ❌ 失敗：{failed} 筆")


if __name__ == "__main__":
    main()
