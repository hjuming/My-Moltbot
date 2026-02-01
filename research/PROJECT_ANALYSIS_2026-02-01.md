# 📊 My-Moltbot 專案全面分析報告

**生成時間**：2026-02-01  
**分析者**：神雕大俠 (Cursor AI Agent)  
**專案路徑**：`/Users/MING/Sites/My-Moltbot`

---

## 🎯 專案概述

### 專案定位
**My-Moltbot** 是一個多功能的自動化管理中樞，整合了三大核心功能：

1. **AI 助理機器人（小龍女）**：透過 Telegram 與 Zeabur 運行的 AI 秘書
2. **GitHub 專案監控系統**：自動化追蹤與報告工具
3. **Map WEDO 地圖資料庫**：去中心化的生活地圖資料平台

---

## 🏗️ 專案架構

### 1. 核心組件

#### A. 小龍女 AI 助理 🐉
- **人設檔案**：`research/personas/LITTLE_DRAGON_GIRL.md`
- **技能手冊**：`research/skills/DATA_PROCESSING_SOP.md`
- **工具定義**：`research/tools/TOOL_DEFINITIONS.json`
- **運行環境**：Zeabur (Python 3.11+)
- **主要職責**：
  - 資料蒐集與分析
  - GitHub Repo 監控
  - 檔案處理（CSV、圖片、OCR）
  - Telegram 通知推送

#### B. GitHub Actions 自動化
- **工作流程**：`.github/workflows/daily_sync.yml`
- **排程時間**：每天台灣時間 09:10 (UTC 01:10)
- **執行任務**：
  1. 更新 GitHub 專案清單
  2. 爬取熱門 Repos (RepoInside)
  3. 生成日報並推送至 Telegram
  4. 更新 `research/LOG.md` 與 `research/TRENDING_REPOS.md`

#### C. Map WEDO 地圖平台 🗺️
- **前端技術棧**：
  - Next.js 16.1.6 + React 19
  - TypeScript
  - Supabase Client
  - Lucide React Icons
  - 玻璃擬態 UI 設計
- **後端資料庫**：
  - Supabase (PostgreSQL + PostGIS)
  - 地理空間查詢支援
  - Row Level Security (RLS)

---

## 📂 目錄結構解析

```
My-Moltbot/
├── .github/workflows/          # GitHub Actions 自動化
│   └── daily_sync.yml          # 每日同步與監控
├── .venv/                      # Python 虛擬環境 (已建立)
├── map-web/                    # Map WEDO 前端專案
│   ├── app/                    # Next.js App Router
│   │   ├── page.tsx            # 主頁面（地圖篩選介面）
│   │   ├── layout.tsx          # 全域佈局
│   │   └── globals.css         # 玻璃擬態樣式
│   ├── lib/
│   │   └── supabase.ts         # Supabase 客戶端
│   └── package.json            # 前端依賴
├── moltbot設定/
│   └── ZEABUR_ENV_SECRETS.env  # 環境變數（API Keys）
├── research/                   # 研究與產出目錄
│   ├── map/                    # 地圖專案相關
│   │   ├── schema_setup.sql    # 資料庫 Schema
│   │   ├── 台南大內尋飽圖_GoogleMap匯入清單.csv
│   │   └── 台灣潛水地圖 DIVE SITE.kmz
│   ├── personas/
│   │   └── LITTLE_DRAGON_GIRL.md
│   ├── skills/
│   │   └── DATA_PROCESSING_SOP.md
│   ├── tools/
│   │   └── TOOL_DEFINITIONS.json
│   ├── LOG.md                  # 自動化日誌
│   ├── MAP_PROJECT_PLAN.md     # 地圖專案總綱
│   └── TASKS.md                # 任務追蹤
└── scripts/                    # 自動化腳本
    ├── clean_with_google_api.py         # 資料清洗腳本 (NEW)
    ├── import_danei_enriched.py         # 大內美食匯入 (NEW)
    ├── template_google_search.py        # Google Maps API 模版 (NEW)
    ├── enrich_danei_with_serpapi.py     # SerpApi 整合
    ├── import_local_maps.py             # KMZ 匯入
    └── update_repos.sh                  # Repo 更新腳本
```

---

## 🔑 環境變數與 API Keys

### 已配置的服務

| 服務類型 | 變數名稱 | 狀態 | 用途 |
|---------|---------|------|------|
| **搜尋引擎** | `TAVILY_API_KEY` | ✅ | 一般網頁搜尋 |
| **Google Maps** | `SERPAPI_API_KEY` | ✅ | 地圖資料搜尋與驗證 |
| **OpenAI** | `OPENAI_API_KEY` | ✅ | AI 模型呼叫 |
| **Telegram Bot** | `TELEGRAM_BOT_TOKEN` | ✅ | 小龍女通知推送 |
| **Telegram Chat** | `TELEGRAM_CHAT_ID` | ✅ | 接收者 ID |
| **GitHub (寫入)** | `MANAGEMENT_TOKEN` | ✅ | My-Moltbot Repo 修改權限 |
| **GitHub (唯讀)** | `READ_ONLY_PAT` | ✅ | 讀取所有 Repos |
| **Gmail** | `GMAIL_ACCOUNT` | ✅ | 信件發送 |
| **Gmail** | `GMAIL_APP_PASSWORD` | ✅ | SMTP 授權 |
| **Supabase** | `SUPABASE_URL` | ✅ | 資料庫連線 |
| **Supabase** | `SUPABASE_SERVICE_ROLE_KEY` | ✅ | 完整操作權限 |
| **Supabase** | `SUPABASE_ANON_KEY` | ✅ | 公開唯讀 API |

