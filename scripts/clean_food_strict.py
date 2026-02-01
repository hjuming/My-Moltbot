#!/usr/bin/env python3
"""
嚴格清理 Food 資料
規則：如果在 Google Maps 找不到（搜尋「台南市大內區 + 店名」），就刪除
"""

import os
import time
from typing import Dict, Optional, List
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

def search_on_google_maps(api_key: str, name: str, region: str = "台南市大內區") -> Optional[Dict]:
    """
    在 Google Maps 搜尋店家
    回傳：找到的店家資訊，或 None
    """
    try:
        query = f"{name} {region}"
        print(f"      搜尋: {query}")
        
        params = {
            'engine': 'google_maps',
            'q': query,
            'hl': 'zh-tw',
            'api_key': api_key
        }
        
        response = requests.get('https://serpapi.com/search', params=params, timeout=30)
        data = response.json()
        
        # 檢查是否有結果
        if 'local_results' in data and len(data['local_results']) > 0:
            result = data['local_results'][0]
            result_name = result.get('title', '')
            
            # 簡單的名稱匹配檢查（前3個字）
            if name[:3] in result_name or result_name[:3] in name:
                print(f"      ✅ 找到: {result_name}")
                return {
                    'name': result_name,
                    'address': result.get('address', ''),
                    'phone': result.get('phone', ''),
                    'rating': result.get('rating'),
                    'reviews': result.get('reviews'),
                    'gps_coordinates': result.get('gps_coordinates', {}),
                    'place_id': result.get('place_id', ''),
                    'google_url': f"https://www.google.com/maps/place/?q=place_id:{result.get('place_id', '')}"
                }
            else:
                print(f"      ⚠️  找到 '{result_name}' 但名稱不匹配")
                return None
        
        print(f"      ❌ 找不到")
        return None
    
    except Exception as e:
        print(f"      ❌ 搜尋失敗: {e}")
        return None

def clean_food_data_strict(dry_run: bool = True):
    """
    嚴格清理 Food 資料
    dry_run=True: 只顯示會刪除的資料，不實際刪除
    dry_run=False: 實際刪除
    """
    
    secrets = load_secrets()
    supabase = create_client(secrets['supabase_url'], secrets['supabase_key'])
    
    print("\n" + "="*70)
    print("🍽️  嚴格清理 Food 資料")
    print("="*70)
    print(f"\n模式: {'🔍 預覽模式（不會實際刪除）' if dry_run else '⚠️  執行模式（會實際刪除）'}\n")
    print("規則: 在 Google Maps 找不到 → 刪除")
    print("搜尋: 「台南市大內區 + 店名」")
    print("-" * 70)
    
    # 取得所有 food 資料
    response = supabase.table('places').select('*').eq('category', 'food').execute()
    places = response.data
    total = len(places)
    
    print(f"\n找到 {total} 筆 food 資料\n")
    print("="*70 + "\n")
    
    to_keep = []  # 保留的
    to_delete = []  # 要刪除的
    to_update = []  # 要更新的
    
    for i, place in enumerate(places, 1):
        name = place.get('name', '')
        place_id = place['id']
        has_location = bool(place.get('location'))
        
        print(f"[{i}/{total}] {name}")
        print(f"   當前狀態: {'有座標' if has_location else '無座標'}")
        
        # 在 Google Maps 搜尋
        google_data = search_on_google_maps(secrets['serpapi_key'], name)
        time.sleep(1.5)  # API 限流
        
        if google_data:
            # 找到了，保留並更新
            print(f"   ✅ 決定: 保留並更新資訊")
            to_keep.append(place)
            
            # 準備更新資料
            coords = google_data['gps_coordinates']
            if coords:
                update_data = {
                    'name': google_data['name'],  # 使用 Google Maps 的正式名稱
                    'address': google_data['address'],
                    'location': f"POINT({coords['longitude']} {coords['latitude']})",
                    'google_url': google_data['google_url'],
                    'metadata': place.get('metadata', {})
                }
                
                # 更新 metadata
                if isinstance(update_data['metadata'], str):
                    update_data['metadata'] = {}
                
                update_data['metadata'].update({
                    'phone': google_data.get('phone'),
                    'rating': google_data.get('rating'),
                    'user_ratings_total': google_data.get('reviews'),
                    'google_verified': True,
                    'last_verified': '2026-02-01'
                })
                
                to_update.append({
                    'id': place_id,
                    'data': update_data
                })
                
                print(f"   📝 更新: 地址={google_data['address'][:30]}...")
                print(f"   📝 更新: 座標=({coords['latitude']}, {coords['longitude']})")
        else:
            # 找不到，刪除
            print(f"   ❌ 決定: 刪除（Google Maps 找不到）")
            to_delete.append(place)
        
        print()
    
    # 統計結果
    print("="*70)
    print("📊 清理結果統計")
    print("="*70)
    print(f"\n✅ 保留: {len(to_keep)} 筆")
    print(f"❌ 刪除: {len(to_delete)} 筆")
    print(f"📝 更新: {len(to_update)} 筆")
    
    # 顯示要刪除的清單
    if to_delete:
        print(f"\n{'='*70}")
        print("⚠️  以下店家將被刪除（Google Maps 找不到）:")
        print("="*70)
        for place in to_delete:
            print(f"   • {place['name']}")
    
    # 實際執行
    if not dry_run:
        print(f"\n{'='*70}")
        print("🚀 開始執行刪除和更新...")
        print("="*70 + "\n")
        
        # 更新保留的資料
        update_success = 0
        for item in to_update:
            try:
                supabase.table('places').update(item['data']).eq('id', item['id']).execute()
                update_success += 1
                print(f"   ✅ 已更新: {item['data']['name']}")
            except Exception as e:
                print(f"   ❌ 更新失敗: {e}")
        
        # 刪除找不到的資料
        delete_success = 0
        for place in to_delete:
            try:
                supabase.table('places').delete().eq('id', place['id']).execute()
                delete_success += 1
                print(f"   🗑️  已刪除: {place['name']}")
            except Exception as e:
                print(f"   ❌ 刪除失敗: {e}")
        
        print(f"\n✅ 執行完成！更新 {update_success} 筆，刪除 {delete_success} 筆")
    else:
        print(f"\n{'='*70}")
        print("ℹ️  這是預覽模式，未實際執行刪除")
        print("="*70)
        print("\n執行實際刪除請使用: python3 scripts/clean_food_strict.py --execute")
    
    print("\n" + "="*70)
    print("✅ 清理完成！")
    print("="*70 + "\n")
    
    return {
        'total': total,
        'keep': len(to_keep),
        'delete': len(to_delete),
        'update': len(to_update),
        'deleted_list': [p['name'] for p in to_delete]
    }

if __name__ == "__main__":
    import sys
    
    # 檢查是否有 --execute 參數
    execute = '--execute' in sys.argv
    
    if not execute:
        print("\n" + "="*70)
        print("⚠️  預覽模式")
        print("="*70)
        print("\n這次執行只會預覽結果，不會實際刪除資料")
        print("如果確定要執行刪除，請使用: python3 scripts/clean_food_strict.py --execute\n")
    else:
        print("\n" + "="*70)
        print("⚠️  警告：執行模式")
        print("="*70)
        print("\n這次執行會實際刪除資料！")
        confirm = input("確定要繼續嗎？(輸入 YES 確認): ")
        if confirm != "YES":
            print("已取消執行")
            sys.exit(0)
    
    result = clean_food_data_strict(dry_run=not execute)
