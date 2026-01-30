#!/bin/bash
set -e

echo "正在使用 READ_ONLY_PAT 獲取倉庫清單..."

# 使用你新設定的環境變數 READ_ONLY_PAT
REPOS_JSON=$(curl -s -H "Authorization: token ${READ_ONLY_PAT}" "https://api.github.com/user/repos?per_page=100")

if echo "$REPOS_JSON" | grep -q "\"message\""; then
    echo "❌ API 授權失敗，請檢查 READ_ONLY_PAT："
    echo "$REPOS_JSON"
    exit 1
fi

mkdir -p research
echo "| 專案名稱 | GitHub 連結 |" > research/GITHUB_REPOS.md
echo "| :--- | :--- |" >> research/GITHUB_REPOS.md

echo "$REPOS_JSON" | python3 - <<'PY'
import sys, json
data = json.load(sys.stdin)
for repo in data:
    name = repo.get('name', 'N/A')
    url = repo.get('html_url', '#')
    print(f"| {name} | [{url}]({url}) |")
PY

echo "✅ 倉庫清單更新完成！"
