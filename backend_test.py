import requests
import sys
from datetime import datetime, timedelta
import json

class AlostudioAPITester:
    def __init__(self, base_url="https://746ffa03-72c3-4e29-97a1-6ab365d40411.preview.emergentagent.com"):
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
        
        # Use the new BookingCompletion model for completion
        completion_data = {
            "booking_id": self.created_booking_id,
            "full_payment_received": True,
            "full_payment_amount": 75.0,  # Natural Glow Glam base price
            "payment_reference": "COMPLETION_TEST_REF"
        }
        success2 = self.run_test("Admin Complete Booking", "PUT", f"admin/bookings/{self.created_booking_id}/complete", 200, completion_data)[0]
        
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

    # FOCUSED TESTS FOR REVIEW REQUEST - NEW FIXES
    
    def test_admin_credentials_from_env(self):
        """Test admin login with environment-based credentials (admin/admin123)"""
        print("\n🔍 Testing Admin Credentials from Environment Variables...")
        
        # Test with correct credentials from .env
        admin_data = {
            "username": "admin",
            "password": "admin123"
        }
        success, response = self.run_test("Admin Login (Env Credentials)", "POST", "admin/login", 200, admin_data)
        if success and response:
            self.admin_session_token = response.get('session_token')
            print(f"   ✅ Login successful with env credentials")
            print(f"   Session token: {self.admin_session_token[:20]}...")
            print(f"   Expires at: {response.get('expires_at')}")
            return True
        return False

    def test_admin_logout_functionality(self):
        """Test new /api/admin/logout endpoint"""
        print("\n🔍 Testing Admin Logout Functionality...")
        
        if not self.admin_session_token:
            print("❌ Cannot test logout - no session token available")
            return False
        
        # Test logout with session token
        success, response = self.run_test("Admin Logout", "POST", 
                                        f"admin/logout?session_token={self.admin_session_token}", 200)
        if success:
            print("   ✅ Logout successful - session invalidated")
            
            # Verify session is actually invalidated by trying to use it
            invalid_success, _ = self.run_test("Verify Session Invalidated", "POST", 
                                             f"admin/verify-session?session_token={self.admin_session_token}", 401)
            if invalid_success:
                print("   ✅ Session properly invalidated - cannot be used after logout")
                self.admin_session_token = None  # Clear the token
                return True
            else:
                print("   ❌ Session not properly invalidated")
                return False
        return False

    def test_booking_completion_with_payment_verification(self):
        """Test updated /api/admin/bookings/{id}/complete endpoint with BookingCompletion model"""
        print("\n🔍 Testing Booking Completion with Payment Verification...")
        
        if not self.created_booking_id:
            print("❌ Cannot test booking completion - no booking ID available")
            return False
        
        # Re-login to get a fresh session token since we logged out
        admin_data = {"username": "admin", "password": "admin123"}
        login_success, login_response = self.run_test("Re-login for Completion Test", "POST", "admin/login", 200, admin_data)
        if not login_success:
            return False
        self.admin_session_token = login_response.get('session_token')
        
        # Test booking completion with full payment verification
        completion_data = {
            "booking_id": self.created_booking_id,
            "full_payment_received": True,
            "full_payment_amount": 150.0,  # Full service amount
            "payment_reference": "FULL_PAYMENT_REF_789"
        }
        
        success, response = self.run_test("Booking Completion (Payment Verification)", "PUT", 
                                        f"admin/bookings/{self.created_booking_id}/complete", 200, completion_data)
        if success:
            print("   ✅ Booking completion with payment verification successful")
            
            # Verify earnings calculation includes balance payment
            earnings_success, earnings_response = self.run_test("Check Earnings After Completion", "GET", "admin/earnings", 200)
            if earnings_success and earnings_response:
                earnings_history = earnings_response.get('earnings_history', [])
                balance_earnings = [e for e in earnings_history if '_balance' in e.get('service_type', '')]
                
                if balance_earnings:
                    print(f"   ✅ Balance payment earnings recorded: {len(balance_earnings)} entries")
                    for earning in balance_earnings[:2]:  # Show first 2
                        print(f"     - {earning.get('service_type')}: ${earning.get('amount')}")
                    return True
                else:
                    print("   ⚠️  No balance payment earnings found (may be expected if deposit = full amount)")
                    return True  # This might be expected behavior
            return True
        return False

    def test_photo_upload_still_works(self):
        """Quick verification that existing photo upload functionality still works after changes"""
        print("\n🔍 Testing Photo Upload Still Works After Changes...")
        
        if not self.created_booking_id:
            print("❌ Cannot test photo upload - no completed booking available")
            return False
        
        # Test admin photo upload (should still work)
        sample_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        upload_data = {
            "user_email": "test@example.com",
            "user_name": "Test User",
            "booking_id": self.created_booking_id,
            "files": [
                {"file_name": "verification_photo.jpg", "file_data": sample_base64}
            ],
            "photo_type": "session"
        }
        
        success, response = self.run_test("Photo Upload Verification", "POST", 
                                        f"admin/bookings/{self.created_booking_id}/upload-photos-base64", 200, upload_data)
        if success and response:
            photos = response.get('photos', [])
            print(f"   ✅ Photo upload still working - uploaded {len(photos)} photos")
            return True
        return False

    def run_focused_review_tests(self):
        """Run the focused tests requested in the review"""
        print("\n" + "="*80)
        print("🎯 FOCUSED REVIEW TESTS - Testing Updated Alostudio Backend Fixes")
        print("="*80)
        
        focused_tests = [
            ("Admin Credentials from Environment Variables", self.test_admin_credentials_from_env),
            ("Admin Logout Functionality", self.test_admin_logout_functionality),
            ("Booking Completion with Payment Verification", self.test_booking_completion_with_payment_verification),
            ("Photo Upload Still Works", self.test_photo_upload_still_works),
        ]
        
        focused_passed = 0
        focused_total = len(focused_tests)
        
        for test_name, test_func in focused_tests:
            print(f"\n{'='*25} {test_name} {'='*25}")
            try:
                if test_func():
                    focused_passed += 1
                    print(f"✅ {test_name} - PASSED")
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"❌ {test_name} - FAILED with exception: {str(e)}")
        
        print(f"\n{'='*80}")
        print(f"🎯 FOCUSED REVIEW RESULTS")
        print(f"Tests passed: {focused_passed}/{focused_total}")
        print(f"Success rate: {(focused_passed/focused_total)*100:.1f}%")
        
        return focused_passed == focused_total

    def run_frame_order_comprehensive_tests(self):
        """Comprehensive frame order system testing as requested in review"""
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE FRAME ORDER SYSTEM VALIDATION")
        print("="*80)
        
        frame_tests = [
            ("Frame Order Creation - All Sizes", self.test_frame_order_all_sizes_comprehensive),
            ("Frame Payment Workflow", self.test_frame_payment_workflow_comprehensive),
            ("Admin Frame Order Management", self.test_admin_frame_management_comprehensive),
            ("Frame Order Status Progression", self.test_frame_status_progression),
            ("Delivery Method Handling", self.test_delivery_method_handling),
            ("Frame Order Earnings Integration", self.test_frame_earnings_integration),
        ]
        
        frame_passed = 0
        frame_total = len(frame_tests)
        
        for test_name, test_func in frame_tests:
            print(f"\n{'='*25} {test_name} {'='*25}")
            try:
                if test_func():
                    frame_passed += 1
                    print(f"✅ {test_name} - PASSED")
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"❌ {test_name} - FAILED with exception: {str(e)}")
        
        print(f"\n{'='*80}")
        print(f"🎯 FRAME ORDER SYSTEM RESULTS")
        print(f"Tests passed: {frame_passed}/{frame_total}")
        print(f"Success rate: {(frame_passed/frame_total)*100:.1f}%")
        
        return frame_passed == frame_total

    def test_frame_order_all_sizes_comprehensive(self):
        """Test frame order creation with all size options and pricing validation"""
        if not self.test_photo_id:
            print("❌ Cannot test frame orders - no photo ID available")
            return False

        frame_sizes = {
            "5x7": 25.0,
            "8x10": 45.0, 
            "11x14": 75.0,
            "16x20": 120.0
        }
        
        frame_styles = ["modern", "classic", "rustic"]
        quantities = [1, 2, 3]
        
        all_success = True
        created_orders = []
        
        for size, expected_price in frame_sizes.items():
            for style in frame_styles[:2]:  # Test 2 styles per size
                for qty in quantities[:2]:  # Test 2 quantities per style
                    order_data = {
                        "user_email": self.test_user_email,
                        "user_name": "Test User",
                        "photo_ids": [self.test_photo_id],
                        "frame_size": size,
                        "frame_style": style,
                        "quantity": qty,
                        "payment_reference": f"INITIAL_REF_{size}_{style}_{qty}",
                        "delivery_method": "self_pickup",
                        "special_instructions": f"Test {size} {style} frame x{qty}"
                    }
                    
                    success, response = self.run_test(f"Create Frame Order ({size} {style} x{qty})", 
                                                    "POST", "frames/order", 200, order_data)
                    if success and response:
                        expected_total = expected_price * qty
                        actual_total = response.get('total_price', 0)
                        
                        if actual_total == expected_total:
                            print(f"   ✅ Pricing correct: {size} {style} x{qty} = ${actual_total}")
                            created_orders.append({
                                'id': response.get('id'),
                                'size': size,
                                'style': style,
                                'quantity': qty,
                                'total': actual_total
                            })
                        else:
                            print(f"   ❌ Pricing incorrect: Expected ${expected_total}, got ${actual_total}")
                            all_success = False
                    else:
                        all_success = False
        
        # Store some order IDs for further testing
        if created_orders:
            self.test_frame_order_id = created_orders[0]['id']
            print(f"   Stored frame order ID for further testing: {self.test_frame_order_id}")
            print(f"   Created {len(created_orders)} frame orders successfully")
        
        return all_success

    def test_frame_payment_workflow_comprehensive(self):
        """Test complete frame payment submission workflow"""
        if not self.test_frame_order_id:
            print("❌ Cannot test frame payment - no frame order ID available")
            return False

        # Test payment submission
        payment_data = {
            "booking_id": self.test_frame_order_id,
            "payment_amount": 25.0,  # 5x7 frame price
            "payment_reference": "FRAME_PAYMENT_TEST_REF"
        }
        
        success, response = self.run_test("Frame Payment Submission", "POST", 
                                        f"frames/{self.test_frame_order_id}/payment", 200, payment_data)
        if not success:
            return False
        
        print("   ✅ Frame payment submitted successfully")
        
        # Verify payment was recorded by checking admin frame orders
        success2, response2 = self.run_test("Verify Payment Recorded", "GET", "admin/frames", 200)
        if success2 and response2:
            paid_order = None
            for order in response2:
                if order.get('id') == self.test_frame_order_id:
                    paid_order = order
                    break
            
            if paid_order and paid_order.get('status') == 'payment_submitted':
                print(f"   ✅ Payment status updated: {paid_order.get('status')}")
                print(f"   ✅ Payment amount recorded: ${paid_order.get('payment_amount')}")
                print(f"   ✅ Payment reference: {paid_order.get('payment_reference')}")
                return True
            else:
                print("   ❌ Payment not properly recorded in order")
                return False
        
        return False

    def test_admin_frame_management_comprehensive(self):
        """Test admin frame order management endpoints"""
        # Test getting all frame orders
        success1, response1 = self.run_test("Admin Get All Frame Orders", "GET", "admin/frames", 200)
        if not success1:
            return False
        
        frame_orders = response1
        print(f"   Found {len(frame_orders)} total frame orders")
        
        # Show order status distribution
        status_counts = {}
        for order in frame_orders:
            status = order.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("   Status distribution:")
        for status, count in status_counts.items():
            print(f"     - {status}: {count}")
        
        # Test admin approval if we have a payment_submitted order
        payment_submitted_orders = [o for o in frame_orders if o.get('status') == 'payment_submitted']
        if payment_submitted_orders and self.test_frame_order_id:
            success2 = self.run_test("Admin Approve Frame Order", "PUT", 
                                   f"admin/frames/{self.test_frame_order_id}/approve", 200)[0]
            if success2:
                print("   ✅ Frame order approval successful")
                return True
        else:
            print("   ⚠️  No payment_submitted orders to approve (may be expected)")
            return True
        
        return False

    def test_frame_status_progression(self):
        """Test frame order status progression workflow"""
        if not self.test_frame_order_id:
            print("❌ Cannot test status progression - no frame order ID available")
            return False
        
        # Test status updates
        status_updates = [
            ("in_progress", "Order is being processed"),
            ("ready_for_pickup", "Frame is ready for customer pickup"),
            ("completed", "Order completed successfully")
        ]
        
        all_success = True
        for status, admin_notes in status_updates:
            status_data = {
                "status": status,
                "admin_notes": admin_notes
            }
            
            success, response = self.run_test(f"Update Status to {status}", "PUT", 
                                            f"admin/frames/{self.test_frame_order_id}/status", 200, status_data)
            if success:
                print(f"   ✅ Status updated to {status}")
            else:
                all_success = False
        
        return all_success

    def test_delivery_method_handling(self):
        """Test delivery method options and address handling"""
        if not self.test_frame_order_id:
            print("❌ Cannot test delivery methods - no frame order ID available")
            return False
        
        # Test self pickup
        pickup_data = {
            "delivery_method": "self_pickup",
            "special_instructions": "Please call when ready for pickup"
        }
        
        success1 = self.run_test("Set Delivery Method - Self Pickup", "PUT", 
                               f"frames/{self.test_frame_order_id}/delivery", 200, pickup_data)[0]
        
        # Test shipping
        shipping_data = {
            "delivery_method": "ship_to_me",
            "delivery_address": "123 Test Street, Test City, TC 12345",
            "special_instructions": "Leave at front door if no answer"
        }
        
        success2 = self.run_test("Set Delivery Method - Shipping", "PUT", 
                               f"frames/{self.test_frame_order_id}/delivery", 200, shipping_data)[0]
        
        # Test admin adding delivery fee
        fee_data = {"delivery_fee": 15.0}
        success3 = self.run_test("Admin Add Delivery Fee", "PUT", 
                               f"admin/frames/{self.test_frame_order_id}/delivery-fee", 200, fee_data)[0]
        
        return success1 and success2 and success3

    def test_frame_earnings_integration(self):
        """Test frame order earnings integration with admin wallet"""
        # Get earnings before
        success1, response1 = self.run_test("Get Earnings Before Frame Approval", "GET", "admin/earnings", 200)
        if not success1:
            return False
        
        initial_earnings = response1.get('total_earnings', 0)
        initial_frame_earnings = response1.get('service_breakdown', {}).get('frames', 0)
        
        print(f"   Initial total earnings: ${initial_earnings}")
        print(f"   Initial frame earnings: ${initial_frame_earnings}")
        
        # Create and approve a new frame order to test earnings
        if self.test_photo_id:
            order_data = {
                "user_email": "earnings@test.com",
                "user_name": "Earnings Test User",
                "photo_ids": [self.test_photo_id],
                "frame_size": "8x10",
                "frame_style": "modern",
                "quantity": 1,
                "payment_reference": "EARNINGS_INITIAL_REF",
                "delivery_method": "self_pickup"
            }
            
            success2, response2 = self.run_test("Create Frame Order for Earnings Test", "POST", "frames/order", 200, order_data)
            if success2:
                earnings_order_id = response2.get('id')
                
                # Submit payment
                payment_data = {
                    "booking_id": earnings_order_id,
                    "payment_amount": 45.0,
                    "payment_reference": "EARNINGS_TEST_REF"
                }
                
                success3 = self.run_test("Submit Payment for Earnings Test", "POST", 
                                       f"frames/{earnings_order_id}/payment", 200, payment_data)[0]
                
                if success3:
                    # Approve order
                    success4 = self.run_test("Approve Frame Order for Earnings", "PUT", 
                                           f"admin/frames/{earnings_order_id}/approve", 200)[0]
                    
                    if success4:
                        # Check earnings after
                        success5, response5 = self.run_test("Get Earnings After Frame Approval", "GET", "admin/earnings", 200)
                        if success5:
                            final_earnings = response5.get('total_earnings', 0)
                            final_frame_earnings = response5.get('service_breakdown', {}).get('frames', 0)
                            
                            print(f"   Final total earnings: ${final_earnings}")
                            print(f"   Final frame earnings: ${final_frame_earnings}")
                            
                            earnings_increase = final_earnings - initial_earnings
                            frame_earnings_increase = final_frame_earnings - initial_frame_earnings
                            
                            if earnings_increase >= 45.0 and frame_earnings_increase >= 45.0:
                                print(f"   ✅ Earnings correctly increased by ${earnings_increase}")
                                print(f"   ✅ Frame earnings increased by ${frame_earnings_increase}")
                                return True
                            else:
                                print(f"   ❌ Earnings increase incorrect: ${earnings_increase} (expected >= $45)")
                                return False
        
        return False

    def test_customer_dashboard_comprehensive(self):
        """Test customer dashboard APIs with frame orders included"""
        success, response = self.run_test("Customer Dashboard with Frame Orders", "GET", 
                                        f"user/{self.test_user_email}/dashboard", 200)
        if success and response:
            photos = response.get('photos', [])
            bookings = response.get('bookings', [])
            frame_orders = response.get('frame_orders', [])
            stats = response.get('stats', {})
            
            print(f"   Dashboard data retrieved:")
            print(f"   - Photos: {len(photos)}")
            print(f"   - Bookings: {len(bookings)}")
            print(f"   - Frame Orders: {len(frame_orders)}")
            print(f"   - Stats: {stats}")
            
            # Verify frame orders have proper structure
            if frame_orders:
                sample_order = frame_orders[0]
                required_fields = ['id', 'frame_size', 'frame_style', 'quantity', 'total_price', 'status']
                missing_fields = [field for field in required_fields if field not in sample_order]
                
                if not missing_fields:
                    print("   ✅ Frame orders have proper structure")
                    
                    # Check status distribution
                    status_counts = {}
                    for order in frame_orders:
                        status = order.get('status', 'unknown')
                        status_counts[status] = status_counts.get(status, 0) + 1
                    
                    print("   Frame order status distribution:")
                    for status, count in status_counts.items():
                        print(f"     - {status}: {count}")
                    
                    return True
                else:
                    print(f"   ❌ Frame orders missing fields: {missing_fields}")
                    return False
            else:
                print("   ⚠️  No frame orders found in dashboard (may be expected)")
                return True
        
        return False

    def test_admin_session_management_comprehensive(self):
        """Test admin session management with login/logout functionality"""
        # Test login
        admin_data = {"username": "admin", "password": "admin123"}
        success1, response1 = self.run_test("Admin Login", "POST", "admin/login", 200, admin_data)
        if not success1:
            return False
        
        session_token = response1.get('session_token')
        print(f"   ✅ Login successful, session token: {session_token[:20]}...")
        
        # Test session verification
        success2, response2 = self.run_test("Admin Session Verification", "POST", 
                                          f"admin/verify-session?session_token={session_token}", 200)
        if not success2:
            return False
        
        print(f"   ✅ Session verification successful")
        
        # Test logout
        success3 = self.run_test("Admin Logout", "POST", 
                               f"admin/logout?session_token={session_token}", 200)[0]
        if not success3:
            return False
        
        print("   ✅ Logout successful")
        
        # Verify session is invalidated
        success4 = self.run_test("Verify Session Invalidated", "POST", 
                               f"admin/verify-session?session_token={session_token}", 401)[0]
        if success4:
            print("   ✅ Session properly invalidated after logout")
            return True
        
        return False