### 缺少的關鍵 Key
- ❌ `GOOGLE_MAPS_API_KEY`（但已用 SerpApi 替代，功能等同）

---

## 🗺️ Map WEDO 專案深度分析

### 資料策略（三種類型）

#### Type A: 輕量引用型 (Reference)
- **適用類別**：美食、旅遊、住宿
- **策略**：只儲存索引，細節連結到 Google Maps
- **儲存欄位**：`name`, `category`, `google_url`, `google_place_id`

#### Type B: 獨家資產型 (Proprietary)
- **適用類別**：潛水 (Dive)
- **策略**：完整託管，Google Maps 資料匱乏
- **儲存欄位**：精確座標、深度、流況、難度、潛水員筆記
- **metadata 範例**：
  ```json
  {
    "aliases": ["大香菇", "Flower Garden"],
    "max_depth": 30,
    "difficulty": "advance",
    "current": "strong",
    "entry_type": "boat",
    "notes": "建議早上第一支下，能見度最好"
  }
  ```

#### Type C: 混合增強型 (Enriched)
- **適用類別**：寵物友善 (Pet)
- **策略**：Google 基礎 + 自訂標籤
- **儲存欄位**：Google 資訊 + 寵物友善特徵
- **metadata 範例**：
  ```json
  {
    "pet_friendly_features": {
      "indoor_allowed": true,
      "floor_allowed": true,
      "has_grass": true
    },
    "wedo_partner": true
  }
  ```

### 資料庫 Schema

```sql
-- PostGIS 空間資料庫
places 表格：
  - id (UUID)
  - name (Text)
  - category (food/dive/pet/travel)
  - dataset_type (google_ref/proprietary/enriched)
  - location (Geography POINT) -- PostGIS 地理座標
  - address (Text)
  - google_place_id (Text)
  - google_url (Text)
  - metadata (JSONB) -- 彈性欄位
  - rating (Numeric)
  - is_verified (Boolean)
  - is_closed (Boolean)

索引：
  - places_location_idx (GIST 空間索引)

安全性：
  - RLS 啟用
  - 公開唯讀
  - Service Role 可修改
```

### 前端功能特色

1. **智慧篩選系統**：
   - 四大類別：美食、旅遊、潛水、寵物
   - 動態標籤過濾
   - 即時搜尋

2. **地理定位排序**：
   - 自動取得使用者位置
   - Haversine 距離計算
   - 依距離由近到遠排序

3. **玻璃擬態 UI**：
   - 半透明毛玻璃效果
   - 漸層色彩分類（Food: 橙色、Dive: 藍色、Pet: 綠色、Travel: 紫色）
   - 響應式設計

4. **無限載入**：
   - 每次顯示 30 筆
   - 點擊載入更多

---

## 🤖 小龍女 AI 助理設定

### 核心人設規則

1. **安全守則（最高優先）**：
   - ✅ 只能修改 `research/` 目錄
   - ❌ 絕對禁止 `git push -f`
   - ❌ 禁止修改 `scripts/` 與 `.github/`
   - ❌ 對其他 Repos 唯讀

2. **語氣風格**：
   - 繁體中文
   - 親切有禮，適度使用 Emoji
   - 稱呼用戶為「老闆」
   - 禁止機械化用語

3. **技能範圍**：
   - CSV/圖片處理
   - OCR 文字辨識
   - GitHub API 查詢
   - Markdown 報告生成
   - Telegram 推送

### 技術依賴

```json
{
  "system_packages": [
    "git", "curl", "wget",
    "tesseract-ocr", "libtesseract-dev"
  ],
  "python_packages": [
    "requests", "pandas", "openpyxl",
    "PyGithub", "python-telegram-bot",
    "pillow", "pytesseract",
    "openai", "google-search-results",
    "beautifulsoup4", "tavily-python"
  ]
}
```

---

## 📜 最新開發成果（神雕大俠交接）

### 今日完成的三大腳本

#### 1. 玄鐵重劍模版 (`template_google_search.py`)
- **用途**：標準化 Google Maps API 呼叫
- **特色**：
  - 自動載入環境變數
  - 完整錯誤處理（HTTP 錯誤、網路逾時）
  - 資料標準化函式
  - 測試通過（成功搜尋大內豆菜麵）

