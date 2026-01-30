#!/bin/bash
set -e
echo "正在獲取倉庫清單..."
mkdir -p research

# 獲取 JSON 並存入檔案
curl -s -H "Authorization: token ${READ_ONLY_PAT}" \
     "https://api.github.com/user/repos?per_page=100" > research/raw_repos.json

if [ ! -s research/raw_repos.json ] || grep -q "\"message\"" research/raw_repos.json; then
    echo "❌ 獲取失敗，請檢查 Token 權限"
    exit 1
fi

# Python 讀取檔案處理資料
python3 - <<'PY'
import json, os
try:
    with open('research/raw_repos.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        with open('research/GITHUB_REPOS.md', 'w', encoding='utf-8') as f:
            f.write("| 專案名稱 | GitHub 連結 |\n| :--- | :--- |\n")
            for repo in data:
                name = repo.get('name', 'N/A')
                url = repo.get('html_url', '#')
                f.write(f"| {name} | [{url}]({url}) |\n")
        print("✅ 檔案寫入完成")
finally:
    if os.path.exists('research/raw_repos.json'):
        os.remove('research/raw_repos.json')
PY
