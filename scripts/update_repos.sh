#!/bin/bash
set -e
echo "正在獲取倉庫清單..."
mkdir -p research
curl -s -H "Authorization: token ${READ_ONLY_PAT}" \
     "https://api.github.com/user/repos?per_page=100" > research/raw_repos.json

if [ ! -s research/raw_repos.json ] || grep -q "\"message\"" research/raw_repos.json; then
    echo "❌ 獲取失敗"
    exit 1
fi

python3 - <<'PY'
import json, os
with open('research/raw_repos.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
if isinstance(data, list):
    with open('research/GITHUB_REPOS.md', 'w', encoding='utf-8') as f:
        f.write("| 專案名稱 | GitHub 連結 |\n| :--- | :--- |\n")
        for repo in data:
            f.write(f"| {repo.get('name')} | [{repo.get('html_url')}]({repo.get('html_url')}) |\n")
os.remove('research/raw_repos.json')
PY
echo "✅ 更新完成"
