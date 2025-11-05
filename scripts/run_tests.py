#!/usr/bin/env python3
"""
POLMED Backend - API Endpoint Tests
Comprehensive test suite for all backend endpoints
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Configuration
BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5000/api')
TEST_USER_EMAIL = 'test@polmed.co.za'
TEST_USER_PASSWORD = 'Test@12345'

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    END = '\033[0m'

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
    
    def log(self, message: str, status: str = 'info'):
        """Log test message"""
        if status == 'pass':
            print(f"{Colors.GREEN}✓{Colors.END} {message}")
        elif status == 'fail':
            print(f"{Colors.RED}✗{Colors.END} {message}")
        elif status == 'warn':
            print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
        else:
            print(f"• {message}")
    
    def test_health_check(self):
        """Test health check endpoint"""
        self.log("\n=== Testing Health Check ===")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log(f"Health check passed - Status: {data.get('status')}", "pass")
                    return True
                else:
                    self.log(f"Health check failed - {data.get('error')}", "fail")
                    return False
            else:
                self.log(f"Health check returned {response.status_code}", "fail")
                return False
        
        except Exception as e:
            self.log(f"Health check error: {e}", "fail")
            return False
    
    def test_authentication(self):
        """Test authentication endpoints"""
        self.log("\n=== Testing Authentication ===")
        
        try:
            # Test login
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.token = data.get('data', {}).get('token')
                    self.log(f"Login successful - Token obtained", "pass")
                    
                    # Test get current user
                    headers = {"Authorization": f"Bearer {self.token}"}
                    response = requests.get(
                        f"{self.base_url}/auth/me",
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        self.log(f"Current user retrieved successfully", "pass")
                        return True
                    else:
                        self.log(f"Failed to get current user", "fail")
                        return False
                else:
                    self.log(f"Login failed - {data.get('error')}", "fail")
                    return False
            else:
                self.log(f"Login returned {response.status_code}", "fail")
                return False
        
        except Exception as e:
            self.log(f"Authentication error: {e}", "fail")
            return False
    
    def test_patient_endpoints(self):
        """Test patient management endpoints"""
        self.log("\n=== Testing Patient Endpoints ===")
        
        if not self.token:
            self.log("No valid token - skipping patient tests", "warn")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            # Test get patients
            response = requests.get(
                f"{self.base_url}/patients?page=1&per_page=10",
                headers=headers
            )
            
            if response.status_code == 200:
                self.log("Get patients endpoint working", "pass")
            else:
                self.log(f"Get patients returned {response.status_code}", "fail")
            
            # Test create patient
            patient_data = {
                "first_name": "Test",
                "last_name": "Patient",
                "date_of_birth": "1990-05-15",
                "gender": "Male",
                "phone_number": "+27123456789",
                "medical_aid_number": "TEST123456",
                "is_palmed_member": True
            }
            
            response = requests.post(
                f"{self.base_url}/patients",
                json=patient_data,
                headers=headers
            )
            
            if response.status_code == 201:
                self.log("Create patient endpoint working", "pass")
                return True
            else:
                self.log(f"Create patient returned {response.status_code}", "fail")
                return False
        
        except Exception as e:
            self.log(f"Patient endpoint error: {e}", "fail")
            return False
    
    def test_dashboard(self):
        """Test dashboard endpoints"""
        self.log("\n=== Testing Dashboard Endpoints ===")
        
        if not self.token:
            self.log("No valid token - skipping dashboard tests", "warn")
            return False
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{self.base_url}/dashboard/stats",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log("Dashboard stats endpoint working", "pass")
                    return True
                else:
                    self.log(f"Dashboard stats failed - {data.get('error')}", "fail")
                    return False
            else:
                self.log(f"Dashboard stats returned {response.status_code}", "fail")
                return False
        
        except Exception as e:
            self.log(f"Dashboard error: {e}", "fail")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{Colors.YELLOW}╔═══════════════════════════════════════════╗")
        print(f"║     POLMED Backend API Test Suite v2.0   ║")
        print(f"╚═══════════════════════════════════════════╝{Colors.END}\n")
        
        print(f"Testing against: {self.base_url}\n")
        
        results = {
            "Health Check": self.test_health_check(),
            "Authentication": self.test_authentication(),
            "Patient Endpoints": self.test_patient_endpoints(),
            "Dashboard": self.test_dashboard(),
        }
        
        # Summary
        self.log("\n=== Test Summary ===")
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "pass" if result else "fail"
            self.log(f"{test_name}: {'PASSED' if result else 'FAILED'}", status)
        
        self.log(f"\nTotal: {passed}/{total} tests passed\n", "pass" if passed == total else "fail")
        
        return 0 if passed == total else 1

def main():
    import sys
    
    tester = APITester(BASE_URL)
    return tester.run_all_tests()

if __name__ == '__main__':
    import sys
    sys.exit(main())
