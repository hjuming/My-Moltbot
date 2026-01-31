# 🛠️ 小龍女技能手冊：資料處理標準作業程序 (SOP)

本文件定義小龍女在 Zeabur 環境中處理特定任務的標準流程，以避免發生災難性錯誤。

## 📦 任務一：處理 User 上傳的資料 (CSV/圖片/Zip)

當老闆透過 Telegram 傳送資料並要求整理時，請嚴格遵守以下步驟：

### 1. 環境準備 (Sandbox Setup)
- **切換工作區**：所有並非 `My-Moltbot` 原生內容的檔案，一律先下載到 `/tmp/work_area_<timestamp>`。
- **檢查工具**：確認環境中是否有處理該檔案類型的工具 (如 `pandas` 處理 CSV, `tesseract` 處理 OCR)。若無，立即回報老闆：「缺少必要工具」。

### 2. 資料處理 (Processing)
- **讀取與驗證**：
  - CSV: 檢查 Header 是否符合預期。
  - Image: 確認圖片可開啟。
- **執行邏輯**：
  - 依照老闆指令進行歸納、摘要或轉轉。
  - **重要**：如果需要合併資料，請先讀取現有的 `research/TARGET_FILE.md`，將新內容 Append (附加) 到後面，而不是直接 Overwrite (覆蓋)。

### 3. 輸出結果 (Commit Strategy)
- **目標路徑**：結果一律存放在 `research/<專案名>/` 或 `research/` 下。
- **Git 操作規範**：
  ```bash
  # 1. 先同步，避免衝突
  git pull origin main --rebase
  
  # 2. 移動處理好的檔案到目標區
  mv /tmp/work_area/result_file.md research/result_file.md
  
  # 3. 精準添加 (禁止 git add .)
  git add research/result_file.md
  
  # 4. 提交與推送
  git commit -m "🐉 Update: [任務名稱] by Little Dragon Girl"
  git push origin main
  ```

---

## 🕵️‍♀️ 任務二：跨專案分析 (Repo Intelligence)

當老闆要求：「去把 `wedo-website` 的最新文章列表抓出來」時：

### 1. 獲取來源 (Fetch Source)
- **不要** 在 `My-Moltbot` 裡面 `git submodule add`。
- **正確做法**：
  - 使用 GitHub API 讀取檔案內容 (推薦)。
  - 或者 `git clone https://<token>@github.com/hjuming/wedo-website.git /tmp/wedo-repo`。

### 2. 分析 (Analyze)
- 在 `/tmp/wedo-repo` 中執行 grep, find 或 python script 進行分析。
- 生成分析報告 (Markdown 格式)。

### 3. 保存報告 (Save Report)
- 將報告存為 `research/reports/WEDO_UPDATE_<DATE>.md`。
- 刪除 `/tmp/wedo-repo`。
- `git add research/reports/...` -> `git push`。

---

## 🚨 緊急應變 (Emergency Protocol)

如果執行過程中發生 Error (如 Merge Conflict, API Timeout)：
1.  **停止操作**：不要嘗試強行 Push。
2.  **還原現場**：`git reset --hard origin/main` (確保你的環境乾淨)。
3.  **求救**：向老闆回報錯誤訊息，等待指示。
