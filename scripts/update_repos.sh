#!/bin/bash
set -e

echo "正在使用 READ_ONLY_PAT 獲取倉庫清單..."

# 1. 確保目錄存在
mkdir -p research

# 2. 直接將 API 結果存入實體檔案，避免使用變數或管道傳輸大數據
curl -s -H "Authorization: token ${READ_ONLY_PAT}" \
     "https://api.github.com/user/repos?per_page=100" > research/raw_repos.json

# 3. 檢查檔案是否為空
if [ ! -s research/raw_repos.json ]; then
    echo "❌ 抓取失敗：API 回傳內容為空"
    exit 1
fi

# 4. 檢查是否包含錯誤訊息 (例如 Bad credentials)
if grep -q "\"message\"" research/raw_repos.json; then
    echo "❌ API 授權失敗，內容如下："
    cat research/raw_repos.json
    exit 1
fi

echo "✅ 成功獲取資料，正在產生 Markdown 表格..."

# 5. 讓 Python 直接讀取檔案內容
python3 - <<'PY'
import sys, json, os

try:
    file_path = 'research/raw_repos.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        with open('research/GITHUB_REPOS.md', 'w', encoding='utf-8') as f:
            f.write("| 專案名稱 | GitHub 連結 |\n")
            f.write("| :--- | :--- |\n")
            for repo in data:
                name = repo.get('name', 'N/A')
                url = repo.get('html_url', '#')
                f.write(f"| {name} | [{url}]({url}) |\n")
        print("✨ 專案表格已成功更新！")
    else:
        print("Error: API 回傳格式非列表")
        sys.exit(1)
finally:
    # 任務完成後刪除暫存的 JSON 檔
    if os.path.exists(file_path):
        os.remove(file_path)
PY

echo "🚀 腳本執行完畢！"
