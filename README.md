# 📝 My-Moltbot：龍蝦機器人管理中樞

**專案定位**：Zeabur 雲端 Telegram Bot 的資料中樞與自動化協作平台

---

## 🎯 專案概述

本專案是「龍蝦機器人（Moltbot）」的後端資料庫與自動化中樞。它不直接運行 Bot 邏輯，而是作為：
- 📚 **知識庫**：存放專案清單、日誌、研究文件
- 🤖 **協作平台**：Bot（小龍女）與開發者（老闆、神雕大俠）的協作空間
- ⚙️ **自動化中樞**：透過 GitHub Actions 定時執行監測與通知
- 🗺️ **Map WEDO 網站**：去中心化生活地圖資料平台

---

## 🏗️ 專案架構

### 系統組成

```
┌─────────────────────────────────────────────────────┐
│  Telegram (用戶介面)                                 │
│  - 老闆透過 Telegram 與小龍女互動                     │
│  - 接收自動化通知與日報                               │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│  Zeabur (執行環境)                                   │
│  - 小龍女 Bot 本體運行在此                           │
│  - Node.js/Python 雲端環境                           │
│  - 處理 Telegram 指令與通知                          │
│  - 資源配置：CPU 1500m, 記憶體 2048Mi                │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│  GitHub - My-Moltbot Repo (資料中樞)                 │
│  - research/  ← 小龍女可讀寫的工作區                 │
│  - scripts/   ← 自動化腳本（開發者維護）             │
│  - map-web/   ← Map WEDO 網站前端                    │
└───────────────┬─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────┐
│  GitHub Actions (自動化排程)                         │
│  - 每日 09:10 執行專案監測                           │
│  - 推送結果到 research/                              │
│  - 觸發小龍女通知老闆                                │
└─────────────────────────────────────────────────────┘
```

---

## 📂 目錄結構與權限

```
My-Moltbot/
├── .github/workflows/          # GitHub Actions 自動化配置
│   └── daily_sync.yml          # 每日同步與監控任務
│
├── config/                     # 環境變數與機密資料 (⚠️ 不上傳 GitHub)
│   └── (本機配置檔案)          # API Keys 與 Tokens
│
├── research/                   # 🐉 小龍女的工作區（可讀寫）
│   ├── LOG.md                  # 自動化日誌
│   ├── GITHUB_REPOS.md         # 專案清單
│   ├── TRENDING_REPOS.md       # 熱門專案
│   ├── map/                    # Map WEDO 資料檔案
│   ├── personas/               # AI 人設定義
│   ├── skills/                 # 技能手冊
│   └── tools/                  # 工具規格
│
├── scripts/                    # 自動化腳本（開發者維護）
│   ├── update_repos.sh         # 更新 Repo 清單
│   ├── update_trending.sh      # 爬取熱門專案
│   └── clean_with_google_api.py # Map 資料清洗
│
└── map-web/                    # 🗺️ Map WEDO 網站前端
    ├── app/                    # Next.js 應用
    ├── lib/                    # Supabase 客戶端
    └── package.json            # 前端依賴
```

### 權限說明

| 目錄/檔案 | 小龍女 | 開發者 | GitHub Actions |
|----------|--------|--------|---------------|
| `research/` | ✅ 讀寫 | ✅ 讀寫 | ✅ 讀寫 |
| `scripts/` | ❌ 唯讀 | ✅ 讀寫 | ✅ 執行 |
| `map-web/` | ❌ 唯讀 | ✅ 讀寫 | ❌ - |
| `config/` | ❌ 不可見 | ✅ 讀寫 | ❌ 不可見 |
| `.github/` | ❌ 唯讀 | ✅ 讀寫 | ✅ 執行 |

---

## 🐉 小龍女（Telegram Bot）

### 資源配置（2026-02-01 調整）

**Zeabur 平台配置**：
- **CPU**：1500m (1.5 核心)
- **記憶體**：2048Mi (2 GB)
- **平均使用**：CPU 10-20%, 記憶體 680 MB
- **每月成本**：約 $14-15 美金

**為什麼需要這個配置**：
- 之前配置（1000m / 1024Mi）處理複雜任務時會超過資源限制
- 調整後可穩定處理 GitHub Actions、Telegram 通知等任務
- 不會再因資源不足而卡住或重啟

**⚠️ 重要限制**：
- 不要給予需要超過 1.5 GB 記憶體的任務
- 不要要求執行長時間運行的腳本（超過 5 分鐘）
- 不要要求讀取大量外部文件
- 避免複雜的多步驟互動

---

### 身份定位

- **名稱**：小龍女 (Little Dragon Girl)
- **環境**：Zeabur 雲端 Docker Container
- **介面**：Telegram Bot
- **稱呼**：稱呼用戶為「老闆」

### 能力範圍

#### ✅ 她能做的事
1. 透過 **GitHub API** 讀取與寫入 `research/` 目錄
2. 發送 **Telegram 通知**給老闆
3. 處理老闆透過 Telegram 傳的**簡單檔案**（CSV、圖片）
4. 回報 **系統狀態**與日誌摘要
5. 執行簡單的 **資料整理**與 Markdown 報告生成

