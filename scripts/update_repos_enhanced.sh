#!/bin/bash
set -e
echo "🔍 正在獲取倉庫清單（含描述）..."
mkdir -p research

# 獲取 JSON 並存入檔案
curl -s -H "Authorization: token ${READ_ONLY_PAT}" \
     "https://api.github.com/user/repos?per_page=100&sort=updated" > research/raw_repos.json

if [ ! -s research/raw_repos.json ] || grep -q "\"message\"" research/raw_repos.json; then
    echo "❌ 獲取失敗，請檢查 Token 權限"
    exit 1
fi

# 保存舊版本用於比對
if [ -f "research/GITHUB_REPOS.md" ]; then
    cp research/GITHUB_REPOS.md research/GITHUB_REPOS.old.md
fi

# Python 處理邏輯
python3 - <<'PY'
import json
import os
import re
from datetime import datetime, timedelta

# 讀取新資料
with open('research/raw_repos.json', 'r', encoding='utf-8') as f:
    repos = json.load(f)

# 讀取舊資料（如果存在）- 用於比對變更
old_repos = {}
if os.path.exists('research/GITHUB_REPOS.old.md'):
    with open('research/GITHUB_REPOS.old.md', 'r', encoding='utf-8') as f:
        for line in f:
            # 提取專案名稱和更新時間
            match = re.search(r'\| ([^|]+) \| ([^|]+) \| ([^|]+) \| \[', line)
            if match and match.group(1).strip() not in ['專案名稱', ':---']:
                name = match.group(1).strip()
                last_update = match.group(2).strip()
                old_repos[name] = last_update

# 建立新的專案集合和數據
new_repo_names = {repo.get('name', 'N/A') for repo in repos}
old_repo_names = set(old_repos.keys())

# 找出變更
added = new_repo_names - old_repo_names
removed = old_repo_names - new_repo_names

# 找出最近更新的專案（24小時內）
now = datetime.now()
recently_updated = []
for repo in repos:
    updated_at = repo.get('updated_at', '')
    if updated_at:
        try:
            update_time = datetime.strptime(updated_at, '%Y-%m-%dT%H:%M:%SZ')
            if (now - update_time) < timedelta(hours=24):
                recently_updated.append({
                    'name': repo.get('name'),
                    'url': repo.get('html_url'),
                    'updated_at': updated_at,
                    'time_ago': int((now - update_time).total_seconds() / 3600)  # 小時數
                })
        except:
            pass

# 按更新時間排序
recently_updated.sort(key=lambda x: x['updated_at'], reverse=True)

# 寫入主檔案
with open('research/GITHUB_REPOS.md', 'w', encoding='utf-8') as f:
    f.write("# 🗂️ GitHub 專案總覽\n\n")
    f.write(f"**更新時間**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"**專案總數**：{len(repos)}\n\n")
    f.write("---\n\n")
    f.write("| 專案名稱 | 最後更新 | 簡介 | 連結 |\n")
    f.write("| :--- | :--- | :--- | :--- |\n")
    
    for repo in sorted(repos, key=lambda x: x.get('name', '').lower()):
        name = repo.get('name', 'N/A')
        desc = repo.get('description', '無描述')
        if not desc or desc.strip() == '':
            desc = '無描述'
        url = repo.get('html_url', '#')
        
        # 格式化更新時間
        updated_at = repo.get('updated_at', '')
        if updated_at:
            try:
                update_time = datetime.strptime(updated_at, '%Y-%m-%dT%H:%M:%SZ')
                time_str = update_time.strftime('%Y-%m-%d')
            except:
                time_str = '未知'
        else:
            time_str = '未知'
        
        # 限制描述長度
        if len(desc) > 40:
            desc = desc[:37] + '...'
        f.write(f"| {name} | {time_str} | {desc} | [🔗]({url}) |\n")

# 寫入變更報告
if added or removed or recently_updated:
    with open('research/REPO_CHANGES.md', 'w', encoding='utf-8') as f:
        f.write(f"# 📋 專案變動報告\n\n")
        f.write(f"**日期**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        if added:
            f.write(f"## ✅ 新增專案（{len(added)}）\n\n")
            for name in sorted(added):
                repo = next((r for r in repos if r.get('name') == name), None)
                if repo:
                    url = repo.get('html_url', '#')
                    desc = repo.get('description', '無描述')
                    updated_at = repo.get('updated_at', '')
                    if updated_at:
                        try:
                            update_time = datetime.strptime(updated_at, '%Y-%m-%dT%H:%M:%SZ')
                            time_str = update_time.strftime('%Y-%m-%d %H:%M')
                        except:
                            time_str = '未知'
                    else:
                        time_str = '未知'
                    
                    f.write(f"- **{name}**\n")
                    f.write(f"  - 連結：{url}\n")
                    f.write(f"  - 描述：{desc}\n")
                    f.write(f"  - 建立時間：{time_str}\n\n")
        
        if removed:
            f.write(f"## ❌ 移除專案（{len(removed)}）\n\n")
            for name in sorted(removed):
                f.write(f"- {name}\n")
            f.write("\n")
        
        if recently_updated:
            f.write(f"## 🔄 最近更新的專案（24小時內，共 {len(recently_updated)} 個）\n\n")
            for item in recently_updated[:10]:  # 最多顯示10個
                name = item['name']
                url = item['url']
                hours = item['time_ago']
                if hours == 0:
                    time_text = "不到1小時前"
                elif hours == 1:
                    time_text = "1小時前"
                else:
                    time_text = f"{hours}小時前"
                f.write(f"- **{name}** - {time_text}\n")
                f.write(f"  - {url}\n\n")
    
    print(f"✅ 發現變更：新增 {len(added)} 個，移除 {len(removed)} 個，最近更新 {len(recently_updated)} 個")
else:
    # 沒有變更，刪除舊的變更報告
    if os.path.exists('research/REPO_CHANGES.md'):
        os.remove('research/REPO_CHANGES.md')
    print("✅ 無變更")

# 清理暫存檔
if os.path.exists('research/raw_repos.json'):
    os.remove('research/raw_repos.json')
if os.path.exists('research/GITHUB_REPOS.old.md'):
    os.remove('research/GITHUB_REPOS.old.md')
PY

echo "✅ 更新完成"
