#!/bin/bash
set -e

echo "正在使用 READ_ONLY_PAT 獲取倉庫清單..."

# 1. 將結果存入暫存檔，避免 Pipe 傳輸問題
REPOS_JSON=$(curl -s -H "Authorization: token ${READ_ONLY_PAT}" "https://api.github.com/user/repos?per_page=100")

# 2. 檢查回傳是否為空或包含錯誤
if [ -z "$REPOS_JSON" ] || echo "$REPOS_JSON" | grep -q "\"message\""; then
    echo "❌ API 獲取失敗。回傳內容為："
    echo "${REPOS_JSON:-空值}"
    exit 1
fi

echo "✅ 成功獲取資料，正在產生 Markdown 表格..."

# 3. 確保 research 目錄存在
mkdir -p research

# 4. 使用安全的 Python 腳本解析
echo "$REPOS_JSON" | python3 - <<'PY'
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        with open('research/GITHUB_REPOS.md', 'w') as f:
            f.write("| 專案名稱 | GitHub 連結 |\n")
            f.write("| :--- | :--- |\n")
            for repo in data:
                name = repo.get('name', 'N/A')
                url = repo.get('html_url', '#')
                f.write(f"| {name} | [{url}]({url}) |\n")
        print("✨ 檔案寫入成功")
    else:
        print("Error: API didn't return a list")
        sys.exit(1)
except Exception as e:
    print(f"Error parsing JSON: {e}")
    sys.exit(1)
PY

echo "🚀 腳本執行完畢！"