#### 2. 資料清洗腳本 (`clean_with_google_api.py`)
- **任務**：清洗 Supabase 中的 pet & dive 資料
- **邏輯**：
  1. 讀取 `category IN ('pet', 'dive')` 的資料
  2. 用 SerpApi 驗證每筆店家存在性
  3. 更新座標、地址、電話
  4. 刪除已歇業店家
  5. 標記找不到的店家
- **安全機制**：禮貌性 0.5 秒延遲，避免 API 限流

#### 3. 大內尋飽圖匯入 (`import_danei_enriched.py`)
- **任務**：匯入 48 筆台南大內美食
- **資料來源**：`research/map/台南大內尋飽圖_GoogleMap匯入清單.csv`
- **流程**：
  1. 讀取 CSV（店名 + 地址關鍵字）
  2. 搜尋 Google Maps 取得座標與電話
  3. 寫入 Supabase `places` 表
- **標籤**：自動加上 `["大內美食", "尋飽圖"]`

### 測試結果

✅ **玄鐵重劍模版測試成功**：
```
🔍 搜尋：大內豆菜麵 台南市大內區
   ✅ 大內豆菜麵
      📍 742臺南市大內區149號
      🗺️  座標：(23.1185729, 120.3587524)
      📞 06 576 3509
      ⭐ 4 (119 則評論)
```

---

## 🚀 待執行任務

### 優先級 1：資料清洗與匯入
```bash
# 任務 1：匯入大內尋飽圖
python3 scripts/import_danei_enriched.py

# 任務 2：清洗潛水與寵物資料
python3 scripts/clean_with_google_api.py
```

### 優先級 2：前端部署
```bash
cd map-web
npm run build
# 部署至 Vercel 或 Zeabur
```

### 優先級 3：小龍女功能增強
- [ ] 整合 Map WEDO 資料維護功能
- [ ] 每日自動檢查歇業店家
- [ ] 新增「缺座標店家」補完任務

---

## 🔧 開發環境設定

### Python 環境
- ✅ 已建立虛擬環境：`.venv/`
- ✅ 已安裝套件：
  - `googlemaps==4.10.0`
  - `supabase==2.27.2`
  - `python-dotenv==1.2.1`
  - `requests` (系統預裝)

### Next.js 環境
```json
{
  "next": "16.1.6",
  "react": "19.2.3",
  "@supabase/supabase-js": "^2.93.3",
  "lucide-react": "^0.563.0"
}
```

---

## 🎓 學習資源與文件

### 專案文件
1. **Map 專案總綱**：`research/MAP_PROJECT_PLAN.md`
2. **小龍女人設**：`research/personas/LITTLE_DRAGON_GIRL.md`
3. **資料處理 SOP**：`research/skills/DATA_PROCESSING_SOP.md`
4. **最終指令書**：`INSTRUCTION_FOR_DRAGON_MAIDEN.md`

### 外部連結
- Supabase Dashboard: https://ivhitbbyyscvjrgmtqxg.supabase.co
- Map WEDO 網站: https://map.wedopr.com
- GitHub Repo: https://github.com/hjuming/My-Moltbot

---

## 📊 專案統計

### 程式碼規模
- **Python 腳本**：12 個主要腳本
- **Next.js 頁面**：1 個主頁 + 佈局
- **SQL Schema**：1 個完整資料表定義
- **Markdown 文件**：8+ 個規劃與說明文件

### API 配額使用
- **SerpApi**：每月 100 次免費搜尋
- **Supabase**：免費版 500 MB 資料庫
- **GitHub Actions**：2000 分鐘/月

---

## 🚨 注意事項

### 安全守則
1. **環境變數保護**：
   - `.gitignore` 已排除 `moltbot設定/`
   - 所有 Secrets 僅存本機與 GitHub Secrets

2. **Git 操作規範**：
   - Commit 訊息包含 `[skip ci]` 避免無限迴圈
   - 禁止 `git add .`（使用 `git add research/`）
   - 絕對禁止 `git push -f`

3. **API 配額管理**：
   - 腳本內建延遲機制
   - 批次處理每次限制 10-20 筆

### 已知問題
- ❌ 部分潛水點座標混在文字欄位中（待清洗）
- ⚠️  寵物資料地址含 HTML 標籤（已有清理函式）
- ⚠️  大內尋飽圖 CSV 部分店名過於簡略（可能搜尋錯誤）

---

## 🎯 未來規劃

### Phase 1：資料完善（本週）
- 執行清洗腳本
- 匯入所有 KMZ 資料
- 驗證座標正確性

### Phase 2：功能增強（下週）
- 地圖視覺化（Mapbox GL JS）
- 路線規劃功能
- 使用者收藏系統

### Phase 3：社群互動（下月）
- 使用者評論系統
- 照片上傳
- 推薦演算法

---

## 📞 聯絡資訊

- **專案維護者**：MING & Antigravity (Google DeepMind)
- **小龍女 Telegram Bot**：@PetsGow_bot
- **技術支援**：透過 GitHub Issues

---

**報告完畢！** 🐉

*神雕大俠已完成環境建置、腳本開發與文件整理。小龍女隨時可以接手執行任務！*
