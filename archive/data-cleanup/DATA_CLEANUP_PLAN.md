# 📊 My-Moltbot 圖資清理與完善計劃

**日期**：2026-02-01  
**現況**：556 筆圖資（pet: 358, dive: 142, food: 56）

---

## 🔍 當前數據問題

### 📉 欄位完整性問題

| 欄位 | 完整度 | 狀態 | 需修正筆數 |
|------|--------|------|-----------|
| 名稱 | 100.0% | ✅ | 0 |
| 分類 | 100.0% | ✅ | 0 |
| description | 98.6% | ✅ | 8 |
| tags | 98.6% | ✅ | 8 |
| 座標 | 89.9% | ⚠️ | **56** (food缺座標) |
| 地址 | 71.8% | ❌ | **157** (dive缺地址) |
| phone | 60.8% | ⚠️ | 218 |
| Google URL | 10.1% | ❌ | **500** (僅food有) |

### 📊 分類別狀況

#### 1. Pet (358 筆) 64.4%
- ✅ 座標：100% (358/358)
- ⚠️ 地址：95.8% (343/358) - **缺 15 筆**
- ❌ Google URL：0% (0/358) - **缺 358 筆**
- ⚠️ 電話：60.8% (約 218 筆)

#### 2. Dive (142 筆) 25.5%
- ✅ 座標：100% (142/142)
- ❌ 地址：0% (0/142) - **缺 142 筆**
- ❌ Google URL：0% (0/142) - **缺 142 筆**
- 特殊：潛點資料是自建的專業資訊

#### 3. Food (56 筆) 10.1%
- ✅ 地址：100% (56/56)
- ❌ 座標：0% (0/56) - **缺 56 筆**
- ✅ Google URL：100% (56/56)
- 來源：台南大內尋飽圖 CSV

---

## 🎯 清理與完善優先順序

### 階段 1：修正 Food 資料（立即執行）⭐⭐⭐

**問題**：56 筆 food 缺少座標

**解決方案**：
```python
# 使用 SerpApi 從 Google Maps URL 取得座標
scripts/fix_food_coordinates.py
```

**預期結果**：
- ✅ Food 座標完整度：100%
- ✅ 整體座標完整度：100%

---

### 階段 2：補強 Pet 資料（高優先）⭐⭐⭐

**問題 1**：15 筆 pet 缺少地址

**解決方案**：
```python
# 從 Google Maps 反向地理編碼取得地址
scripts/fix_pet_addresses.py
```

**問題 2**：358 筆 pet 缺少 Google Maps URL

**解決方案**：
```python
# 使用名稱+地址搜尋 Google Maps，取得 URL
scripts/enrich_pet_google_urls.py
```

**預期結果**：
- ✅ Pet 地址完整度：100%
- ✅ Pet Google URL 完整度：100%

---

### 階段 3：補強 Dive 資料（選擇性）⭐⭐

**問題**：142 筆 dive 缺少地址和 Google URL

**策略**：
1. **地址**：可選擇性補充（潛點可能沒有明確地址）
   - 使用反向地理編碼取得大致位置（縣市+區域）
   - 例如：「屏東縣恆春鎮外海」

2. **Google URL**：可選擇性補充
   - 潛點可能無 Google Maps 商家資料
   - 可產生座標指向的 Google Maps 連結
   - 格式：`https://www.google.com/maps?q=緯度,經度`

**解決方案**：
```python
# 為潛點補充地址和地圖連結
scripts/enrich_dive_locations.py
```

---

### 階段 4：電話號碼補強（低優先）⭐

**問題**：約 218 筆缺少電話

**解決方案**：
```python
# 從 Google Maps 取得電話號碼
scripts/enrich_phone_numbers.py
```

---

## 🤖 小龍女任務規劃

### 任務 1：環境確認 ✅
- [x] 檢查 Zeabur 環境
- [x] 確認 Python 套件
- [x] 推送 requirements.txt
- [x] 重新部署

### 任務 2：每日資料品質監控 🔄
**目標**：讓小龍女每天回報圖資品質狀態

**建立腳本**：
```python
# research/tasks/daily_data_quality_check.py
# 產生簡報格式的品質報告
```

**小龍女執行**：
1. 每天早上 9:00 自動執行
2. 透過 Telegram 回報：
   - 📊 總筆數變化
   - ✅ 欄位完整度
   - ⚠️ 需要注意的項目
   - 🔥 異常資料（重複、錯誤）

### 任務 3：簡單資料修正提醒 🔔
**目標**：發現異常時通知

**範例**：
- ❌ 發現重複資料：「板橋動物之家」出現 2 次
- ⚠️ 座標異常：座標在海外
- ⚠️ 電話格式錯誤：不符合台灣格式

---

## 📋 執行清單

### 立即執行（本機）

```bash
# 1. 修正 food 座標
python3 scripts/fix_food_coordinates.py

# 2. 補強 pet 地址
python3 scripts/fix_pet_addresses.py

# 3. 補強 pet Google URLs
python3 scripts/enrich_pet_google_urls.py

# 4. 重新分析確認
python3 scripts/analyze_places_data.py
```

### 小龍女設定（GitHub Actions）

```yaml
# .github/workflows/daily_data_quality.yml
name: Daily Data Quality Check

on:
  schedule:
    - cron: '0 1 * * *'  # 每天早上 9:00 (UTC+8)
  workflow_dispatch:

jobs:
  quality_check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check Data Quality
        run: python research/tasks/daily_data_quality_check.py
      - name: Notify Telegram
        run: |
          curl -X POST "https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage" \
            -d chat_id="${{ secrets.TELEGRAM_CHAT_ID }}" \
            -d text="$(cat quality_report.txt)"
```

---

## 🎯 完成後的目標狀態

### 預期完整度

| 欄位 | 目標完整度 | 當前 | 差距 |
|------|-----------|------|------|
| 名稱 | 100% | 100% | ✅ |
| 分類 | 100% | 100% | ✅ |
| 座標 | 100% | 89.9% | +10.1% |
| 地址 | 95%+ | 71.8% | +23.2% |
| Google URL | 90%+ | 10.1% | +79.9% |
| 電話 | 80%+ | 60.8% | +19.2% |

### 品質指標

- ✅ **所有資料都有座標**（地圖顯示必要）
- ✅ **95%+ 資料有地址**（使用者查詢友善）
- ✅ **90%+ 資料有 Google URL**（可導航、查詢評價）
- ✅ **80%+ 資料有電話**（可直接聯繫）
- ✅ **標籤正確分類**（搜尋、篩選功能）

---

## 🚀 開始執行

**建議老闆：**

1. **先執行階段 1-2**（修正 food 和 pet 資料）
2. **測試小龍女品質監控**（建立每日回報機制）
3. **觀察一週後決定是否執行階段 3-4**

**準備好了嗎？我們從階段 1 開始！** 🎯

---

**神雕大俠**  
*資料品質管理顧問*