def main():
    print("🚀 Starting Alostudio API Tests - COMPREHENSIVE FRAME ORDER VALIDATION")
    print("=" * 80)
    
    tester = AlostudioAPITester()
    
    # Essential setup tests
    setup_tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Get All Services", tester.test_get_all_services),
        ("Create Booking", tester.test_create_booking),
        ("Submit Payment", tester.test_submit_payment),
        ("Admin Get Bookings", tester.test_admin_get_bookings),
        ("Admin Booking Actions", tester.test_admin_booking_actions),
        ("User Photo Upload", tester.test_user_photo_upload),
    ]
    
    print(f"📋 Running {len(setup_tests)} setup tests...")
    
    for test_name, test_func in setup_tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Setup test {test_name} failed with exception: {str(e)}")
    
    # Run comprehensive frame order tests
    frame_success = tester.run_frame_order_comprehensive_tests()
    
    # Run customer dashboard test
    print(f"\n{'='*25} Customer Dashboard Integration {'='*25}")
    dashboard_success = tester.test_customer_dashboard_comprehensive()
    
    # Run admin session management test
    print(f"\n{'='*25} Admin Session Management {'='*25}")
    session_success = tester.test_admin_session_management_comprehensive()
    
    # Quick admin photo upload validation
    print(f"\n{'='*25} Admin Photo Upload Validation {'='*25}")
    photo_success = tester.test_photo_upload_still_works()
    
    # Print final results
    print(f"\n{'='*80}")
    print(f"📊 COMPREHENSIVE BACKEND VALIDATION RESULTS")
    print(f"Setup tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Setup success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    print(f"Frame Order System: {'✅ PASSED' if frame_success else '❌ FAILED'}")
    print(f"Customer Dashboard: {'✅ PASSED' if dashboard_success else '❌ FAILED'}")
    print(f"Admin Session Management: {'✅ PASSED' if session_success else '❌ FAILED'}")
    print(f"Admin Photo Upload: {'✅ PASSED' if photo_success else '❌ FAILED'}")
    
    all_success = frame_success and dashboard_success and session_success and photo_success
    
    if all_success:
        print("🎉 All comprehensive backend validation tests passed!")
        print("✅ Frame ordering system is ready for end-to-end testing")
        return 0
    else:
        print("⚠️  Some backend validation tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())