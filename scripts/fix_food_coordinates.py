#!/usr/bin/env python3
"""
修正 Food 資料座標 - 使用 SerpApi 搜尋
"""

import os
import time
from typing import Dict, Optional
from supabase import create_client
from dotenv import load_dotenv
import requests

def load_secrets() -> Dict[str, str]:
    """載入環境變數"""
    env_path = os.path.join(os.path.dirname(__file__), '..', 'moltbot設定', 'ZEABUR_ENV_SECRETS.env')
    load_dotenv(env_path)
    
    return {
        'serpapi_key': os.getenv('SERPAPI_API_KEY'),
        'supabase_url': os.getenv('SUPABASE_URL'),
        'supabase_key': os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    }

def search_place_coordinates(api_key: str, name: str, address: str) -> Optional[tuple]:
    """使用 SerpApi 搜尋地點座標 - 支援模糊搜尋"""
    try:
        # 嘗試多種搜尋策略
        search_queries = [
            f"{name} {address}",  # 原始查詢
            f"{name} 台南大內",   # 簡化地址
            f"{name} 大內區",      # 更簡化
        ]
        
        for query in search_queries:
            print(f"      嘗試: {query}")
            
            params = {
                'engine': 'google_maps',
                'q': query,
                'hl': 'zh-tw',
                'api_key': api_key
            }
            
            response = requests.get('https://serpapi.com/search', params=params, timeout=30)
            data = response.json()
            
            # 檢查結果
            if 'local_results' in data and len(data['local_results']) > 0:
                result = data['local_results'][0]
                result_name = result.get('title', '')
                
                # 驗證結果是否匹配（名稱相似度檢查）
                if name[:3] in result_name or result_name[:3] in name:
                    if 'gps_coordinates' in result:
                        coords = result['gps_coordinates']
                        lat, lng = coords['latitude'], coords['longitude']
                        print(f"      ✅ 找到: {result_name}")
                        print(f"      ✅ 座標: ({lat}, {lng})")
                        return (lat, lng)
                else:
                    print(f"      ⚠️  找到 '{result_name}' 但不匹配")
            
            time.sleep(0.5)  # 避免過快請求
        
        print(f"      ❌ 所有搜尋策略都未找到結果")
        return None
    
    except Exception as e:
        print(f"      ❌ 搜尋失敗: {e}")
        return None

def fix_food_coordinates(limit: int = None):
    """修正 food 類別的座標資料"""
    
    secrets = load_secrets()
    supabase = create_client(secrets['supabase_url'], secrets['supabase_key'])
    
    print("\n" + "="*70)
    print("🍽️  修正 Food 資料座標")
    print("="*70 + "\n")
    
    # 取得所有 food 且缺少座標的資料
    query = supabase.table('places')\
        .select('*')\
        .eq('category', 'food')\
        .is_('location', 'null')
    
    if limit:
        query = query.limit(limit)
    
    response = query.execute()
    places = response.data
    total = len(places)
    
    if total == 0:
        print("✅ 所有 food 資料都已有座標！\n")
        return
    
    print(f"找到 {total} 筆需要修正的資料\n")
    print("-" * 70)
    
    success_count = 0
    fail_count = 0
    
    for i, place in enumerate(places, 1):
        name = place.get('name', '')
        address = place.get('address', '')
        place_id = place['id']
        
        print(f"\n[{i}/{total}] {name}")
        print(f"   地址: {address}")
        
        # 使用 SerpApi 搜尋
        coordinates = None
        if name and address:
            coordinates = search_place_coordinates(secrets['serpapi_key'], name, address)
            time.sleep(1.5)  # API 限流
        else:
            print(f"      ⚠️  缺少名稱或地址")
        
        # 更新資料庫
        if coordinates:
            try:
                # PostGIS POINT 格式: POINT(經度 緯度)
                point_wkt = f"POINT({coordinates[1]} {coordinates[0]})"
                
                supabase.table('places')\
                    .update({'location': point_wkt})\
                    .eq('id', place_id)\
                    .execute()
                
                print(f"   💾 已更新: {point_wkt}")
                success_count += 1
            except Exception as e:
                print(f"   ❌ 更新失敗: {e}")
                fail_count += 1
        else:
            fail_count += 1
    
    print("\n" + "="*70)
    print(f"✅ 完成！成功: {success_count} / {total}, 失敗: {fail_count}")
    print("="*70 + "\n")
    
    return success_count, fail_count

if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    fix_food_coordinates(limit)
