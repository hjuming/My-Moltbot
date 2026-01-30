#!/bin/bash
set -e

echo "正在更新 GitHub 倉庫清單..."

# 使用 GITHUB_TOKEN_READ 獲取所有倉庫
REPOS_JSON=$(curl -s -H "Authorization: token ${GITHUB_TOKEN_READ}" "https://api.github.com/user/repos?per_page=100")

# 建立 Markdown 表格
echo "| 專案名稱 | GitHub 連結 |" > research/GITHUB_REPOS.md
echo "| :--- | :--- |" >> research/GITHUB_REPOS.md
echo "$REPOS_JSON" | python3 -c "import sys,json; j=json.load(sys.stdin); [print(f'| {x[\"name\"]} | [{x[\"html_url\"]}]({x[\"html_url\"]}) |') for x in j]" >> research/GITHUB_REPOS.md

echo "更新完成！"
