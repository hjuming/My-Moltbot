# 🚀 下一階段：讓小龍女聽懂人話 (自然語言互動架構)

## 🎯 目標
將目前的「指令式互動」(`/report`) 升級為「自然語言對話」，讓老闆（用戶）不需要記憶任何指令，像在跟秘書聊天一樣即可。

## 🗣️ 預期場景
- **老闆**：「小龍女，今天 WEDO 有更新嗎？」
- **小龍女**：「報告老闆，正在幫您查詢... (呼叫 API) ... 查到了！今天 WEDO 沒有動靜喔。」

- **老闆**：「最近有什麼新專案？」
- **小龍女**：「稍等喔...(讀取 GITHUB_REPOS.md)... 我們最近新增了 `lottery-app` 和 `ai-agent` 兩個專案！」

## 🛠️ 技術架構升級 (Roadmap)

目前的 `My-Moltbot` 是「大腦資料庫」，但負責聽話的「該 Bot (Zeabur)」需要進行以下升級：

### 1. 接入 LLM (大語言模型)
在 Zeabur 的 Bot 程式碼中接入 OpenAI (GPT-4o-mini) 或 Anthropic (Claude 3.5 Haiku) API。
- **功能**：理解用戶意圖 (Intent Recognition)。
- **System Prompt**：植入「小龍女」人設，並給予她「查詢資料的權限」。

### 2. Tool Calling (工具調用)
賦予 AI 調用 GitHub API 的能力 (Function Calling)。
- 當 AI 判斷老闆想看報表 -> 自動觸發 `daily_sync.yml` 或直接讀取 `research/LOG.md`。
- 當 AI 判斷老闆想聊天 -> 直接以小龍女口吻閒聊。

### 3. 記憶上下文 (Context)
讓 Bot 短暫記住前幾句對話，這樣老闆說「那其他的呢？」時，她知道是在問其他專案。

## 📝 給開發者的行動清單
1. [ ] 申請 OpenAI/Anthropic API Key 並放入 Zeabur 環境變數。
2. [ ] 在 Bot 主程式增加 `chat_completion` 邏輯。
3. [ ] 設定 System Prompt：「你是小龍女，你的老闆是 MING，只能用繁體中文回答...」。
4. [ ] 實作 Function: `get_daily_report()` 對接 GitHub API。

---
*此文檔由 Antigravity 生成，作為未來升級的藍圖。*
