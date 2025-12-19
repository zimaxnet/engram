
import requests
import time
import sys

BASE_URL = "https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io"

def check_health():
    print(f"Checking Health... ({BASE_URL}/health)")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        if resp.status_code == 200:
            print("✅ Health Check Passed")
            return True
        else:
            print(f"❌ Health Check Failed: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def check_singularity():
    """
    Verifies that the 'engram_project_state' context is available/bootstrapped.
    This confirms the 'Singularity' (Self-Reflection) is working in the cloud.
    """
    print("\nVerifying 'Singularity' (Context Store)...")
    # We'll use the MCP Context Tool endpoint if exposed via HTTP, 
    # OR simpler: we can't easily hit the MCP SSE endpoint with straight HTTP without a client.
    # But checking /docs or /openapi.json might show us if routers are loaded.
    
    # Alternatively, if we exposed a direct REST endpoint for context in a previous step?
    # Checking implementation... pure MCP.
    
    # Workaround: Check /health with a detailed flag if we added one? No.
    # Let's check /status endpoint if it exists, or the basic root.
    
    # Actually, the best proxy for "Deep Health" is hitting the MCP initialization.
    # But since it's SSE, we can just Open a connection and see if it holds?
    pass

    # For now, let's just stick to Health. The user said "Screen-by-screen" which implies UI.
    # We should print the URLs for them.

if __name__ == "__main__":
    print("--- Engram Live Verification ---")
    
    # 1. Wait for Health
    max_retries = 30
    ready = False
    for i in range(max_retries):
        if check_health():
            ready = True
            break
        print(f"Waiting for container to start... ({i+1}/{max_retries})")
        time.sleep(5)
    
    if not ready:
        print("\n❌ Timed out waiting for container.")
        sys.exit(1)

    print("\n🚀 Container is UP!")
    print(f"API URL: {BASE_URL}")
    print(f"Frontend: https://engram.work")
    print(f"Recommended Verification:")
    print("1. Visit https://engram.work")
    print("2. Check if 'Episodes' load (Connectivity check)")
    print("3. Verify 'Singularity' by asking Chat: 'What is the implementation plan for Engram?'")
