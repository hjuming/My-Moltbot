import os
import requests
import json

def check_env_vars():
    required_vars = [
        "TAVILY_API_KEY", 
        "SERPAPI_API_KEY", 
        "GMAIL_ACCOUNT", 
        "GMAIL_APP_PASSWORD",
        "READ_ONLY_PAT", 
        "MANAGEMENT_TOKEN"
    ]
    
    print("📋 Environment Variable Check:")
    all_present = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask the key for security log
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
            print(f"  ✅ {var}: Detected ({masked})")
        else:
            print(f"  ❌ {var}: MISSING")
            all_present = False
    return all_present

def test_tavily():
    print("\n🔎 Testing Tavily Search API...")
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("  ⏩ Skipped (No Key)")
        return
        
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": "hello world", "max_results": 1},
            timeout=10
        )
        if resp.status_code == 200:
            print("  ✅ Tavily: OK")
        else:
            print(f"  ❌ Tavily: Failed ({resp.status_code}) - {resp.text}")
    except Exception as e:
        print(f"  ❌ Tavily: Error ({e})")

def test_serpapi():
    print("\n🗺️ Testing SerpApi (Google Maps)...")
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key:
        print("  ⏩ Skipped (No Key)")
        return

    try:
        # Simple query for coffee in Taipei
        params = {
            "engine": "google_maps",
            "q": "Starbucks",
            "ll": "@25.0330,121.5654,15.1z",
            "type": "search",
            "api_key": api_key
        }
        resp = requests.get("https://serpapi.com/search", params=params, timeout=10)
        if resp.status_code == 200:
            print("  ✅ SerpApi: OK")
        else:
            print(f"  ❌ SerpApi: Failed ({resp.status_code}) - {resp.text}")
    except Exception as e:
        print(f"  ❌ SerpApi: Error ({e})")

def test_github_pat():
    print("\n🐙 Testing READ_ONLY_PAT (GitHub API)...")
    token = os.environ.get("READ_ONLY_PAT")
    if not token:
        print("  ⏩ Skipped (No Token)")
        return

    try:
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        # Try to fetch user profile
        resp = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        
        if resp.status_code == 200:
            user_data = resp.json()
            print(f"  ✅ GitHub Auth: OK (Logged in as: {user_data.get('login')})")
            
            # Additional check: Repo Access
            print("  ...Checking Repo List Access...")
            repo_resp = requests.get("https://api.github.com/user/repos?per_page=1", headers=headers, timeout=10)
            if repo_resp.status_code == 200:
                print("  ✅ GitHub Repos: OK (Can read repo list)")
            else:
                print(f"  ⚠️ GitHub Repos: Failed ({repo_resp.status_code}) - Might confirm Scopes?")
        else:
            print(f"  ❌ GitHub Auth: Failed ({resp.status_code}) - {resp.text}")
            print("  💡 Hint: Check if token is expired or requires SSO authorization.")

    except Exception as e:
        print(f"  ❌ GitHub: Error ({e})")

if __name__ == "__main__":
    print("🐉 Little Dragon Girl - System Diagnosis Tool v1.0")
    print("==================================================")
    if check_env_vars():
        print("\n🚀 All keys present. Proceeding with connectivity tests...")
        test_tavily()
        test_serpapi()
        test_github_pat()
    else:
        print("\n⚠️  Some keys are missing. Please check Zeabur Dashboard.")
    print("\n==================================================")
    print("Diagnosis Complete.")
