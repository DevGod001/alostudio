import requests
import sys
from datetime import datetime, timedelta
import json

class AlostudioAPITester:
    def __init__(self, base_url="https://660c9e73-bf14-4313-a5e9-0d599270a454.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_booking_id = None
        self.test_service_id = None
        self.admin_session_token = None
        self.test_photo_id = None
        self.test_frame_order_id = None
        self.test_user_email = "test@example.com"

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
        """Test admin login and store session token"""
        admin_data = {
            "username": "admin",
            "password": "admin123"
        }
        success, response = self.run_test("Admin Login", "POST", "admin/login", 200, admin_data)
        if success and response:
            self.admin_session_token = response.get('session_token')
            print(f"   Session token stored: {self.admin_session_token[:20]}...")
            print(f"   Expires at: {response.get('expires_at')}")
        return success

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

    # NEW TESTS FOR SPECIFIC FEATURES

    def test_admin_session_verification(self):
        """Test admin session verification and renewal"""
        if not self.admin_session_token:
            print("❌ Cannot test session verification - no session token available")
            return False
        
        success, response = self.run_test("Admin Session Verification", "POST", 
                                        f"admin/verify-session?session_token={self.admin_session_token}", 200)
        if success and response:
            print(f"   Session extended to: {response.get('expires_at')}")
        return success

    def test_user_photo_upload(self):
        """Test user photo upload"""
        photo_data = {
            "user_email": self.test_user_email,
            "user_name": "Test User",
            "file_name": "test_photo.jpg",
            "photo_type": "upload"
        }
        success, response = self.run_test("User Photo Upload", "POST", "user/photos", 200, photo_data)
        if success and response:
            self.test_photo_id = response.get('photo_id')
            print(f"   Photo ID stored: {self.test_photo_id}")
        return success

    def test_get_user_photos(self):
        """Test retrieving user photos"""
        return self.run_test("Get User Photos", "GET", f"user/{self.test_user_email}/photos", 200)[0]

    def test_user_dashboard(self):
        """Test comprehensive user dashboard data"""
        success, response = self.run_test("User Dashboard", "GET", f"user/{self.test_user_email}/dashboard", 200)
        if success and response:
            print(f"   Photos: {len(response.get('photos', []))}")
            print(f"   Bookings: {len(response.get('bookings', []))}")
            print(f"   Frame Orders: {len(response.get('frame_orders', []))}")
            stats = response.get('stats', {})
            print(f"   Stats - Total Photos: {stats.get('total_photos', 0)}, Total Bookings: {stats.get('total_bookings', 0)}")
        return success

    def test_create_frame_order(self):
        """Test creating frame orders with different sizes"""
        if not self.test_photo_id:
            print("❌ Cannot test frame order - no photo ID available")
            return False

        # Test different frame sizes and their pricing
        frame_sizes = ["5x7", "8x10", "11x14", "16x20"]
        expected_prices = {"5x7": 25.0, "8x10": 45.0, "11x14": 75.0, "16x20": 120.0}
        
        all_success = True
        for size in frame_sizes:
            order_data = {
                "user_email": self.test_user_email,
                "user_name": "Test User",
                "photo_ids": [self.test_photo_id],
                "frame_size": size,
                "frame_style": "modern",
                "quantity": 2,
                "special_instructions": f"Test order for {size} frames"
            }
            
            success, response = self.run_test(f"Create Frame Order ({size})", "POST", "frames/order", 200, order_data)
            if success and response:
                expected_total = expected_prices[size] * 2
                actual_total = response.get('total_price', 0)
                if actual_total == expected_total:
                    print(f"   ✅ Pricing correct: {size} = ${actual_total} (${expected_prices[size]} x 2)")
                    if size == "8x10":  # Store one order ID for payment testing
                        self.test_frame_order_id = response.get('id')
                        print(f"   Frame order ID stored: {self.test_frame_order_id}")
                else:
                    print(f"   ❌ Pricing incorrect: Expected ${expected_total}, got ${actual_total}")
                    all_success = False
            else:
                all_success = False
        
        return all_success

    def test_frame_order_payment(self):
        """Test frame order payment submission"""
        if not self.test_frame_order_id:
            print("❌ Cannot test frame payment - no frame order ID available")
            return False

        payment_data = {
            "booking_id": self.test_frame_order_id,
            "payment_amount": 90.0,  # 8x10 frames: $45 x 2
            "payment_reference": "FRAME_TEST_REF_456"
        }
        
        return self.run_test("Frame Order Payment", "POST", f"frames/{self.test_frame_order_id}/payment", 200, payment_data)[0]

    def test_admin_get_frame_orders(self):
        """Test admin retrieval of frame orders"""
        success, response = self.run_test("Admin Get Frame Orders", "GET", "admin/frames", 200)
        if success and response:
            print(f"   Found {len(response)} frame orders")
            for order in response[:3]:  # Show first 3
                print(f"   - Order {order.get('id', 'Unknown')[:8]}...: {order.get('frame_size')} {order.get('frame_style')} x{order.get('quantity')} = ${order.get('total_price')}")
        return success

    def test_admin_approve_frame_order(self):
        """Test admin approval of frame orders"""
        if not self.test_frame_order_id:
            print("❌ Cannot test frame approval - no frame order ID available")
            return False

        return self.run_test("Admin Approve Frame Order", "PUT", f"admin/frames/{self.test_frame_order_id}/approve", 200)[0]

    def test_admin_earnings(self):
        """Test admin earnings/wallet API"""
        success, response = self.run_test("Admin Earnings", "GET", "admin/earnings", 200)
        if success and response:
            print(f"   Total Earnings: ${response.get('total_earnings', 0)}")
            print(f"   Recent Earnings (30 days): ${response.get('recent_earnings', 0)}")
            
            breakdown = response.get('service_breakdown', {})
            print(f"   Service Breakdown:")
            for service, amount in breakdown.items():
                print(f"     - {service}: ${amount}")
            
            stats = response.get('stats', {})
            print(f"   Stats - Total Transactions: {stats.get('total_transactions', 0)}")
            print(f"   Average Transaction: ${stats.get('average_transaction', 0):.2f}")
        return success

    def test_service_types_enhancement(self):
        """Test that new service types are properly created"""
        success, response = self.run_test("Get All Services (Enhanced)", "GET", "services", 200)
        if success and response:
            service_types = set()
            for service in response:
                service_types.add(service.get('type'))
            
            expected_types = {'makeup', 'photography', 'video', 'editing', 'graphic_design', 'frames'}
            missing_types = expected_types - service_types
            
            if not missing_types:
                print(f"   ✅ All expected service types found: {sorted(service_types)}")
                
                # Check specific new services
                frames_services = [s for s in response if s.get('type') == 'frames']
                editing_services = [s for s in response if s.get('type') == 'editing']
                design_services = [s for s in response if s.get('type') == 'graphic_design']
                
                print(f"   - Frame services: {len(frames_services)}")
                print(f"   - Editing services: {len(editing_services)}")
                print(f"   - Graphic design services: {len(design_services)}")
                
                return True
            else:
                print(f"   ❌ Missing service types: {missing_types}")
                return False
        return success

    def test_invalid_admin_session(self):
        """Test invalid session token handling"""
        invalid_token = "invalid-token-12345"
        success, response = self.run_test("Invalid Session Token", "POST", 
                                        f"admin/verify-session?session_token={invalid_token}", 401)
        # For this test, we expect a 401 status, so success means we got the expected error
        return success

    # ADMIN PHOTO UPLOAD TESTS - NEW FUNCTIONALITY
    
    def test_admin_photo_upload_base64(self):
        """Test admin photo upload using base64 method for completed bookings"""
        if not self.created_booking_id:
            print("❌ Cannot test admin photo upload - no completed booking ID available")
            return False
        
        # Sample base64 image data (small test image)
        sample_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        upload_data = {
            "user_email": "test@example.com",
            "user_name": "Test User",
            "booking_id": self.created_booking_id,
            "files": [
                {
                    "file_name": "session_photo1.jpg",
                    "file_data": sample_base64
                },
                {
                    "file_name": "session_photo2.jpg", 
                    "file_data": sample_base64
                }
            ],
            "photo_type": "session"
        }
        
        success, response = self.run_test("Admin Photo Upload (Base64)", "POST", 
                                        f"admin/bookings/{self.created_booking_id}/upload-photos-base64", 200, upload_data)
        if success and response:
            photos = response.get('photos', [])
            print(f"   Successfully uploaded {len(photos)} photos")
            for photo in photos:
                print(f"   - Photo ID: {photo.get('id')}, File: {photo.get('file_name')}")
        return success

    def test_admin_photo_upload_non_completed_booking(self):
        """Test that admin photo upload fails for non-completed bookings"""
        # Create a new booking that's not completed
        if not self.test_service_id:
            print("❌ Cannot test - no service ID available")
            return False

        tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        booking_data = {
            "service_id": self.test_service_id,
            "customer_name": "Jane Doe",
            "customer_email": "jane@test.com",
            "customer_phone": "555-5678",
            "booking_date": tomorrow,
            "booking_time": "14:00"
        }
        
        # Create booking
        success, response = self.run_test("Create Test Booking (Non-Completed)", "POST", "bookings", 200, booking_data)
        if not success:
            return False
            
        non_completed_booking_id = response.get('id')
        
        # Try to upload photos to non-completed booking (should fail)
        sample_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        upload_data = {
            "user_email": "jane@test.com",
            "user_name": "Jane Doe",
            "booking_id": non_completed_booking_id,
            "files": [{"file_name": "test.jpg", "file_data": sample_base64}],
            "photo_type": "session"
        }
        
        success, response = self.run_test("Admin Photo Upload (Non-Completed Booking)", "POST", 
                                        f"admin/bookings/{non_completed_booking_id}/upload-photos-base64", 400, upload_data)
        # For this test, we expect a 400 status (bad request), so success means we got the expected error
        return success

    def test_get_booking_photos(self):
        """Test retrieving photos for a specific booking"""
        if not self.created_booking_id:
            print("❌ Cannot test - no booking ID available")
            return False
            
        success, response = self.run_test("Get Booking Photos", "GET", 
                                        f"admin/bookings/{self.created_booking_id}/photos", 200)
        if success and response:
            print(f"   Found {len(response)} photos for booking")
            for photo in response:
                print(f"   - Photo: {photo.get('file_name')}, Type: {photo.get('photo_type')}, Admin Upload: {photo.get('uploaded_by_admin')}")
        return success

    def test_user_dashboard_with_session_photos(self):
        """Test that uploaded session photos appear in user dashboard"""
        success, response = self.run_test("User Dashboard (With Session Photos)", "GET", 
                                        f"user/test@example.com/dashboard", 200)
        if success and response:
            photos = response.get('photos', [])
            session_photos = [p for p in photos if p.get('photo_type') == 'session' and p.get('uploaded_by_admin')]
            
            print(f"   Total photos in dashboard: {len(photos)}")
            print(f"   Session photos uploaded by admin: {len(session_photos)}")
            
            if session_photos:
                print("   Session photos found:")
                for photo in session_photos[:3]:  # Show first 3
                    print(f"   - {photo.get('file_name')} (Booking: {photo.get('booking_id')})")
                return True
            else:
                print("   ❌ No session photos found in user dashboard")
                return False
        return success

    def test_admin_photo_upload_workflow(self):
        """Test complete admin photo upload workflow"""
        print("\n🔄 Testing Complete Admin Photo Upload Workflow:")
        
        # Step 1: Verify we have a completed booking
        if not self.created_booking_id:
            print("❌ No completed booking available for workflow test")
            return False
        
        print(f"   ✅ Using completed booking: {self.created_booking_id}")
        
        # Step 2: Upload photos via admin
        sample_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        upload_data = {
            "user_email": "test@example.com",
            "user_name": "Test User",
            "booking_id": self.created_booking_id,
            "files": [
                {"file_name": "workflow_photo1.jpg", "file_data": sample_base64},
                {"file_name": "workflow_photo2.jpg", "file_data": sample_base64}
            ],
            "photo_type": "session"
        }
        
        success1, response1 = self.run_test("Workflow: Admin Upload Photos", "POST", 
                                          f"admin/bookings/{self.created_booking_id}/upload-photos-base64", 200, upload_data)
        if not success1:
            return False
        
        print(f"   ✅ Uploaded {len(response1.get('photos', []))} photos")
        
        # Step 3: Verify photos appear in booking photos endpoint
        success2, response2 = self.run_test("Workflow: Get Booking Photos", "GET", 
                                          f"admin/bookings/{self.created_booking_id}/photos", 200)
        if not success2:
            return False
        
        booking_photos = response2
        workflow_photos = [p for p in booking_photos if 'workflow_photo' in p.get('file_name', '')]
        print(f"   ✅ Found {len(workflow_photos)} workflow photos in booking")
        
        # Step 4: Verify photos appear in user dashboard
        success3, response3 = self.run_test("Workflow: User Dashboard Check", "GET", 
                                          f"user/test@example.com/dashboard", 200)
        if not success3:
            return False
        
        dashboard_photos = response3.get('photos', [])
        dashboard_workflow_photos = [p for p in dashboard_photos if 'workflow_photo' in p.get('file_name', '')]
        print(f"   ✅ Found {len(dashboard_workflow_photos)} workflow photos in user dashboard")
        
        # Step 5: Verify metadata is correct
        if dashboard_workflow_photos:
            sample_photo = dashboard_workflow_photos[0]
            metadata_correct = (
                sample_photo.get('photo_type') == 'session' and
                sample_photo.get('uploaded_by_admin') == True and
                sample_photo.get('booking_id') == self.created_booking_id
            )
            
            if metadata_correct:
                print("   ✅ Photo metadata is correct (session type, admin uploaded, correct booking ID)")
                return True
            else:
                print("   ❌ Photo metadata is incorrect")
                print(f"      Type: {sample_photo.get('photo_type')} (expected: session)")
                print(f"      Admin uploaded: {sample_photo.get('uploaded_by_admin')} (expected: True)")
                print(f"      Booking ID: {sample_photo.get('booking_id')} (expected: {self.created_booking_id})")
                return False
        else:
            print("   ❌ No workflow photos found in user dashboard")
            return False

    def test_admin_photo_upload_invalid_booking(self):
        """Test admin photo upload with invalid booking ID"""
        invalid_booking_id = "invalid-booking-123"
        sample_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        upload_data = {
            "user_email": "test@example.com",
            "user_name": "Test User",
            "booking_id": invalid_booking_id,
            "files": [{"file_name": "test.jpg", "file_data": sample_base64}],
            "photo_type": "session"
        }
        
        success, response = self.run_test("Admin Photo Upload (Invalid Booking)", "POST", 
                                        f"admin/bookings/{invalid_booking_id}/upload-photos-base64", 404, upload_data)
        # For this test, we expect a 404 status, so success means we got the expected error
        return success

def main():
    print("🚀 Starting Alostudio API Tests - Comprehensive Backend Testing")
    print("=" * 70)
    
    tester = AlostudioAPITester()
    
    # Test sequence - organized by feature areas
    tests = [
        # Basic API Tests
        ("Root Endpoint", tester.test_root_endpoint),
        ("Get All Services", tester.test_get_all_services),
        ("Service Types Enhancement", tester.test_service_types_enhancement),
        ("Get Services by Type", tester.test_get_services_by_type),
        ("Get Combo Services", tester.test_combo_services),
        ("Get Settings", tester.test_settings),
        
        # Booking Flow Tests
        ("Check Availability", tester.test_availability_check),
        ("Create Booking", tester.test_create_booking),
        ("Submit Payment", tester.test_submit_payment),
        ("Get Customer Bookings", tester.test_customer_bookings),
        
        # Admin Session Management Tests
        ("Admin Login", tester.test_admin_login),
        ("Admin Session Verification", tester.test_admin_session_verification),
        ("Invalid Session Token", tester.test_invalid_admin_session),
        
        # Photo Gallery API Tests
        ("User Photo Upload", tester.test_user_photo_upload),
        ("Get User Photos", tester.test_get_user_photos),
        ("User Dashboard", tester.test_user_dashboard),
        
        # Frame Order System Tests
        ("Create Frame Orders", tester.test_create_frame_order),
        ("Frame Order Payment", tester.test_frame_order_payment),
        ("Admin Get Frame Orders", tester.test_admin_get_frame_orders),
        ("Admin Approve Frame Order", tester.test_admin_approve_frame_order),
        
        # Admin Management Tests
        ("Admin Get Bookings", tester.test_admin_get_bookings),
        ("Admin Booking Actions", tester.test_admin_booking_actions),
        ("Admin Services", tester.test_admin_services),
        ("Admin Update Settings", tester.test_admin_update_settings),
        
        # Admin Photo Upload Tests - NEW FUNCTIONALITY
        ("Admin Photo Upload (Base64)", tester.test_admin_photo_upload_base64),
        ("Admin Photo Upload (Non-Completed Booking)", tester.test_admin_photo_upload_non_completed_booking),
        ("Admin Photo Upload (Invalid Booking)", tester.test_admin_photo_upload_invalid_booking),
        ("Get Booking Photos", tester.test_get_booking_photos),
        ("User Dashboard (With Session Photos)", tester.test_user_dashboard_with_session_photos),
        ("Admin Photo Upload Workflow", tester.test_admin_photo_upload_workflow),
        
        # Admin Earnings/Wallet Tests
        ("Admin Earnings", tester.test_admin_earnings),
    ]
    
    print(f"📋 Running {len(tests)} comprehensive tests...")
    
    for test_name, test_func in tests:
        print(f"\n{'='*25} {test_name} {'='*25}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {str(e)}")
    
    # Print final results
    print(f"\n{'='*70}")
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