# 📝 My-Moltbot：龍蝦機器人 (Moltbot) 管理與檔案核心

## 致 Antigravity/接手開發者
本專案為活在 Zeabur 環境中的「龍蝦機器人」後端資料庫與自動化中樞。它不直接運行 Bot 邏輯，而是作為儲存庫、知識庫與自動化排程器，透過 Telegram 指令與 GitHub Actions 進行連動。

## � 專案人設 (Persona)
本專案的自動化通知已人格化，維護時請務必遵守以下人設：
- **角色名稱**：小龍女 (Little Dragon Girl) 🐉
- **稱呼用戶**：老闆 (Boss)
- **語氣風格**：貼心、有禮貌、充滿元氣，會使用 Emoji (如 💪, ✅, 💤)。
- **禁忌**：禁止使用冷冰冰的工程師用語（如 "System Report", "Status Code 200"），必須轉化為人類語言（如 "報告老闆，一切正常"）。

## �🏗️ 系統架構
- **指令來源**：Telegram (用戶與 Bot 互動)。
- **執行環境**：Zeabur (運行中的 Node.js/Python 機器人環境)。
- **資料中樞**：GitHub (本倉庫 My-Moltbot)，負責存放專案清單、日誌及研究文件。
- **自動化**：GitHub Actions，負責定時監測、同步 repo 狀態及發送日報。

## 🔑 環境變數 (Secrets)
設定在 GitHub 倉庫的 `Settings > Secrets and variables > Actions` 中，必須配置以下四組變數，否則自動化流程將失效：

| 變數名稱 | 類型 | 說明 |
| :--- | :--- | :--- |
| `MANAGEMENT_TOKEN` | PAT (Fine-grained) | 具備本專案的 Read/Write 權限，用於推送自動化變更。 |
| `READ_ONLY_PAT` | PAT (Classic) | 具備 repo 權限。用於獲取帳戶下所有 (43+) 專案的清單及監測其他私有專案。 |
| `TELEGRAM_BOT_TOKEN` | Token | 龍蝦機器人的 API Token。 |
| `TELEGRAM_CHAT_ID` | ID | 接收通知與日報的指定 Telegram 頻道/用戶 ID。 |

## 🤖 自動化工作流 (GitHub Actions)

### Daily Sync and WEDO Monitor (`daily_sync.yml`)
- **觸發時間**：每天 01:10 UTC (台灣時間 09:10) 或手動觸發。
- **執行任務**：
  1. 調用 `scripts/update_repos.sh` 更新 `research/GITHUB_REPOS.md`。
  2. 檢查 `hjuming/wedo-website` 的當日提交狀態。
  3. 將結果紀錄於 `research/LOG.md` 並透過 Telegram 發送摘要回報。

## ⚠️ 重要注意事項 (Maintenance)
- **防止無限迴圈**：由於 Action 會推播變更回本倉庫，所有由機器人產生的 commit 必須包含 `[skip ci]` 關鍵字，以防止再次觸發 Action 造成循環。
- **路徑依賴**：腳本位於 `scripts/`，產出的文件位於 `research/`。修改目錄結構時，請同步更新 `.github/workflows/daily_sync.yml`。
- **權限問題**：如果出現 `401 Bad credentials`，請優先檢查 `READ_ONLY_PAT` 是否過期，或名稱是否被 GitHub 保留關鍵字（如 `GITHUB_` 前綴）阻擋。

## 📂 目錄說明
- `scripts/`：存放執行邏輯的 `.sh` 腳本。
- `research/`：存放自動化產出的 MD 文件、專案清單與歷史日誌。
- `.github/workflows/`：定義雲端排程任務。

## 🛠️ 機器人互動指令預留
- **指令**：`/report`
- **用途**：讓用戶從 Telegram 直接調閱 `research/LOG.md` 的最新狀態。
- **邏輯**：
  1. 使用 `MANAGEMENT_TOKEN` 透過 GitHub API 讀取本專案檔案。
  2. 抓取 `LOG.md` 的最後三行文字。
  3. 將文字回傳至 Telegram。
- **狀態**：目前已在 GitHub Actions 端實現主動推送，未來可由 Antigravity 實作被動查詢。

## 🔌 Zeabur 機器人核心配置 (Configuration)

為了讓小龍女 (Little Dragon Girl) 在 Zeabur 上正確運作並具備專案協作能力，請參照以下配置檔：

### 1. 🧠 大腦與人設 (Brain & Persona)
- **檔案位置**：`research/personas/LITTLE_DRAGON_GIRL.md`
- **用途**：這是她的 System Prompt。請將此檔案內容餵給 LLM，讓她知道自己是誰、該做什麼、以及**絕對不能做什麼** (如 Force Push)。

### 2. 📚 技能手冊 (Skills SOP)
- **檔案位置**：`research/skills/DATA_PROCESSING_SOP.md`
- **用途**：教導她如何處理檔案 (CSV, 圖片) 以及如何安全地操作 Git。這是為了防止她再次誤刪倉庫的重要準則。

### 3. 🧰 工具規格 (Tool Specs)
- **檔案位置**：`research/tools/TOOL_DEFINITIONS.json`
- **用途**：定義她運行環境所需的 System Packages (如 `tesseract-ocr`) 與 Python Libraries。請確保 Zeabur 的 Docker Image 包含這些依賴。

---
*專案維護者：MING & Antigravity (Google DeepMind)*
