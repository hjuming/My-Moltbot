#!/usr/bin/env python3
"""
分析 Supabase places 資料表狀態
檢查欄位完整性、分類分布、標籤使用情況
"""

import os
from typing import Dict, List
from collections import Counter
from supabase import create_client
from dotenv import load_dotenv

def load_secrets() -> Dict[str, str]:
    """載入環境變數"""
    env_path = os.path.join(os.path.dirname(__file__), '..', 'moltbot設定', 'ZEABUR_ENV_SECRETS.env')
    load_dotenv(env_path)
    
    return {
        'supabase_url': os.getenv('SUPABASE_URL'),
        'supabase_key': os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    }

def analyze_places_data(supa_url: str, supa_key: str):
    """分析 places 資料表"""
    
    supabase = create_client(supa_url, supa_key)
    
    print("\n" + "="*60)
    print("📊 Supabase Places 資料分析")
    print("="*60 + "\n")
    
    # 1. 取得所有資料
    response = supabase.table('places').select('*').execute()
    places = response.data
    
    total_count = len(places)
    print(f"📍 總筆數：{total_count}")
    print("-" * 60)
    
    # 2. 分類統計
    categories = Counter(place.get('category') for place in places)
    print("\n🏷️  分類分布：")
    for cat, count in categories.most_common():
        percentage = (count / total_count) * 100
        print(f"   {cat or '(未分類)':<15} {count:>4} 筆 ({percentage:>5.1f}%)")
    
    # 3. 欄位完整性檢查
    print("\n✅ 欄位完整性：")
    fields_to_check = {
        'name': '名稱',
        'address': '地址',
        'location': '座標',
        'google_url': 'Google 地圖連結',
        'category': '分類',
    }
    
    for field, label in fields_to_check.items():
        filled = sum(1 for p in places if p.get(field))
        empty = total_count - filled
        percentage = (filled / total_count) * 100
        status = "✅" if percentage > 95 else "⚠️" if percentage > 80 else "❌"
        print(f"   {status} {label:<15} {filled:>4}/{total_count} ({percentage:>5.1f}%)")
    
    # 4. metadata 欄位分析
    print("\n📦 metadata 欄位統計：")
    metadata_fields = set()
    for place in places:
        metadata = place.get('metadata')
        if metadata and isinstance(metadata, dict):
            metadata_fields.update(metadata.keys())
    
    if metadata_fields:
        for field in sorted(metadata_fields):
            count = sum(1 for p in places 
                       if isinstance(p.get('metadata'), dict) and p.get('metadata', {}).get(field))
            percentage = (count / total_count) * 100
            print(f"   • {field:<25} {count:>4} 筆 ({percentage:>5.1f}%)")
    else:
        print("   (無 metadata)")
    
    # 5. 標籤分析
    print("\n🏷️  標籤使用情況：")
    all_tags = []
    places_with_tags = 0
    
    for place in places:
        metadata = place.get('metadata')
        if isinstance(metadata, dict):
            tags = metadata.get('tags', [])
            if tags:
                places_with_tags += 1
                all_tags.extend(tags)
    
    if all_tags:
        tag_counts = Counter(all_tags)
        print(f"   使用標籤的筆數：{places_with_tags}/{total_count} ({places_with_tags/total_count*100:.1f}%)")
        print(f"   總標籤數：{len(tag_counts)} 個")
        print(f"\n   前 10 個常用標籤：")
        for tag, count in tag_counts.most_common(10):
            print(f"      • {tag:<20} {count:>4} 次")
    else:
        print("   ⚠️  尚未使用標籤")
    
    # 6. 分類別詳細資料
    print("\n" + "="*60)
    print("📋 各分類詳細統計")
    print("="*60)
    
    for category in sorted(categories.keys()):
        cat_places = [p for p in places if p.get('category') == category]
        
        print(f"\n【{category}】({len(cat_places)} 筆)")
        print("-" * 40)
        
        # 地址完整性
        with_address = sum(1 for p in cat_places if p.get('address'))
        print(f"  地址：{with_address}/{len(cat_places)} ({with_address/len(cat_places)*100:.1f}%)")
        
        # 座標完整性
        with_location = sum(1 for p in cat_places if p.get('location'))
        print(f"  座標：{with_location}/{len(cat_places)} ({with_location/len(cat_places)*100:.1f}%)")
        
        # Google URL
        with_google = sum(1 for p in cat_places if p.get('google_url'))
        print(f"  Google 地圖：{with_google}/{len(cat_places)} ({with_google/len(cat_places)*100:.1f}%)")
        
        # 評分
        with_rating = sum(1 for p in cat_places 
                         if isinstance(p.get('metadata'), dict) and p.get('metadata', {}).get('rating'))
        if with_rating > 0:
            ratings = [p.get('metadata', {}).get('rating', 0) for p in cat_places 
                      if isinstance(p.get('metadata'), dict) and p.get('metadata', {}).get('rating')]
            avg_rating = sum(ratings) / len(ratings)
            print(f"  評分：{with_rating}/{len(cat_places)} 筆有評分 (平均 {avg_rating:.1f} ⭐)")
    
    # 7. 需要修正的項目
    print("\n" + "="*60)
    print("⚠️  需要注意的項目")
    print("="*60 + "\n")
    
    issues = []
    
    # 缺少座標
    no_location = [p for p in places if not p.get('location')]
    if no_location:
        issues.append(f"❌ {len(no_location)} 筆缺少座標")
    
    # 缺少地址
    no_address = [p for p in places if not p.get('address')]
    if no_address:
        issues.append(f"⚠️  {len(no_address)} 筆缺少地址")
    
    # 缺少分類
    no_category = [p for p in places if not p.get('category')]
    if no_category:
        issues.append(f"❌ {len(no_category)} 筆缺少分類")
    
    # 缺少 Google URL
    no_google = [p for p in places if not p.get('google_url')]
    if no_google:
        issues.append(f"⚠️  {len(no_google)} 筆缺少 Google 地圖連結")
    
    if issues:
        for issue in issues:
            print(f"   {issue}")
    else:
        print("   ✅ 所有資料完整！")
    
    print("\n" + "="*60)
    print("✅ 分析完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    secrets = load_secrets()
    analyze_places_data(
        secrets['supabase_url'],
        secrets['supabase_key']
    )
