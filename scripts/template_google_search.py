#!/usr/bin/env python3
"""
🗡️ 玄鐵重劍：Google Maps 資料搜尋標準模版
適用於：SerpApi (Google Maps API 代理服務)
作者：神雕大俠
用途：教小龍女如何正確呼叫 Google Maps 搜尋
"""

import json
import urllib.request
import urllib.parse
from pathlib import Path
import ssl

# ==========================================
# 第一步：自動載入環境變數
# ==========================================
ENV_FILE = Path("/Users/MING/Sites/My-Moltbot/moltbot設定/ZEABUR_ENV_SECRETS.env")

def load_secrets():
    """從環境檔案載入所有 API Keys"""
    secrets = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    secrets[k] = v
    return secrets


# ==========================================
# 第二步：標準搜尋函式 (錯誤防禦)
# ==========================================
def search_google_maps(api_key: str, query: str, region: str = "tw") -> dict:
    """
    使用 SerpApi 搜尋 Google Maps
    
    Args:
        api_key: SERPAPI_API_KEY
        query: 搜尋關鍵字 (例如："大內豆菜麵 台南市大內區")
        region: 地區代碼 (預設 tw = 台灣)
    
    Returns:
        dict: 店家資訊，包含座標、電話、地址等
        None: 搜尋失敗
    """
    params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "api_key": api_key,
        "hl": "zh-TW",
        "gl": region,
        "limit": 1  # 只取第一筆最相關結果
    }
    
    url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
    
    try:
        # SSL 設定（避免憑證錯誤）
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(url, context=ctx, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            # 回傳結構處理
            if "local_results" in data and len(data["local_results"]) > 0:
                return data["local_results"][0]
            
            if "place_results" in data:
                return data["place_results"]
            
            # 找不到結果
            print(f"⚠️  無結果：{query}")
            return None
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 錯誤 {e.code}：{query}")
        if e.code == 400:
            print("   可能原因：API Key 無效或配額用完")
        return None
        
    except urllib.error.URLError as e:
        print(f"❌ 網路錯誤：{e.reason}")
        return None
        
    except Exception as e:
        print(f"❌ 未知錯誤：{type(e).__name__} - {e}")
        return None


# ==========================================
# 第三步：資料標準化函式
# ==========================================
def extract_place_data(serp_result: dict) -> dict:
    """
    將 SerpApi 回傳結果標準化成統一格式
    
    Returns:
        {
            "name": "店名",
            "address": "完整地址",
            "lat": 緯度,
            "lng": 經度,
            "phone": "電話",
            "rating": 評分,
            "reviews": 評論數,
            "google_url": "Google Maps 連結",
            "business_status": "OPERATIONAL" / "CLOSED_PERMANENTLY"
        }
    """
    if not serp_result:
        return None
    
    coords = serp_result.get("gps_coordinates", {})
    
    return {
        "name": serp_result.get("title", "").split(" - ")[0],  # 去掉後綴
        "address": serp_result.get("address"),
        "lat": coords.get("latitude"),
        "lng": coords.get("longitude"),
        "phone": serp_result.get("phone"),
        "rating": serp_result.get("rating"),
        "reviews": serp_result.get("reviews"),
        "google_url": f"https://www.google.com/maps/place/?q=place_id:{serp_result.get('place_id')}" if serp_result.get('place_id') else None,
        "business_status": "OPERATIONAL"  # SerpApi 不會回傳歇業店家
    }


# ==========================================
# 範例使用方式
# ==========================================
if __name__ == "__main__":
    print("🗡️  玄鐵重劍測試開始...\n")
    
    # 1. 載入 API Key
    secrets = load_secrets()
    api_key = secrets.get("SERPAPI_API_KEY")
    
    if not api_key:
        print("❌ 找不到 SERPAPI_API_KEY！請檢查環境檔案。")
        exit(1)
    
    print(f"✅ API Key 已載入：{api_key[:20]}...\n")
    
    # 2. 測試搜尋
    test_queries = [
        "大內豆菜麵 台南市大內區",
        "阿榮牛肉湯 台南市大內區",
    ]
    
    for query in test_queries:
        print(f"🔍 搜尋：{query}")
        result = search_google_maps(api_key, query)
        
        if result:
            data = extract_place_data(result)
            print(f"   ✅ {data['name']}")
            print(f"      📍 {data['address']}")
            print(f"      🗺️  座標：({data['lat']}, {data['lng']})")
            print(f"      📞 {data['phone']}")
            print(f"      ⭐ {data['rating']} ({data['reviews']} 則評論)")
        else:
            print("   ❌ 搜尋失敗")
        
        print()
    
    print("🎉 測試完成！小龍女可以直接複製這些函式使用。")
