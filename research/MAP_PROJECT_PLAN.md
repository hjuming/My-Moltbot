# 🗺️ Moltbot Map Hub - 建置計畫書

## 1. 專案願景
建立一個去中心化、私有化且高度風格化的「生活地圖資料庫」。
不再依賴 Google Maps 的單一介面，而是將多年累積的圖資轉化為可程式化的資產，支援「大內美食」、「台灣潛水」、「寵物友善」、「旅遊規劃」等垂直應用。

## 2. 系統策略 (Data Strategy)

### A. 輕量引用型 (Reference) - 美食、旅遊、住宿
*   **現況**：Google Maps 已有完善資訊（評論、照片、營業時間）。
*   **策略**：**不重複造輪子**。我們只儲存「索引」與「策展邏輯」。
*   **資料庫存什麼？**：`Place ID`、`名稱`、`分類`、`Google連結`。
*   **使用者體驗**：在我們的 App 篩選出一組清單（例如「大內區私藏」），想看細節點擊直接跳轉 Google Maps App。

### B. 獨家資產型 (Proprietary) - 潛水 (Dive)
*   **現況**：Google Maps 資料匱乏，地點多在海上或荒島，名稱不統一。
*   **策略**：**完整託管建立**。這是未來的核心資產。
*   **資料庫存什麼？**：精確經緯度 (GPS)、深度、流況、難度、別名、潛水員筆記、季節建議。
*   **使用者體驗**：完全在我們的 App 內瀏覽詳細資訊（因為 Google 上沒有）。

### C. 混合增強型 (Enriched) - 寵物 (Pet)
*   **現況**：Google 有基礎地點，但缺乏「寵物友善細節」。
*   **策略**：**資料增補**。以 Google 地點為基礎，疊加 Pets WEDO 的業務資料。
*   **資料庫存什麼？**：Google 基礎資訊 + **寵物友善標籤** (可落地、有草地、寵物餐)、合作特約狀態。
*   **使用者體驗**：在 App 內看到地圖，並能依據「有沒有草地」這種特殊條件進行篩選。

---

## 3. 資料庫設計 (Schema Design)

### Table: `places` (地點主表)

| 欄位名 | 類型 | 說明 |
| :--- | :--- | :--- |
| `id` | UUID | 主鍵 |
| `name` | Text | 地點名稱 |
| `category` | Text | 主分類 (food, dive, pet, travel) |
| `dataset_type` | Text | 資料類型 (google_ref, proprietary, enriched) |
| `location` | Geography | 經緯度座標 (Point) **(潛水點最重要)** |
| `google_place_id`| Text | Google Maps 唯一 ID (Google 生態系連結用) |
| `google_url` | Text | 跳轉連結 (針對 A 類資料) |
| `metadata` | JSONB | **特有欄位** (詳見下方) |

### Metadata 結構差異 (JSONB)

#### 🍽️ 美食/旅遊 (Type A: Reference)
```json
{
  "tags": ["老闆私藏", "大內區"], 
  "curation_note": "這家的布丁是隱藏版，菜單上沒有" // 僅存個人的策展筆記
}
```

#### 🤿 潛水 (Type B: Proprietary)
```json
{
  "aliases": ["大香菇", "Flower Garden"], // 別名系統
  "max_depth": 30,
  "difficulty": "advance",
  "current": "strong", // 流況
  "entry_type": "boat",
  "notes": "建議早上第一支下，能見度最好...", // 潛水員經驗談
  "season": ["summer", "autumn"]
}
```

#### 🐾 寵物 (Type C: Enriched)
```json
{
  "pet_friendly_features": {
    "indoor_allowed": true,
    "floor_allowed": true, // 可落地
    "has_grass": true,
    "pet_menu": false
  },
  "business_type": "restaurant", // 餐廳/旅館/醫院
  "wedo_partner": true // 是否為 Wedo 特約
}
```

---

## 4. 分類對照表 (Mapping Strategy)

將您 Google Maps 的清單名稱對應到系統分類：

| Google 清單名稱 | System Category | System Subcategory | tags (自動標記) |
| :--- | :--- | :--- | :--- |
| 咖啡廳/簡餐店/冰品店/甜點店 | `food` | `cafe` | `dessert`, `brunch` |
| 日式/居酒屋/壽司/拉麵 | `food` | `japanese` | `sushi`, `izakaya`, `ramen` |
| 燒肉店/燒烤店 | `food` | `bbq` | `yakiniku` |
| 美式/披薩/漢堡/墨西哥菜 | `food` | `american` | `burger`, `pizza` |
| 小吃/便當/夜市... | `food` | `street_food` | `local` |
| 火鍋餐廳 | `food` | `hotpot` | |
| 酒吧/聊天 | `food` | `bar` | `alcohol` |
| 潛水 DIVING | `dive` | `dive_site` | |
| 住宿/旅館/民宿... | `travel` | `accommodation`| |
| 景點/車站/機場... | `travel` | `attraction` | |
| 親子/百貨/賣場 | `life` | `shopping` | `family` |

---

## 5. 執行階段 (Phases)

### Phase 1: 基礎建設 (Infrastructure)
1.  建立 Supabase 專案。
2.  建立 `places` 表格與 PostGIS 擴充。
3.  設定 API 權限 (Row Level Security)。

### Phase 2: 資料清洗與匯入 (Ingest)
1.  使用者匯出 Google Takeout JSON。
2.  Antigravity 撰寫 Python 腳本 (`scripts/import_google_takeout.py`)。
3.  將 JSON 轉換格式並寫入 Supabase。

### Phase 3: 自動化維護 (Automation)
1.  **小龍女每日任務**：
    *   查詢 `SELECT * FROM places WHERE google_place_id IS NULL OR updated_at < NOW() - INTERVAL '30 days'`。
    *   每天處理 10-20 筆 (避免爆 API 額度)。
    *   使用 SerpApi 抓取最新營業時間與歇業狀態。
    *   更新 Supabase。

### Phase 4: 應用開發 (Application)
1.  開發「大內美食地圖」Web 介面 (Next.js + Mapbox/Google Maps JS)。
2.  開發「台灣潛水地圖」資訊頁。

---

*此文件由 Antigravity 規劃，作為 My-Moltbot 地圖專案的開發總綱。*
