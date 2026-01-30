#!/bin/bash
set -e

echo "正在使用 GITHUB_TOKEN_READ 獲取倉庫清單..."

# 1. 獲取資料
REPOS_JSON=$(curl -s -H "Authorization: token ${GITHUB_TOKEN_READ}" "https://api.github.com/user/repos?per_page=100")

# 2. 檢查 API 是否成功
if echo "$REPOS_JSON" | grep -q "\"message\""; then
    echo "❌ API 授權失敗，請檢查 GITHUB_TOKEN_READ："
    echo "$REPOS_JSON"
    exit 1
fi

# 3. 生成 Markdown
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
