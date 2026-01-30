#!/bin/bash
set -e

echo "正在從 GitHub 獲取倉庫清單..."

# 1. 獲取資料並存入變數
REPOS_JSON=$(curl -s -H "Authorization: token ${GITHUB_TOKEN_READ}" "https://api.github.com/user/repos?per_page=100")

# 2. 檢查回傳內容是否包含錯誤訊息 (例如 Bad credentials)
if echo "$REPOS_JSON" | grep -q "\"message\""; then
    echo "❌ GitHub API 回傳錯誤訊息："
    echo "$REPOS_JSON"
    exit 1
fi

echo "✅ 資料獲取成功，正在生成 Markdown..."

# 3. 使用更穩健的 Python 腳本產生表格
echo "| 專案名稱 | GitHub 連結 |" > research/GITHUB_REPOS.md
echo "| :--- | :--- |" >> research/GITHUB_REPOS.md

echo "$REPOS_JSON" | python3 - <<'PY'
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        for repo in data:
            name = repo.get('name', 'N/A')
            url = repo.get('html_url', '#')
            print(f"| {name} | [{url}]({url}) |")
    else:
        print(f"Error: Expected list, got {type(data)}")
        sys.exit(1)
except Exception as e:
    print(f"Python Error: {e}")
    sys.exit(1)
PY

echo "✨ 倉庫清單更新完成！"