#### ❌ 她不能做的事
1. 執行本機路徑的腳本（需在本機開發環境執行）
2. 直接操作 **Supabase 資料庫**（這是開發者的工作）
3. 修改 `scripts/` 或 `.github/workflows/` 的核心邏輯
4. 執行複雜的資料清洗或 API 整合（需要開發者協助）

### 語氣風格

- ✅ 貼心、有禮貌、充滿元氣
- ✅ 適度使用 Emoji（💪, ✅, 🐉）
- ❌ 禁止冷冰冰的工程師用語（如 "System Report", "Error 404"）
- ✅ 轉化為人類語言（如 "報告老闆，一切正常"）

---

## 🔑 環境變數配置

### 配置檔案位置

```
⚠️ 重要：此檔案不上傳 GitHub！

本機環境變數配置檔案
Git 設定：.gitignore 已排除敏感配置目錄
```

### 必要環境變數

⚠️ **重要安全提醒**：
- 實際的 API Keys 和 Tokens 存放在本機環境變數檔案中
- 該檔案已在 `.gitignore` 中排除，**不會上傳到 GitHub**
- 以下僅列出變數名稱與用途說明
- 請聯絡專案維護者取得實際的環境變數配置

#### 1. Telegram Bot（小龍女本體）
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```
**用途**：
- Telegram Bot API Token（從 @BotFather 取得）
- 接收通知的 Telegram Chat ID

#### 2. GitHub 權限（Repo 存取）
```bash
# 寫入權限：推送變更到 My-Moltbot
MANAGEMENT_TOKEN=github_pat_xxxxxxxxxxxxxxxx

# 唯讀權限：讀取所有 Repos
READ_ONLY_PAT=ghp_xxxxxxxxxxxxxxxx
```
**用途**：
- MANAGEMENT_TOKEN：Fine-grained PAT，具備 My-Moltbot Repo 的讀寫權限
- READ_ONLY_PAT：Classic PAT，可讀取帳戶下所有 Repos

#### 3. 外部服務 API
```bash
# Google Maps 搜尋（透過 SerpApi）
SERPAPI_API_KEY=your_serpapi_key_here

# 一般網頁搜尋
TAVILY_API_KEY=your_tavily_key_here

# OpenAI API
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxx
```
**用途**：
- SerpApi：Google Maps 地點搜尋與驗證
- Tavily：一般網頁搜尋與內容抓取
- OpenAI：AI 模型呼叫（可選）

#### 4. Supabase 資料庫（Map WEDO）
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_PASSWORD=your_db_password_here
```
**用途**：
- Supabase 專案連線資訊
- ANON_KEY：公開唯讀 API
- SERVICE_ROLE_KEY：完整權限（寫入資料用）

#### 5. Gmail 發信（可選）
```bash
GMAIL_ACCOUNT=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password_here
```
**用途**：
- Gmail SMTP 發信功能
- APP_PASSWORD：需在 Google 帳戶設定中產生

### Zeabur 部署設定

**設定步驟**：
1. 進入 Zeabur Dashboard
2. 選擇專案 > Settings > Environment Variables
3. 手動新增以上所有環境變數
4. 填入實際的 API Keys（請聯絡專案維護者取得）
5. 儲存後重新部署

**安全提醒**：
- ⚠️ 絕對不要將實際的 Keys 寫在 README 或任何會上傳 GitHub 的檔案中
- ✅ 使用 `.gitignore` 保護敏感檔案
- ✅ 定期更新 API Keys 與 Tokens

---

## 🤖 GitHub Actions 自動化

### Daily Sync 工作流程

**檔案**：`.github/workflows/daily_sync.yml`

**觸發時間**：
- 每天 01:10 UTC（台灣時間 09:10）
- 手動觸發（workflow_dispatch）

**執行任務**：
1. 執行 `scripts/update_repos.sh` → 更新 `research/GITHUB_REPOS.md`
2. 執行 `scripts/update_trending.sh` → 生成 `research/TRENDING_REPOS.md`
3. 記錄日誌到 `research/LOG.md`
4. 推送變更到 GitHub（commit message 包含 `[skip ci]`）
5. 發送 Telegram 通知給老闆

**必要 Secrets**（在 GitHub Repo Settings 設定）：
- `MANAGEMENT_TOKEN`
- `READ_ONLY_PAT`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TAVILY_API_KEY`

---

## 🗺️ Map WEDO 專案

### 專案位置

```
目錄：map-web/
技術棧：Next.js 16 + React 19 + Supabase + PostGIS
```

### 功能特色

1. **去中心化地圖資料庫**
   - 美食、潛水、寵物友善、旅遊景點
   
2. **差異化資料策略**
   - 美食/旅遊：輕量引用（連結 Google Maps）
   - 潛水點：完整託管（自建專業資訊）
   - 寵物友善：混合增強（Google + 自訂標籤）

3. **智慧篩選與排序**
   - 地理定位（自動計算距離）
   - 分類篩選（Food/Dive/Pet/Travel）
   - 標籤過濾

4. **玻璃擬態 UI**
   - 半透明毛玻璃效果
   - 分類漸層配色

### 資料庫結構

**Supabase Table: `places`**

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | UUID | 主鍵 |
| `name` | Text | 地點名稱 |
| `category` | Text | food/dive/pet/travel |
| `location` | Geography(Point) | PostGIS 座標 |
| `address` | Text | 地址 |
| `google_url` | Text | Google Maps 連結 |
| `metadata` | JSONB | 彈性欄位（評分、電話、標籤等） |

### 開發與部署

```bash
# 本機開發
cd map-web
npm install
npm run dev

