import requests
import time
import json
import random

BASE_URL = "http://127.0.0.1:8000"

def generate_bulk_requirements(count=1000):
    prefixes = ["The system must", "Users should be able to", "Ensure that", "The platform requires"]
    actions = ["process", "display", "calculate", "detect", "secure", "validate", "synchronize"]
    objects = ["data packets", "user credentials", "payment transactions", "system logs", "API requests", "metadata"]
    conditions = ["with < 50ms latency", "using 256-bit encryption", "every 5 minutes", "when the load exceeds 80%"]
    
    requirements = []
    for _ in range(count):
        req = f"{random.choice(prefixes)} {random.choice(actions)} {random.choice(objects)} {random.choice(conditions)}."
        requirements.append(req)
    return requirements

def get_auth_token():
    username = "stress_test_user"
    password = "stress_test_password"
    
    # Try login first
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except:
        pass
        
    # Register if login fails (likely user doesn't exist)
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
        if resp.status_code == 200 or resp.status_code == 201:
            return resp.json()["access_token"]
        elif resp.status_code == 409: # Conflict - user already exists but login failed? 
            # This shouldn't happen with correct password, but let's be safe
            print("Warning: User exists but login failed. Manual check required.")
    except Exception as e:
        print(f"Auth error: {e}")
    
    return None

def run_stress_test(num_requirements=1000):
    print(f"Starting Stress Test with {num_requirements} requirements...")
    
    token = get_auth_token()
    if not token:
        print("Error: Could not obtain authentication token. Stress test aborted.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Start Analysis (Mocking a meeting session)
    print("Step 1: Initiating bulk upload...")
    meeting_id = "stress-test-session"
    requirements = generate_bulk_requirements(num_requirements)
    
    try:
        response = requests.post(
            f"{BASE_URL}/meetings/{meeting_id}/bulk",
            json={"requirements": requirements},
            headers=headers
        )
        if response.status_code == 405:
            print("Method Not Allowed. Check URL and API prefix.")
            return
            
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"Job Created: {job_id}")
        
        # 2. Poll Status
        start_time = time.time()
        while True:
            status_resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
            status_resp.raise_for_status()
            status_data = status_resp.json()
            
            progress = status_data.get("progress", 0)
            status = status_data.get("status", "UNKNOWN")
            
            elapsed = time.time() - start_time
            print(f"[{elapsed:.1f}s] Status: {status} | Progress: {progress}%", end="\r")
            
            if status == "COMPLETED":
                print(f"\nCOMPLETED in {elapsed:.1f} seconds!")
                print(f"Result: {len(status_data.get('result', []))} items processed.")
                break
            elif status == "FAILED":
                print(f"\nJOB FAILED: {status_data.get('error')}")
                break
            
            time.sleep(1) # Poll every second
            
    except Exception as e:
        print(f"\nError during stress test: {e}")

if __name__ == "__main__":
    # Check if server is running
    try:
        requests.get(BASE_URL + "/health", timeout=1)
    except:
        print(f"Error: FastAPI server not found at {BASE_URL}. Start it with 'uvicorn app.main:app --reload' first.")
    else:
        run_stress_test(50) # Small sample for verification

