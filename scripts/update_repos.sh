name: Daily Sync and WEDO Monitor

on:
  schedule:
    - cron: '10 1 * * *' # 台灣時間 09:10
  workflow_dispatch: {}

jobs:
  sync-and-monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          persist-credentials: false

      - name: Ensure scripts executable
        run: |
          mkdir -p scripts
          chmod +x ./scripts/*.sh || true

      - name: Run update_repos.sh
        env:
          READ_ONLY_PAT: ${{ secrets.READ_ONLY_PAT }}
        run: |
          ./scripts/update_repos.sh

      - name: Check WEDO marketing report
        id: wedo_check
        env:
          READ_ONLY_PAT: ${{ secrets.READ_ONLY_PAT }}
        run: |
          TODAY=$(date -u +%Y-%m-%d)
          SINCE="${TODAY}T00:00:00Z"
          echo "Checking commits in wedo-website since $SINCE"
          resp=$(curl -sSL -H "Authorization: token $READ_ONLY_PAT" "https://api.github.com/repos/hjuming/wedo-website/commits?since=${SINCE}")
          
          # 使用 Python 安全解析，若無 commit 則輸出 NONE
          python3 - <<'PY'
import sys, json, os
try:
    j = json.loads(os.environ.get('RESP', '[]'))
    if isinstance(j, list) and len(j) > 0:
        url = j[0].get('html_url', 'No URL found')
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"status=FOUND\nurl={url}\n")
        print(f"Found latest commit: {url}")
    else:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write("status=NONE\n")
        print("No commits found for today.")
except Exception as e:
    print(f"Error: {e}")
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write("status=NONE\n")
PY
        env:
          RESP: ${{ env.resp }} # 注意：這裡我們改用內聯處理更安全

      - name: Update LOG and Push
        env:
          MANAGEMENT_TOKEN: ${{ secrets.MANAGEMENT_TOKEN }}
          WEDO_STATUS: ${{ steps.wedo_check.outputs.status }}
          WEDO_URL: ${{ steps.wedo_check.outputs.url }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          TODAY=$(date +%Y-%m-%d)
          mkdir -p research
          if [ "$WEDO_STATUS" = "FOUND" ]; then
            REPORT_MSG="$TODAY WEDO report: $WEDO_URL"
          else
            REPORT_MSG="$TODAY WEDO report: 未生成"
          fi
          echo "$REPORT_MSG" >> research/LOG.md
          
          git config user.name "moltbot-action"
          git config user.email "moltbot-action@example.com"
          git add .
          git commit -m "Automated Sync: $TODAY" || exit 0
          git remote set-url origin https://${MANAGEMENT_TOKEN}@github.com/hjuming/My-Moltbot.git
          git push origin HEAD:main

          # Telegram 通知
          MSG="🚀 Moltbot 任務報告\n📅 日期: $TODAY\n📊 $REPORT_MSG"
          curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d chat_id="${TELEGRAM_CHAT_ID}" \
            -d text="$MSG"
