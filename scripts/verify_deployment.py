
import os
import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"  # Adjust if running on different port
# Or use the production URL if verifying prod: https://engram.work/api/v1

def check_health():
    print("Checking API Health...")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        if resp.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API Health failed: {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Is the server running?")
        return False

def verify_story_execution():
    print("\nVerifying Story Delegation Workflow...")
    
    # 1. Trigger Workflow
    payload = {
        "text": "Create a story about a futuristic city on Mars.",
        "user_id": "verify-script",
        "tenant_id": "default",
        "context": "Verification script"
    }
    
    # Note: Depending on how delegation is exposed, we might call the story endpoint directly
    # OR we chat with Elena. Calling story endpoint directly is more deterministic for this test.
    
    try:
        resp = requests.post(
            f"{BASE_URL}/stories/execute",
            json={
                "topic": "Futuristic Mars City",
                "include_image": True,
                "include_diagram": False
            }
        )
        
        if resp.status_code != 202:
            print(f"❌ Failed to trigger story: {resp.text}")
            return False
            
        data = resp.json()
        workflow_id = data.get("workflow_id")
        story_id = data.get("story_id")
        print(f"✅ Workflow triggered: {workflow_id}, Story ID: {story_id}")
        
        # 2. Poll for Story Completion
        # We need an endpoint to check story status. 
        # For now, we'll poll the GET /stories/{id} endpoint until it returns content
        
        print("Waiting for story generation (this may take 30-60s)...")
        max_retries = 30
        for i in range(max_retries):
            time.sleep(2)
            # Assuming GET /stories/{id} returns the story
            resp = requests.get(f"{BASE_URL}/stories/{story_id}")
            if resp.status_code == 200:
                story_data = resp.json()
                if story_data.get("story_content"):
                     print("✅ Story content generated!")
                     
                     # Check for image
                     if story_data.get("image_path"):
                         print(f"✅ Image generated at: {story_data['image_path']}")
                         
                         # Verify Image Access
                         img_resp = requests.get(f"{BASE_URL}/images/{os.path.basename(story_data['image_path'])}")
                         if img_resp.status_code == 200:
                             print("✅ Image is accessible via API")
                             return True
                         else:
                             print(f"❌ Image not accessible: {img_resp.status_code}")
                             return False
                     else:
                         print("⚠️ Story finished but no image path yet. Waiting...")
            else:
                pass
                
        print("❌ Timeout waiting for story/image generation.")
        return False
        
    except Exception as e:
        print(f"❌ Error executing story verification: {e}")
        return False

if __name__ == "__main__":
    if not check_health():
        sys.exit(1)
        
    if not verify_story_execution():
        sys.exit(1)
        
    print("\n✅ All verifications passed!")
