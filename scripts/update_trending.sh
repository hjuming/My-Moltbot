#!/bin/bash
set -e

# 檢查 TAVILY_API_KEY 是否存在
if [ -z "$TAVILY_API_KEY" ]; then
    echo "⚠️  未偵測到 TAVILY_API_KEY，跳過熱門專案抓取。"
    echo "| 日期 | 狀態 | 備註 |" > research/TRENDING_REPOS.md
    echo "| :--- | :--- | :--- |" >> research/TRENDING_REPOS.md
    echo "| $(date +%Y-%m-%d) | Skipped | Missing API Key |" >> research/TRENDING_REPOS.md
    exit 0
fi

echo "正在調用 Tavily 搜尋 RepoInside 最新推薦..."

# 使用 Python 調用 Tavily API
python3 - <<'PY'
import os
import json
import urllib.request
import urllib.error

tavily_api_key = os.environ.get('TAVILY_API_KEY')
if not tavily_api_key:
    exit(0)

# 1. 搜尋 RepoInside
url = "https://api.tavily.com/search"
payload = {
    "api_key": tavily_api_key,
    "query": "site:repoinside.com latest github projects recommendation this week",
    "search_depth": "basic",
    "include_answer": True,
    "max_results": 5
}

try:
    req = urllib.request.Request(url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers={'Content-Type': 'application/json'})
    
    with urllib.request.urlopen(req) as response:
        result = json.load(response)
        
    # 2. 生成 Markdown
    markdown_content = "# 🔥 本週熱門 Github 專案 (via RepoInside)\n\n"
    markdown_content += f"更新時間：{os.environ.get('TODAY', 'N/A')}\n\n"
    markdown_content += "| 專案 | 說明 | 連結 |\n| :--- | :--- | :--- |\n"
    
    found_projects = False
    if 'results' in result:
        for item in result['results']:
            title = item.get('title', 'Unknown Project').replace('|', '-')
            url = item.get('url', '#')
            snippet = item.get('content', '').replace('\n', ' ').replace('|', '-')[:100] + '...'
            markdown_content += f"| {title} | {snippet} | [Link]({url}) |\n"
            found_projects = True

    if not found_projects:
        markdown_content += "| 無 | 本次搜尋未發現特定推薦 | - |\n"

    # 3. 寫入檔案
    os.makedirs('research', exist_ok=True)
    with open('research/TRENDING_REPOS.md', 'w', encoding='utf-8') as f:
        f.write(markdown_content)
        
    print("✅ research/TRENDING_REPOS.md 更新完成")

except Exception as e:
    print(f"❌ Tavily 搜尋失敗: {e}")
PY