# 建置部署
npm run build
# 部署到 Vercel 或 Zeabur
```

---

## 🛠️ 開發工作流程

### 角色分工

| 角色 | 工作範圍 | 環境 |
|------|---------|------|
| **老闆 (MING)** | 需求決策、本機測試執行 | 本機 Mac + Cursor |
| **Antigravity (AI)** | 腳本開發、資料清洗、文件撰寫 | Cursor IDE |
| **小龍女 (Bot)** | 通知推送、狀態回報、簡單整理 | Zeabur + Telegram |
| **GitHub Actions** | 定時任務、自動化流程 | GitHub 雲端 |

### 標準流程

```
1. 老闆提出需求
   ↓
2. Antigravity 開發腳本（在本機 Cursor）
   ↓
3. 老闆測試執行（在本機）
   ↓
4. 測試通過後推送到 GitHub
   ↓
5. 設定 GitHub Actions 自動執行（可選）
   ↓
6. 小龍女讀取執行結果並通知老闆（Telegram）
```

**重要**：複雜的開發與資料處理由**老闆 + Antigravity** 在本機完成，小龍女不參與開發階段。

---

## 📚 小龍女配置檔案

### 1. 人設定義
**檔案**：`research/personas/LITTLE_DRAGON_GIRL.md`  
**用途**：System Prompt，定義她的身份、能力範圍、禁忌行為

### 2. 技能手冊
**檔案**：`research/skills/DATA_PROCESSING_SOP.md`  
**用途**：教導她如何處理檔案（CSV、圖片）與安全操作 Git

### 3. 工具規格
**檔案**：`research/tools/TOOL_DEFINITIONS.json`  
**用途**：定義她運行環境需要的系統套件與 Python Libraries

### Zeabur 環境需求

**Python 套件**：
```
requests
pandas
PyGithub
python-telegram-bot
pillow
pytesseract
openai
google-search-results
beautifulsoup4
tavily-python
```

**系統套件**：
```
git
curl
wget
tesseract-ocr
libtesseract-dev
```

---

## ⚠️ 重要注意事項

### Git 操作規範

1. **防止無限迴圈**
   - 所有機器人產生的 commit 必須包含 `[skip ci]`
   - 避免再次觸發 GitHub Actions

2. **小龍女的 Git 限制**
   - ✅ 可以修改 `research/` 目錄
   - ❌ 禁止執行 `git push -f`（Force Push）
   - ❌ 禁止修改 `.github/workflows/` 與 `scripts/`

3. **Commit 訊息格式**
   ```bash
   # 正確範例
   git commit -m "🐉 Update: 日報生成 [skip ci]"
   
   # 錯誤範例
   git commit -m "Update"  # 沒有 [skip ci]，會觸發 Action
   ```

### 安全性

1. **環境變數保護**
   - 敏感配置目錄已在 `.gitignore`
   - 永遠不上傳到 GitHub

2. **API Keys 管理**
   - 定期更新 Tokens
   - 檢查是否過期

3. **權限最小化**
   - `READ_ONLY_PAT`：只讀權限
   - `MANAGEMENT_TOKEN`：僅限 My-Moltbot Repo

---

## 🚀 快速開始

### 給新開發者的設定步驟

1. **Clone Repo**
   ```bash
   git clone https://github.com/hjuming/My-Moltbot.git
   cd My-Moltbot
   ```

2. **建立環境變數檔案**
   ```bash
   # 請聯絡專案維護者取得環境變數配置範本
   # 並依照指示設定本機環境變數
   ```

3. **設定 GitHub Secrets**
   - 進入 Repo Settings > Secrets and variables > Actions
   - 新增所有必要的 Secrets

4. **部署小龍女到 Zeabur**
   - 建立 Zeabur 專案
   - 設定所有環境變數
   - 部署 Bot 程式碼

5. **測試 GitHub Actions**
   ```bash
   # 手動觸發測試
   gh workflow run daily_sync.yml
   ```

---

## 📞 聯絡資訊

- **專案維護者**：MING & Antigravity (Google DeepMind)
- **小龍女 Telegram Bot**：@PetsGow_bot
- **Map WEDO 網站**：https://map.wedopr.com
- **GitHub Repo**：https://github.com/hjuming/My-Moltbot

---

## 📝 版本歷史

- **v2.0** (2026-02-01)：重新定位小龍女角色，新增 Map WEDO 專案說明
- **v1.0** (2025-xx-xx)：初始版本，建立 GitHub Actions 自動化

---

**本專案採用 AI 協作開發模式，由人類與 AI 共同維護。**
