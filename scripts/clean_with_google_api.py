#!/usr/bin/env python3
"""
🧹 Map WEDO 資料清洗腳本 v2.0：差異化清洗策略
任務：
  - Pet 資料：嚴格驗證，不符就刪除（以 Google Maps 為唯一準則）
  - Dive 資料：保留自建資料，用 Google Maps 補強座標與描述
作者：神雕大俠
"""

import json
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from typing import Optional, Dict, List
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
# Google Maps 搜尋 (SerpApi)
# ==========================================
def search_google_maps(api_key: str, query: str) -> Optional[Dict]:
    """使用 SerpApi 搜尋 Google Maps"""
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
# Supabase 操作
# ==========================================
def fetch_places_by_category(supa_url: str, supa_key: str, categories: List[str]) -> List[Dict]:
    """從 Supabase 讀取指定類別的資料"""
    api_url = f"{supa_url}/rest/v1/places"
    
    category_filter = ",".join(categories)
    params = urllib.parse.urlencode({"category": f"in.({category_filter})", "select": "*"})
    
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}"
    }
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(f"{api_url}?{params}", headers=headers)
        with urllib.request.urlopen(req, context=ctx) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"❌ 讀取資料庫失敗：{e}")
        return []


def update_place(supa_url: str, supa_key: str, place_id: str, updated_data: Dict):
    """更新單筆資料"""
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
            data=json.dumps(updated_data).encode('utf-8'),
            headers=headers,
            method='PATCH'
        )
        with urllib.request.urlopen(req, context=ctx):
            pass
    except Exception as e:
        print(f"   ⚠️  更新失敗：{e}")


def delete_place(supa_url: str, supa_key: str, place_id: str):
    """刪除單筆資料"""
    api_url = f"{supa_url}/rest/v1/places?id=eq.{place_id}"
    
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}"
    }
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(api_url, headers=headers, method='DELETE')
        with urllib.request.urlopen(req, context=ctx):
            pass
    except Exception as e:
        print(f"   ⚠️  刪除失敗：{e}")


# ==========================================
# Pet 資料：嚴格清洗（不符就刪除）
# ==========================================
def clean_pet_data(api_key: str, supa_url: str, supa_key: str, places: List[Dict]) -> Dict:
    """清洗寵物資料：以 Google Maps 為準，不符就刪除"""
    print("\n🐾 開始清洗寵物 (Pet) 資料...")
    print("   策略：嚴格驗證，找不到或不符就直接刪除")
    print("-" * 60)
    
    stats = {"total": 0, "updated": 0, "deleted": 0}
    
    for idx, place in enumerate(places, 1):
        if place.get("category") != "pet":
            continue
        
        stats["total"] += 1
        place_id = place.get("id")
        name = place.get("name")
        address = place.get("address", "")
        
        print(f"[Pet {stats['total']}] 🔍 {name}")
        
        # 搜尋 Google Maps
        query = f"{name} {address}" if address else name
        result = search_google_maps(api_key, query)
        
        if not result:
            # 找不到 → 直接刪除
            print(f"   ❌ Google Maps 找不到，刪除資料")
            delete_place(supa_url, supa_key, place_id)
            stats["deleted"] += 1
            time.sleep(0.5)
            continue
        
        # 檢查歇業狀態
        business_status = result.get("business_status", "OPERATIONAL")
        if business_status == "CLOSED_PERMANENTLY":
            print(f"   🗑️  已歇業，刪除資料")
            delete_place(supa_url, supa_key, place_id)
            stats["deleted"] += 1
            time.sleep(0.5)
            continue
        
        # 更新為 Google Maps 的正確資料
        coords = result.get("gps_coordinates", {})
        lat = coords.get("latitude")
        lng = coords.get("longitude")
        
        # 保留原有的寵物友善特徵（如果有）
        original_metadata = json.loads(place.get("metadata", "{}"))
        pet_features = original_metadata.get("pet_friendly_features", {})
        
        updated_data = {
            "name": result.get("title", "").split(" - ")[0],
            "address": result.get("address"),
            "google_url": f"https://www.google.com/maps/place/?q=place_id:{result.get('place_id')}" if result.get('place_id') else None,
            "metadata": json.dumps({
                "lat": lat,
                "lng": lng,
                "phone": result.get("phone"),
                "rating": result.get("rating"),
                "user_ratings_total": result.get("reviews"),
                "pet_friendly_features": pet_features,  # 保留寵物友善標籤
                "verified_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "GoogleMaps (SerpApi)"
            }, ensure_ascii=False)
        }
        
        update_place(supa_url, supa_key, place_id, updated_data)
        
        print(f"   ✅ 已更新：{result.get('address')}")
        print(f"      📞 {result.get('phone', '無電話')}")
        
        stats["updated"] += 1
        time.sleep(0.5)
    
    return stats


