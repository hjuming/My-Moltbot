# 🐉 小龍女任務：數據品質快速檢查

## 📋 任務目標

查詢 Supabase 資料庫，產生一份簡潔的數據品質報告，測試妳的資料查詢和報告能力。

---

## ✅ 執行步驟

### 步驟 1：確認環境變數

先確認妳可以讀取這些環境變數：
```python
import os
print("✅ 環境變數檢查：")
print(f"SUPABASE_URL: {'有' if os.getenv('SUPABASE_URL') else '無'}")
print(f"SUPABASE_SERVICE_ROLE_KEY: {'有' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else '無'}")
```

### 步驟 2：安裝必要套件（如果還沒有）

```python
import subprocess
import sys

packages = ['supabase']
for pkg in packages:
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
```

### 步驟 3：執行資料查詢

**請執行以下完整的 Python 程式碼**：

```python
import os
from supabase import create_client

# 連接資料庫
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

# 查詢資料
response = supabase.table('places').select('id, name, category, location, address').execute()
places = response.data

# 統計分析
total = len(places)
by_category = {}
with_location = 0
with_address = 0

for place in places:
    # 分類統計
    category = place.get('category', '未分類')
    by_category[category] = by_category.get(category, 0) + 1
    
    # 欄位完整度
    if place.get('location'):
        with_location += 1
    if place.get('address'):
        with_address += 1

# 產生報告
print("=" * 50)
print("📊 My-Moltbot 數據品質報告")
print("=" * 50)
print()
print(f"📍 總筆數：{total}")
print()
print("🏷️  分類分布：")
for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
    percentage = (count / total) * 100
    print(f"   • {cat}: {count} 筆 ({percentage:.1f}%)")
print()
print("✅ 欄位完整度：")
print(f"   • 座標：{with_location}/{total} ({with_location/total*100:.1f}%)")
print(f"   • 地址：{with_address}/{total} ({with_address/total*100:.1f}%)")
print()
print("=" * 50)
print("✅ 報告完成！")
print("=" * 50)
```

---

## 📤 預期輸出格式

妳的回報應該像這樣：

```
==================================================
📊 My-Moltbot 數據品質報告
==================================================

📍 總筆數：556

🏷️  分類分布：
   • pet: 358 筆 (64.4%)
   • dive: 142 筆 (25.5%)
   • food: 56 筆 (10.1%)

✅ 欄位完整度：
   • 座標：500/556 (89.9%)
   • 地址：399/556 (71.8%)

==================================================
✅ 報告完成！
==================================================
```

---

## ⚠️ 重要提醒

1. **直接執行**：不要計劃、不要解釋，直接執行上面的 Python 程式碼
2. **完整輸出**：把所有輸出結果原封不動地回報給老闆
3. **錯誤處理**：如果遇到錯誤，回報完整的錯誤訊息：
   - 錯誤類型
   - 錯誤訊息
   - 發生在哪一行

---

## 🎯 成功標準

- ✅ 成功連接到 Supabase
- ✅ 成功查詢 places 資料表
- ✅ 正確統計總筆數和分類
- ✅ 產生格式化的報告

---

**小龍女，開始執行吧！直接執行步驟 3 的程式碼即可。** 🚀

---

**老闆備註**：
這個任務測試小龍女的：
1. 資料庫連接能力
2. 數據查詢和處理能力
3. 報告產生能力
4. 按照指令執行的能力
