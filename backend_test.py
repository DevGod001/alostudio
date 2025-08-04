import requests
import sys
from datetime import datetime, timedelta
import json

class AlostudioAPITester:
    def __init__(self, base_url="https://a11188dd-ed74-44ef-b8ec-e94856b80d3a.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_booking_id = None
        self.test_service_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response: Found {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.text else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_get_all_services(self):
        """Test getting all services"""
        success, response = self.run_test("Get All Services", "GET", "services", 200)
        if success and response:
            # Store first service ID for booking tests
            if len(response) > 0:
                self.test_service_id = response[0]['id']
                print(f"   Stored service ID for testing: {self.test_service_id}")
        return success

    def test_get_services_by_type(self):
        """Test getting services by type"""
        success1, _ = self.run_test("Get Makeup Services", "GET", "services/makeup", 200)
        success2, _ = self.run_test("Get Photography Services", "GET", "services/photography", 200)
        success3, _ = self.run_test("Get Video Services", "GET", "services/video", 200)
        return success1 and success2 and success3

    def test_availability_check(self):
        """Test availability checking"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        success, response = self.run_test("Check Availability", "GET", f"availability/{tomorrow}", 200)
        if success and response:
            print(f"   Available slots: {len(response.get('available_slots', []))}")
        return success

    def test_create_booking(self):
        """Test creating a booking"""
        if not self.test_service_id:
            print("❌ Cannot test booking - no service ID available")
            return False

        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        booking_data = {
            "service_id": self.test_service_id,
            "customer_name": "John Doe",
            "customer_email": "john@test.com",
            "customer_phone": "555-1234",
            "booking_date": tomorrow,
            "booking_time": "10:00"
        }
        
        success, response = self.run_test("Create Booking", "POST", "bookings", 200, booking_data)
        if success and response:
            self.created_booking_id = response.get('id')
            print(f"   Created booking ID: {self.created_booking_id}")
        return success

    def test_submit_payment(self):
        """Test submitting payment for booking"""
        if not self.created_booking_id:
            print("❌ Cannot test payment - no booking ID available")
            return False

        payment_data = {
            "booking_id": self.created_booking_id,
            "payment_amount": 50.0,
            "payment_reference": "TEST_REF_123"
        }
        
        return self.run_test("Submit Payment", "POST", f"bookings/{self.created_booking_id}/payment", 200, payment_data)[0]

    def test_customer_bookings(self):
        """Test getting customer bookings"""
        return self.run_test("Get Customer Bookings", "GET", "bookings/customer/john@test.com", 200)[0]

    def test_admin_login(self):
        """Test admin login"""
        admin_data = {
            "username": "admin",
            "password": "admin123"
        }
        return self.run_test("Admin Login", "POST", "admin/login", 200, admin_data)[0]

    def test_admin_get_bookings(self):
        """Test admin getting all bookings"""
        return self.run_test("Admin Get All Bookings", "GET", "admin/bookings", 200)[0]

    def test_admin_booking_actions(self):
        """Test admin booking management actions"""
        if not self.created_booking_id:
            print("❌ Cannot test admin actions - no booking ID available")
            return False

        success1 = self.run_test("Admin Approve Booking", "PUT", f"admin/bookings/{self.created_booking_id}/approve", 200)[0]
        success2 = self.run_test("Admin Complete Booking", "PUT", f"admin/bookings/{self.created_booking_id}/complete", 200)[0]
        
        return success1 and success2

    def test_admin_services(self):
        """Test admin service management"""
        return self.run_test("Admin Get All Services", "GET", "admin/services", 200)[0]

    def test_combo_services(self):
        """Test getting combo services"""
        success, response = self.run_test("Get Combo Services", "GET", "combo-services", 200)
        if success and response:
            print(f"   Found {len(response)} combo services")
            for combo in response:
                print(f"   - {combo.get('name', 'Unknown')}: ${combo.get('final_price', 0)} (was ${combo.get('total_price', 0)})")
        return success

    def test_settings(self):
        """Test getting settings"""
        success, response = self.run_test("Get Settings", "GET", "settings", 200)
        if success and response:
            print(f"   WhatsApp: {response.get('whatsapp_number', 'Not set')}")
            print(f"   CashApp: {response.get('cashapp_id', 'Not set')}")
        return success

    def test_admin_update_settings(self):
        """Test admin updating settings"""
        settings_data = {
            "whatsapp_number": "+16144055997",
            "cashapp_id": "$VitiPay"
        }
        return self.run_test("Admin Update Settings", "PUT", "admin/settings", 200, settings_data)[0]

def main():
    print("🚀 Starting Alostudio API Tests")
    print("=" * 50)
    
    tester = AlostudioAPITester()
    
    # Test sequence
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Get All Services", tester.test_get_all_services),
        ("Get Services by Type", tester.test_get_services_by_type),
        ("Get Combo Services", tester.test_combo_services),
        ("Get Settings", tester.test_settings),
        ("Check Availability", tester.test_availability_check),
        ("Create Booking", tester.test_create_booking),
        ("Submit Payment", tester.test_submit_payment),
        ("Get Customer Bookings", tester.test_customer_bookings),
        ("Admin Login", tester.test_admin_login),
        ("Admin Get Bookings", tester.test_admin_get_bookings),
        ("Admin Booking Actions", tester.test_admin_booking_actions),
        ("Admin Services", tester.test_admin_services),
        ("Admin Update Settings", tester.test_admin_update_settings)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())