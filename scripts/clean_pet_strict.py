#!/usr/bin/env python3
"""
嚴格清理 Pet 資料
規則：如果在 Google Maps 找不到，就刪除
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

def search_on_google_maps(api_key: str, name: str, address: str) -> Optional[Dict]:
    """
    在 Google Maps 搜尋店家
    回傳：找到的店家資訊，或 None
    """
    try:
        # 提取關鍵字（去掉括號內的分店資訊）
        base_name = name.split('(')[0].split('（')[0].strip()
        
        # 提取地區資訊
        region = ''
        if address:
            # 提取縣市
            for city in ['台北市', '新北市', '桃園市', '台中市', '台南市', '高雄市', '基隆市', '新竹市', '嘉義市']:
                if city in address:
                    region = city
                    break
            # 提取縣
            if not region:
                for county in ['新竹縣', '苗栗縣', '彰化縣', '南投縣', '雲林縣', '嘉義縣', '屏東縣', '宜蘭縣', '花蓮縣', '台東縣', '澎湖縣', '金門縣', '連江縣']:
                    if county in address:
                        region = county
                        break
        
        # 嘗試多種搜尋策略
        search_queries = [
            f"{name} {address}",  # 完整名稱 + 完整地址
            f"{base_name} {region}",  # 基礎名稱 + 縣市
            f"{name}",  # 只用完整名稱
        ]
        
        for query in search_queries:
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
                # 檢查前3個結果
                for result in data['local_results'][:3]:
                    result_name = result.get('title', '')
                    result_address = result.get('address', '')
                    
                    # 名稱匹配檢查（更寬鬆）
                    name_keywords = [w for w in base_name.split() if len(w) > 1]
                    name_match = any(keyword in result_name for keyword in name_keywords) if name_keywords else (base_name[:2] in result_name)
                    
                    # 地址匹配檢查（只要縣市對就算）
                    address_match = True  # 預設為 True，除非明確不符
                    if region and result_address:
                        address_match = region in result_address
                    
                    if name_match and address_match:
                        print(f"      ✅ 找到: {result_name}")
                        print(f"      📍 地址: {result_address}")
                        return {
                            'name': result_name,
                            'address': result_address,
                            'phone': result.get('phone', ''),
                            'rating': result.get('rating'),
                            'reviews': result.get('reviews'),
                            'gps_coordinates': result.get('gps_coordinates', {}),
                            'place_id': result.get('place_id', ''),
                            'google_url': f"https://www.google.com/maps/place/?q=place_id:{result.get('place_id', '')}"
                        }
            
            time.sleep(0.5)  # 避免過快請求
        
        print(f"      ❌ 找不到")
        return None
    
    except Exception as e:
        print(f"      ❌ 搜尋失敗: {e}")
        return None

def clean_pet_data_strict(dry_run: bool = True, limit: int = None):
    """
    嚴格清理 Pet 資料
    dry_run=True: 只顯示會刪除的資料，不實際刪除
    dry_run=False: 實際刪除
    limit: 限制處理筆數（用於測試）
    """
    
    secrets = load_secrets()
    supabase = create_client(secrets['supabase_url'], secrets['supabase_key'])
    
    print("\n" + "="*70)
    print("🐾 嚴格清理 Pet 資料")
    print("="*70)
    print(f"\n模式: {'🔍 預覽模式（不會實際刪除）' if dry_run else '⚠️  執行模式（會實際刪除）'}\n")
    if limit:
        print(f"測試模式: 只處理前 {limit} 筆")
    print("規則: 在 Google Maps 找不到 → 刪除")
    print("搜尋: 「店名 + 地址」")
    print("-" * 70)
    
    # 取得所有 pet 資料
    query = supabase.table('places').select('*').eq('category', 'pet')
    if limit:
        query = query.limit(limit)
    
    response = query.execute()
    places = response.data
    total = len(places)
    
    print(f"\n找到 {total} 筆 pet 資料\n")
    print("="*70 + "\n")
    
    to_keep = []  # 保留的
    to_delete = []  # 要刪除的
    to_update = []  # 要更新的
    
    for i, place in enumerate(places, 1):
        name = place.get('name', '')
        address = place.get('address', '')
        place_id = place['id']
        has_google_url = bool(place.get('google_url'))
        
        print(f"[{i}/{total}] {name}")
        print(f"   地址: {address[:50]}..." if len(address) > 50 else f"   地址: {address}")
        print(f"   當前狀態: {'有 Google URL' if has_google_url else '無 Google URL'}")
        
        # 在 Google Maps 搜尋
        google_data = search_on_google_maps(secrets['serpapi_key'], name, address)
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
                elif not isinstance(update_data['metadata'], dict):
                    update_data['metadata'] = {}
                
                # 保留原有的 pet_friendly_features
                original_metadata = place.get('metadata', {})
                if isinstance(original_metadata, dict):
                    pet_features = original_metadata.get('pet_friendly_features')
                    if pet_features:
                        update_data['metadata']['pet_friendly_features'] = pet_features
                
                update_data['metadata'].update({
                    'phone': google_data.get('phone'),
                    'rating': google_data.get('rating'),
                    'user_ratings_total': google_data.get('reviews'),
                    'google_verified': True,
                    'last_verified': '2026-02-01'
                })
                
                to_update.append({
                    'id': place_id,
                    'original_name': name,
                    'data': update_data
                })
                
                if google_data['name'] != name:
                    print(f"   📝 更名: {name} → {google_data['name']}")
                print(f"   📝 更新座標: ({coords['latitude']:.6f}, {coords['longitude']:.6f})")
        else:
            # 找不到，刪除
            print(f"   ❌ 決定: 刪除（Google Maps 找不到）")
            to_delete.append(place)
        
        print()
    
    # 統計結果
    print("="*70)
    print("📊 清理結果統計")
    print("="*70)
    print(f"\n✅ 保留: {len(to_keep)} 筆 ({len(to_keep)/total*100:.1f}%)")
    print(f"❌ 刪除: {len(to_delete)} 筆 ({len(to_delete)/total*100:.1f}%)")
    print(f"📝 更新: {len(to_update)} 筆")
    
    # 顯示要刪除的清單
    if to_delete:
        print(f"\n{'='*70}")
        print("⚠️  以下店家將被刪除（Google Maps 找不到）:")
        print("="*70)
        for place in to_delete:
            print(f"   • {place['name']} ({place.get('address', '無地址')[:40]}...)")
    
    # 顯示更名的清單
    renamed = [u for u in to_update if u['original_name'] != u['data']['name']]
    if renamed:
        print(f"\n{'='*70}")
        print("📝 以下店家將更名（以 Google Maps 為準）:")
        print("="*70)
        for item in renamed:
            print(f"   • {item['original_name']}")
            print(f"     → {item['data']['name']}")
    
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
                print(f"   ❌ 更新失敗 ({item['original_name']}): {e}")
        
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
        print("\n執行實際刪除請使用:")
        if limit:
            print(f"  python3 scripts/clean_pet_strict.py --execute --limit {limit}")
        else:
            print("  python3 scripts/clean_pet_strict.py --execute")
    
    print("\n" + "="*70)
    print("✅ 清理完成！")
    print("="*70 + "\n")
    
    return {
        'total': total,
        'keep': len(to_keep),
        'delete': len(to_delete),
        'update': len(to_update),
        'renamed': len(renamed) if renamed else 0,
        'deleted_list': [{'name': p['name'], 'address': p.get('address', '')} for p in to_delete],
        'renamed_list': [{'old': u['original_name'], 'new': u['data']['name']} for u in renamed] if renamed else []
    }

if __name__ == "__main__":
    import sys
    
    # 解析參數
    execute = '--execute' in sys.argv
    limit = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    
    if not execute:
        print("\n" + "="*70)
        print("⚠️  預覽模式")
        print("="*70)
        print("\n這次執行只會預覽結果，不會實際刪除資料")
        if limit:
            print(f"測試模式: 只處理前 {limit} 筆")
        print("\n如果確定要執行刪除，請使用:")
        if limit:
            print(f"  python3 scripts/clean_pet_strict.py --execute --limit {limit}")
        else:
            print("  python3 scripts/clean_pet_strict.py --execute")
        print()
    else:
        print("\n" + "="*70)
        print("⚠️  警告：執行模式")
        print("="*70)
        print(f"\n這次執行會實際刪除資料！")
        if limit:
            print(f"（測試模式：只處理前 {limit} 筆）")
        confirm = input("確定要繼續嗎？(輸入 YES 確認): ")
        if confirm != "YES":
            print("已取消執行")
            sys.exit(0)
    
    result = clean_pet_data_strict(dry_run=not execute, limit=limit)
