import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test_admin_tools():
    # 1. Login as admin
    login_data = {
        "username": "admin@example.com",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        return
    
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in successfully. Token length: {len(token)}")
    
    # 2. Test clear-data
    print("Testing clear-data...")
    clear_resp = requests.post(f"{BASE_URL}/model/clear-data", headers=headers)
    print(f"clear-data status: {clear_resp.status_code}")
    print(f"clear-data response: {clear_resp.text}")
    
    # 3. Test seed-data
    print("Testing seed-data...")
    seed_resp = requests.post(f"{BASE_URL}/model/seed-data", headers=headers)
    print(f"seed-data status: {seed_resp.status_code}")
    print(f"seed-data response: {seed_resp.text}")

if __name__ == "__main__":
    test_admin_tools()
