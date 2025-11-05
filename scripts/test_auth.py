#!/usr/bin/env python3
"""
Test Authentication and API Access
"""

import requests
import json

# Test login
def test_login():
    """Test user login"""
    login_data = {
        "email": "admin@polmed.org", 
        "password": "Admin123!"
    }
    
    try:
        print("🔐 Testing login...")
        response = requests.post(
            "http://localhost:5000/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('token'):
                print("✅ LOGIN SUCCESS!")
                print(f"Token: {data['token'][:50]}...")
                return data['token']
            else:
                print("❌ Login failed - no token returned")
                return None
        else:
            print("❌ Login failed")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_protected_endpoint(token):
    """Test access to protected endpoint with token"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("\n📡 Testing protected routes endpoint...")
        response = requests.get(
            "http://localhost:5000/api/routes",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Routes endpoint working with token!")
            return True
        else:
            print("❌ Routes endpoint failed")
            return False
            
    except Exception as e:
        print(f"❌ Routes test error: {e}")
        return False

if __name__ == "__main__":
    print("=== AUTHENTICATION TEST ===")
    
    # Test login
    token = test_login()
    
    if token:
        # Test protected endpoint
        test_protected_endpoint(token)
        
        # Save token for frontend testing
        with open("test_token.txt", "w") as f:
            f.write(token)
        print(f"\n💾 Token saved to test_token.txt")
    else:
        print("\n❌ Cannot test endpoints without valid token")