# ==========================================
# Dive 資料：補強自建資料（保留原始，補充座標與描述）
# ==========================================
def clean_dive_data(api_key: str, supa_url: str, supa_key: str, places: List[Dict]) -> Dict:
    """清洗潛水資料：保留自建資料，用 Google Maps 補強"""
    print("\n🤿 開始清洗潛水 (Dive) 資料...")
    print("   策略：保留自建資料，補充座標與基本資訊")
    print("-" * 60)
    
    stats = {"total": 0, "enriched": 0, "skipped": 0}
    
    for idx, place in enumerate(places, 1):
        if place.get("category") != "dive":
            continue
        
        stats["total"] += 1
        place_id = place.get("id")
        name = place.get("name")
        address = place.get("address", "")
        
        print(f"[Dive {stats['total']}] 🔍 {name}")
        
        # 搜尋 Google Maps（補充用）
        query = f"{name} 潛水" if not address else f"{name} {address}"
        result = search_google_maps(api_key, query)
        
        # 讀取原始 metadata（保留自建的潛水專業資訊）
        original_metadata = json.loads(place.get("metadata", "{}"))
        
        if not result:
            # 找不到 Google 資料 → 保留原始資料，標記為自建
            print(f"   ℹ️  Google Maps 無資料，保留自建資訊")
            original_metadata["source"] = "self_maintained"
            original_metadata["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            update_place(supa_url, supa_key, place_id, {
                "metadata": json.dumps(original_metadata, ensure_ascii=False)
            })
            stats["skipped"] += 1
            time.sleep(0.3)
            continue
        
        # 有 Google 資料 → 補強座標與基本資訊
        coords = result.get("gps_coordinates", {})
        lat = coords.get("latitude")
        lng = coords.get("longitude")
        
        # 生成簡單介紹（若原本沒有）
        if not original_metadata.get("description"):
            description = f"{name}位於{result.get('address', '台灣東北角海域')}，是熱門的潛水地點。"
        else:
            description = original_metadata.get("description")
        
        # 合併資料：保留自建專業資訊 + Google 補充
        enriched_metadata = {
            **original_metadata,  # 保留所有自建欄位（max_depth, difficulty, current 等）
            "lat": lat,
            "lng": lng,
            "phone": result.get("phone"),
            "rating": result.get("rating"),
            "description": description,
            "google_verified": True,
            "verified_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source": "hybrid (self + google)"
        }
        
        # 確保有基本標籤
        if "tags" not in enriched_metadata:
            enriched_metadata["tags"] = ["潛水", "Diving"]
        
        updated_data = {
            "address": result.get("address"),
            "google_url": f"https://www.google.com/maps/place/?q=place_id:{result.get('place_id')}" if result.get('place_id') else None,
            "metadata": json.dumps(enriched_metadata, ensure_ascii=False)
        }
        
        update_place(supa_url, supa_key, place_id, updated_data)
        
        print(f"   ✅ 已補強：座標 ({lat}, {lng})")
        if result.get("phone"):
            print(f"      📞 {result.get('phone')}")
        
        stats["enriched"] += 1
        time.sleep(0.5)
    
    return stats


# ==========================================
# 主程式
# ==========================================
def clean_places(api_key: str, supa_url: str, supa_key: str):
    """執行差異化清洗"""
    
    print("🧹 Map WEDO 資料清洗 v2.0")
    print("=" * 60)
    
    # 1. 讀取資料
    print("\n📖 讀取資料庫中的 pet 與 dive 類別...")
    places = fetch_places_by_category(supa_url, supa_key, ["pet", "dive"])
    print(f"   找到 {len(places)} 筆資料")
    
    if not places:
        print("✅ 沒有資料需要清洗")
        return
    
    # 2. 分類處理
    pet_stats = clean_pet_data(api_key, supa_url, supa_key, places)
    dive_stats = clean_dive_data(api_key, supa_url, supa_key, places)
    
    # 3. 輸出統計
    print("\n" + "=" * 60)
    print("🎉 清洗完成！")
    print("\n🐾 寵物 (Pet) 資料：")
    print(f"   總計：{pet_stats['total']} 筆")
    print(f"   ✅ 更新：{pet_stats['updated']} 筆")
    print(f"   🗑️  刪除：{pet_stats['deleted']} 筆")
    print("\n🤿 潛水 (Dive) 資料：")
    print(f"   總計：{dive_stats['total']} 筆")
    print(f"   ✅ 補強：{dive_stats['enriched']} 筆")
    print(f"   ℹ️  保留：{dive_stats['skipped']} 筆（純自建）")


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
    
    clean_places(api_key, supa_url, supa_key)
