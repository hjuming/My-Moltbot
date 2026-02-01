# 🐉 小龍女環境檢測任務

姑姑，這是一個簡單的測試，幫助我們了解妳的運行環境。

---

## 📋 任務目標

請回答以下問題，用**實際執行程式碼**的方式，不要猜測。

---

## 🔍 檢測項目

### 1. 運行環境識別
```python
# 執行這段 Python 程式碼並回報結果
import os
import sys
import platform

print("運行環境資訊：")
print(f"作業系統：{platform.system()}")
print(f"Python 版本：{sys.version}")
print(f"當前工作目錄：{os.getcwd()}")
print(f"Python 執行檔位置：{sys.executable}")
```

---

### 2. 環境變數檢查
```python
# 執行這段程式碼，列出可用的環境變數（只顯示名稱）
import os

important_vars = [
    "TELEGRAM_BOT_TOKEN",
    "MANAGEMENT_TOKEN", 
    "SERPAPI_API_KEY",
    "SUPABASE_URL"
]

print("\n環境變數檢查：")
for var in important_vars:
    exists = "✅" if os.getenv(var) else "❌"
    print(f"{exists} {var}")
```

---

### 3. Python 套件檢查
```python
# 執行這段程式碼，檢查重要套件是否安裝
import importlib

packages = [
    "requests",
    "github",  # PyGithub
    "telegram",  # python-telegram-bot
    "pandas"
]

print("\nPython 套件檢查：")
for pkg in packages:
    try:
        importlib.import_module(pkg)
        print(f"✅ {pkg}")
    except ImportError:
        print(f"❌ {pkg}")
```

---

## 📝 回報格式

請將上述三段程式碼的**完整輸出**貼給老闆，格式如下：

```
報告老闆，環境檢測完成！

【運行環境資訊】
[第一段程式碼的輸出]

【環境變數檢查】
[第二段程式碼的輸出]

【Python 套件檢查】
[第三段程式碼的輸出]
```

---

## ⚠️ 重要提醒

1. ✅ **請實際執行程式碼**，不要猜測或解釋
2. ✅ **貼出完整輸出**，包括所有 print 的內容
3. ❌ **不要寫執行計畫**，直接執行
4. ❌ **不要解釋結果**，只要貼輸出

---

## 💡 如果遇到錯誤

如果執行時出現錯誤，請貼出**完整錯誤訊息**：

```
報告老闆，執行時出現錯誤：

[完整錯誤訊息]
```

---

**姑姑，這個任務很簡單，就是執行三段程式碼並貼結果。不要想太多，直接做！** 💪

---

**神雕大俠**
