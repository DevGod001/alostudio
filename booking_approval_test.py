import requests
import sys
from datetime import datetime, timedelta
import json

class BookingApprovalWorkflowTester:
    def __init__(self, base_url="https://660c9e73-bf14-4313-a5e9-0d599270a454.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_session_token = None
        self.test_booking_id = None
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

    def setup_test_data(self):
        """Setup required test data"""
        print("\n📋 Setting up test data...")
        
        # Get services
        success, services = self.run_test("Get Services", "GET", "services", 200)
        if success and services:
            self.test_service_id = services[0]['id']
            print(f"   Using service: {services[0]['name']} (ID: {self.test_service_id})")
        
        # Admin login
        admin_data = {"username": "admin", "password": "admin123"}
        success, response = self.run_test("Admin Login", "POST", "admin/login", 200, admin_data)
        if success and response:
            self.admin_session_token = response.get('session_token')
            print(f"   Admin session established")
        
        return self.test_service_id and self.admin_session_token

    def test_create_booking_with_payment(self):
        """Test 1: Create a new booking and submit payment to trigger payment_submitted status"""
        print("\n" + "="*60)
        print("TEST 1: Create Test Booking with Payment")
        print("="*60)
        
        if not self.test_service_id:
            print("❌ Cannot create booking - no service ID available")
            return False
        
        # Step 1: Create booking
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        booking_data = {
            "service_id": self.test_service_id,
            "customer_name": "Sarah Johnson",
            "customer_email": "sarah.johnson@email.com",
            "customer_phone": "555-0123",
            "booking_date": tomorrow,
            "booking_time": "14:30"
        }
        
        success, response = self.run_test("Create New Booking", "POST", "bookings", 200, booking_data)
        if not success:
            return False
        
        self.test_booking_id = response.get('id')
        initial_status = response.get('status')
        print(f"   ✅ Booking created with ID: {self.test_booking_id}")
        print(f"   ✅ Initial status: {initial_status}")
        
        # Verify initial status is pending_payment
        if initial_status != "pending_payment":
            print(f"   ❌ Expected initial status 'pending_payment', got '{initial_status}'")
            return False
        
        # Step 2: Submit payment
        payment_data = {
            "booking_id": self.test_booking_id,
            "payment_amount": 75.0,  # Deposit amount
            "payment_reference": "CASHAPP_REF_SAR123"
        }
        
        success, response = self.run_test("Submit Payment", "POST", f"bookings/{self.test_booking_id}/payment", 200, payment_data)
        if not success:
            return False
        
        print(f"   ✅ Payment submitted successfully")
        
        # Step 3: Verify booking status changed to payment_submitted
        success, bookings = self.run_test("Get Customer Bookings", "GET", "bookings/customer/sarah.johnson@email.com", 200)
        if success and bookings:
            booking = next((b for b in bookings if b['id'] == self.test_booking_id), None)
            if booking:
                current_status = booking.get('status')
                payment_amount = booking.get('payment_amount')
                payment_ref = booking.get('payment_reference')
                
                print(f"   ✅ Current status: {current_status}")
                print(f"   ✅ Payment amount: ${payment_amount}")
                print(f"   ✅ Payment reference: {payment_ref}")
                
                if current_status == "payment_submitted":
                    print("   ✅ Status correctly changed to 'payment_submitted'")
                    return True
                else:
                    print(f"   ❌ Expected status 'payment_submitted', got '{current_status}'")
                    return False
            else:
                print("   ❌ Booking not found in customer bookings")
                return False
        
        return False

    def test_admin_payment_approval_workflow(self):
        """Test 2: Admin payment approval workflow"""
        print("\n" + "="*60)
        print("TEST 2: Admin Payment Approval Workflow")
        print("="*60)
        
        if not self.test_booking_id:
            print("❌ Cannot test approval - no booking ID available")
            return False
        
        # Step 1: Verify booking appears in admin dashboard with payment_submitted status
        success, bookings = self.run_test("Admin Get All Bookings", "GET", "admin/bookings", 200)
        if not success:
            return False
        
        test_booking = next((b for b in bookings if b['id'] == self.test_booking_id), None)
        if not test_booking:
            print("   ❌ Test booking not found in admin bookings")
            return False
        
        print(f"   ✅ Booking found in admin dashboard")
        print(f"   ✅ Status: {test_booking.get('status')}")
        print(f"   ✅ Customer: {test_booking.get('customer_name')}")
        print(f"   ✅ Payment amount: ${test_booking.get('payment_amount')}")
        
        if test_booking.get('status') != 'payment_submitted':
            print(f"   ❌ Expected status 'payment_submitted', got '{test_booking.get('status')}'")
            return False
        
        # Step 2: Test admin approve endpoint
        success, response = self.run_test("Admin Approve Payment", "PUT", f"admin/bookings/{self.test_booking_id}/approve", 200)
        if not success:
            return False
        
        print(f"   ✅ Admin approval successful")
        
        # Step 3: Verify status changed to confirmed
        success, bookings = self.run_test("Verify Status After Approval", "GET", "admin/bookings", 200)
        if success and bookings:
            approved_booking = next((b for b in bookings if b['id'] == self.test_booking_id), None)
            if approved_booking:
                new_status = approved_booking.get('status')
                print(f"   ✅ Status after approval: {new_status}")
                
                if new_status == "confirmed":
                    print("   ✅ Status correctly changed to 'confirmed'")
                else:
                    print(f"   ❌ Expected status 'confirmed', got '{new_status}'")
                    return False
            else:
                print("   ❌ Booking not found after approval")
                return False
        
        # Step 4: Verify earnings are properly recorded
        success, earnings = self.run_test("Check Earnings After Approval", "GET", "admin/earnings", 200)
        if success and earnings:
            earnings_history = earnings.get('earnings_history', [])
            booking_earnings = [e for e in earnings_history if e.get('booking_id') == self.test_booking_id]
            
            if booking_earnings:
                earning = booking_earnings[0]
                print(f"   ✅ Earnings recorded: ${earning.get('amount')} for {earning.get('service_type')}")
                print(f"   ✅ Payment date: {earning.get('payment_date')}")
                return True
            else:
                print("   ❌ No earnings recorded for approved booking")
                return False
        
        return False

    def test_status_progression_workflow(self):
        """Test 3: Complete booking workflow - payment_submitted → confirmed → completed"""
        print("\n" + "="*60)
        print("TEST 3: Status Progression Testing")
        print("="*60)
        
        if not self.test_booking_id:
            print("❌ Cannot test progression - no booking ID available")
            return False
        
        # At this point, booking should be in 'confirmed' status from previous test
        success, bookings = self.run_test("Check Current Status", "GET", "admin/bookings", 200)
        if not success:
            return False
        
        current_booking = next((b for b in bookings if b['id'] == self.test_booking_id), None)
        if not current_booking:
            print("   ❌ Booking not found")
            return False
        
        current_status = current_booking.get('status')
        print(f"   ✅ Current status: {current_status}")
        
        if current_status != 'confirmed':
            print(f"   ❌ Expected status 'confirmed' for progression test, got '{current_status}'")
            return False
        
        # Test completion with payment verification
        completion_data = {
            "booking_id": self.test_booking_id,
            "full_payment_received": True,
            "full_payment_amount": 150.0,  # Full service amount
            "payment_reference": "FINAL_PAYMENT_SAR456"
        }
        
        success, response = self.run_test("Admin Complete Booking", "PUT", f"admin/bookings/{self.test_booking_id}/complete", 200, completion_data)
        if not success:
            return False
        
        print(f"   ✅ Booking completion successful")
        
        # Verify final status is completed
        success, bookings = self.run_test("Verify Final Status", "GET", "admin/bookings", 200)
        if success and bookings:
            completed_booking = next((b for b in bookings if b['id'] == self.test_booking_id), None)
            if completed_booking:
                final_status = completed_booking.get('status')
                full_payment_received = completed_booking.get('full_payment_received')
                full_payment_amount = completed_booking.get('full_payment_amount')
                
                print(f"   ✅ Final status: {final_status}")
                print(f"   ✅ Full payment received: {full_payment_received}")
                print(f"   ✅ Full payment amount: ${full_payment_amount}")
                
                if final_status == "completed":
                    print("   ✅ Status correctly changed to 'completed'")
                    
                    # Check if balance payment earnings were recorded
                    success, earnings = self.run_test("Check Balance Payment Earnings", "GET", "admin/earnings", 200)
                    if success and earnings:
                        earnings_history = earnings.get('earnings_history', [])
                        balance_earnings = [e for e in earnings_history if e.get('booking_id') == self.test_booking_id and '_balance' in e.get('service_type', '')]
                        
                        if balance_earnings:
                            balance_earning = balance_earnings[0]
                            print(f"   ✅ Balance payment earnings recorded: ${balance_earning.get('amount')}")
                            print(f"   ✅ Service type: {balance_earning.get('service_type')}")
                        else:
                            print("   ⚠️  No balance payment earnings found (may be expected if deposit = full amount)")
                    
                    return True
                else:
                    print(f"   ❌ Expected final status 'completed', got '{final_status}'")
                    return False
            else:
                print("   ❌ Booking not found after completion")
                return False
        
        return False

    def test_current_database_state(self):
        """Test 4: Check current database state and booking statuses"""
        print("\n" + "="*60)
        print("TEST 4: Current Database State")
        print("="*60)
        
        # Get all bookings and analyze their statuses
        success, bookings = self.run_test("Get All Bookings", "GET", "admin/bookings", 200)
        if not success:
            return False
        
        print(f"   ✅ Total bookings in database: {len(bookings)}")
        
        # Count bookings by status
        status_counts = {}
        payment_submitted_bookings = []
        
        for booking in bookings:
            status = booking.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if status == 'payment_submitted':
                payment_submitted_bookings.append(booking)
        
        print(f"   ✅ Booking status breakdown:")
        for status, count in status_counts.items():
            print(f"     - {status}: {count}")
        
        # Show payment_submitted bookings in detail
        if payment_submitted_bookings:
            print(f"   ✅ Bookings in 'payment_submitted' status:")
            for booking in payment_submitted_bookings[:5]:  # Show first 5
                print(f"     - ID: {booking.get('id')[:8]}...")
                print(f"       Customer: {booking.get('customer_name')}")
                print(f"       Email: {booking.get('customer_email')}")
                print(f"       Payment: ${booking.get('payment_amount')}")
                print(f"       Reference: {booking.get('payment_reference')}")
                print(f"       Date: {booking.get('booking_date')}")
                print()
        else:
            print(f"   ✅ No bookings currently in 'payment_submitted' status")
        
        # Test booking creation process sets correct statuses
        print(f"   🔍 Testing booking creation process...")
        
        # Create a test booking to verify initial status
        if self.test_service_id:
            test_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            test_booking_data = {
                "service_id": self.test_service_id,
                "customer_name": "Database Test User",
                "customer_email": "dbtest@email.com",
                "customer_phone": "555-9999",
                "booking_date": test_date,
                "booking_time": "16:00"
            }
            
            success, response = self.run_test("Test Booking Creation Status", "POST", "bookings", 200, test_booking_data)
            if success and response:
                initial_status = response.get('status')
                print(f"   ✅ New booking initial status: {initial_status}")
                
                if initial_status == "pending_payment":
                    print("   ✅ Booking creation process sets correct initial status")
                    return True
                else:
                    print(f"   ❌ Expected initial status 'pending_payment', got '{initial_status}'")
                    return False
        
        return True

    def run_comprehensive_workflow_test(self):
        """Run the complete booking approval workflow test"""
        print("\n" + "="*80)
        print("🎯 ALOSTUDIO BOOKING APPROVAL WORKFLOW TEST")
        print("Testing the payment approval process as requested")
        print("="*80)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Failed to setup test data")
            return False
        
        # Run all workflow tests
        workflow_tests = [
            ("Create Test Booking with Payment", self.test_create_booking_with_payment),
            ("Admin Payment Approval Workflow", self.test_admin_payment_approval_workflow),
            ("Status Progression Testing", self.test_status_progression_workflow),
            ("Current Database State", self.test_current_database_state),
        ]
        
        workflow_passed = 0
        workflow_total = len(workflow_tests)
        
        for test_name, test_func in workflow_tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                if test_func():
                    workflow_passed += 1
                    print(f"✅ {test_name} - PASSED")
                else:
                    print(f"❌ {test_name} - FAILED")
            except Exception as e:
                print(f"❌ {test_name} - FAILED with exception: {str(e)}")
        
        # Final results
        print(f"\n{'='*80}")
        print(f"🎯 BOOKING APPROVAL WORKFLOW TEST RESULTS")
        print(f"Tests passed: {workflow_passed}/{workflow_total}")
        print(f"Success rate: {(workflow_passed/workflow_total)*100:.1f}%")
        print(f"Total API calls: {self.tests_run}")
        print(f"API success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if workflow_passed == workflow_total:
            print("🎉 All booking approval workflow tests passed!")
            print("✅ Payment approval process is working correctly")
        else:
            print("⚠️  Some booking approval workflow tests failed")
            print("❌ Issues found with payment approval process")
        
        return workflow_passed == workflow_total

def main():
    print("🚀 Starting Alostudio Booking Approval Workflow Test")
    print("=" * 70)
    
    tester = BookingApprovalWorkflowTester()
    success = tester.run_comprehensive_workflow_test()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())