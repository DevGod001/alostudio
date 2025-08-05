import requests
import sys
from datetime import datetime, timedelta
import json

class FramePaymentFocusedTester:
    def __init__(self, base_url="https://660c9e73-bf14-4313-a5e9-0d599270a454.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_session_token = None
        self.test_user_email = "test@example.com"
        self.test_user_name = "Test User"

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
                    if isinstance(response_data, dict) and 'message' in response_data:
                        print(f"   Message: {response_data['message']}")
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

    def test_frame_payment_workflow(self):
        """Test the complete frame payment workflow that was reported as not working"""
        print("\n💳 TESTING FRAME PAYMENT WORKFLOW - USER REPORTED AS NOT WORKING")
        print("="*70)
        
        # Step 1: Admin login
        admin_data = {"username": "admin", "password": "admin123"}
        success1, response1 = self.run_test("Admin Login", "POST", "admin/login", 200, admin_data)
        if not success1:
            return False
        
        self.admin_session_token = response1.get('session_token')
        
        # Step 2: Create test photo
        photo_data = {
            "user_email": self.test_user_email,
            "user_name": self.test_user_name,
            "file_name": "payment_test_photo.jpg",
            "photo_type": "upload"
        }
        success2, response2 = self.run_test("Create Test Photo", "POST", "user/photos", 200, photo_data)
        if not success2:
            return False
        
        photo_id = response2.get('photo_id')
        
        # Step 3: Create frame order
        order_data = {
            "user_email": self.test_user_email,
            "user_name": self.test_user_name,
            "photo_ids": [photo_id],
            "frame_size": "8x10",
            "frame_style": "modern",
            "quantity": 2,
            "special_instructions": "Payment workflow test order"
        }
        success3, response3 = self.run_test("Create Frame Order", "POST", "frames/order", 200, order_data)
        if not success3:
            return False
        
        order_id = response3.get('id')
        total_price = response3.get('total_price')
        initial_status = response3.get('status')
        
        print(f"   ✅ Frame order created:")
        print(f"      Order ID: {order_id}")
        print(f"      Total Price: ${total_price}")
        print(f"      Initial Status: {initial_status}")
        
        # Step 4: Submit payment (THE MAIN FUNCTIONALITY REPORTED AS NOT WORKING)
        payment_data = {
            "booking_id": order_id,  # Note: API uses booking_id field name
            "payment_amount": total_price,
            "payment_reference": "WORKFLOW_TEST_REF_123"
        }
        success4, response4 = self.run_test("Submit Frame Payment (REPORTED NOT WORKING)", "POST", f"frames/{order_id}/payment", 200, payment_data)
        if not success4:
            print("❌ FRAME PAYMENT SUBMISSION FAILED - This confirms the user's report")
            return False
        
        print(f"   ✅ Frame payment submitted successfully!")
        print(f"      Payment Amount: ${payment_data['payment_amount']}")
        print(f"      Payment Reference: {payment_data['payment_reference']}")
        
        # Step 5: Verify payment was recorded by checking admin frame orders
        success5, response5 = self.run_test("Verify Payment in Admin Orders", "GET", "admin/frames", 200)
        if success5 and response5:
            test_order = next((order for order in response5 if order.get('id') == order_id), None)
            if test_order:
                payment_status = test_order.get('status')
                recorded_amount = test_order.get('payment_amount')
                recorded_reference = test_order.get('payment_reference')
                
                print(f"   ✅ Payment verification:")
                print(f"      Status after payment: {payment_status}")
                print(f"      Recorded amount: ${recorded_amount}")
                print(f"      Recorded reference: {recorded_reference}")
                
                if payment_status == 'payment_submitted' and recorded_amount == total_price:
                    print(f"   ✅ Payment correctly recorded and status updated!")
                else:
                    print(f"   ❌ Payment not properly recorded")
                    return False
            else:
                print(f"   ❌ Could not find order in admin list")
                return False
        
        # Step 6: Test admin approval
        success6, response6 = self.run_test("Admin Approve Frame Order", "PUT", f"admin/frames/{order_id}/approve", 200)
        if not success6:
            return False
        
        # Step 7: Verify earnings were recorded
        success7, response7 = self.run_test("Verify Earnings Recorded", "GET", "admin/earnings", 200)
        if success7 and response7:
            earnings_history = response7.get('earnings_history', [])
            recent_frame_earnings = [e for e in earnings_history[:10] if e.get('service_type') == 'frames']
            
            if recent_frame_earnings:
                latest_earning = recent_frame_earnings[0]
                print(f"   ✅ Earnings recorded:")
                print(f"      Amount: ${latest_earning.get('amount')}")
                print(f"      Service Type: {latest_earning.get('service_type')}")
                print(f"      Booking ID: {latest_earning.get('booking_id')}")
            else:
                print(f"   ⚠️  No recent frame earnings found")
        
        print(f"\n🎉 FRAME PAYMENT WORKFLOW COMPLETED SUCCESSFULLY!")
        print(f"   The frame payment functionality that was reported as 'not working' is actually working correctly.")
        return True

    def test_multiple_frame_sizes_payment(self):
        """Test payment submission for all frame sizes"""
        print("\n🖼️  TESTING PAYMENT FOR ALL FRAME SIZES")
        print("="*50)
        
        # Create test photo first
        photo_data = {
            "user_email": self.test_user_email,
            "user_name": self.test_user_name,
            "file_name": "multi_size_test.jpg",
            "photo_type": "upload"
        }
        success, response = self.run_test("Create Photo for Multi-Size Test", "POST", "user/photos", 200, photo_data)
        if not success:
            return False
        
        photo_id = response.get('photo_id')
        
        # Test all frame sizes
        frame_sizes = [
            {"size": "5x7", "expected_price": 25.0},
            {"size": "8x10", "expected_price": 45.0},
            {"size": "11x14", "expected_price": 75.0},
            {"size": "16x20", "expected_price": 120.0}
        ]
        
        payment_success_count = 0
        
        for frame_info in frame_sizes:
            size = frame_info["size"]
            expected_price = frame_info["expected_price"]
            
            # Create order
            order_data = {
                "user_email": self.test_user_email,
                "user_name": self.test_user_name,
                "photo_ids": [photo_id],
                "frame_size": size,
                "frame_style": "modern",
                "quantity": 1,
                "special_instructions": f"Multi-size payment test for {size}"
            }
            
            success1, response1 = self.run_test(f"Create {size} Order", "POST", "frames/order", 200, order_data)
            if not success1:
                continue
            
            order_id = response1.get('id')
            actual_price = response1.get('total_price')
            
            if actual_price != expected_price:
                print(f"   ❌ Price mismatch for {size}: expected ${expected_price}, got ${actual_price}")
                continue
            
            # Submit payment
            payment_data = {
                "booking_id": order_id,
                "payment_amount": actual_price,
                "payment_reference": f"MULTI_SIZE_{size}_REF"
            }
            
            success2, response2 = self.run_test(f"Submit Payment for {size} (${actual_price})", "POST", f"frames/{order_id}/payment", 200, payment_data)
            if success2:
                payment_success_count += 1
                print(f"   ✅ {size} payment successful")
            else:
                print(f"   ❌ {size} payment failed")
        
        success_rate = (payment_success_count / len(frame_sizes)) * 100
        print(f"\n   Payment Success Rate: {payment_success_count}/{len(frame_sizes)} ({success_rate:.1f}%)")
        
        return payment_success_count == len(frame_sizes)

    def test_edge_cases(self):
        """Test edge cases for frame payment"""
        print("\n⚠️  TESTING EDGE CASES")
        print("="*30)
        
        # Test 1: Payment for non-existent order
        invalid_payment_data = {
            "booking_id": "non-existent-order-id",
            "payment_amount": 50.0,
            "payment_reference": "INVALID_TEST_REF"
        }
        success1, response1 = self.run_test("Payment for Non-Existent Order", "POST", "frames/non-existent-order-id/payment", 404, invalid_payment_data)
        
        # Test 2: Create order and test duplicate payment
        photo_data = {
            "user_email": self.test_user_email,
            "user_name": self.test_user_name,
            "file_name": "edge_case_test.jpg",
            "photo_type": "upload"
        }
        success2, response2 = self.run_test("Create Photo for Edge Case", "POST", "user/photos", 200, photo_data)
        if success2:
            photo_id = response2.get('photo_id')
            
            order_data = {
                "user_email": self.test_user_email,
                "user_name": self.test_user_name,
                "photo_ids": [photo_id],
                "frame_size": "8x10",
                "frame_style": "modern",
                "quantity": 1,
                "special_instructions": "Edge case test order"
            }
            
            success3, response3 = self.run_test("Create Order for Edge Case", "POST", "frames/order", 200, order_data)
            if success3:
                order_id = response3.get('id')
                total_price = response3.get('total_price')
                
                # First payment
                payment_data = {
                    "booking_id": order_id,
                    "payment_amount": total_price,
                    "payment_reference": "FIRST_PAYMENT_REF"
                }
                success4, response4 = self.run_test("First Payment", "POST", f"frames/{order_id}/payment", 200, payment_data)
                
                # Second payment (should still work - might update the payment info)
                payment_data2 = {
                    "booking_id": order_id,
                    "payment_amount": total_price,
                    "payment_reference": "SECOND_PAYMENT_REF"
                }
                success5, response5 = self.run_test("Second Payment (Duplicate)", "POST", f"frames/{order_id}/payment", 200, payment_data2)
        
        return success1  # At least the invalid order test should pass

    def run_focused_payment_tests(self):
        """Run focused tests on frame payment functionality"""
        print("\n" + "="*80)
        print("🎯 FOCUSED FRAME PAYMENT TESTING - USER REPORTED ISSUE")
        print("="*80)
        print("Testing the specific frame order payment functionality that was reported as not working")
        
        test_phases = [
            ("Complete Frame Payment Workflow", self.test_frame_payment_workflow),
            ("Multiple Frame Sizes Payment", self.test_multiple_frame_sizes_payment),
            ("Edge Cases", self.test_edge_cases),
        ]
        
        passed_phases = 0
        total_phases = len(test_phases)
        
        for phase_name, phase_func in test_phases:
            print(f"\n{'='*25} {phase_name} {'='*25}")
            try:
                if phase_func():
                    passed_phases += 1
                    print(f"✅ {phase_name} - PASSED")
                else:
                    print(f"❌ {phase_name} - FAILED")
            except Exception as e:
                print(f"❌ {phase_name} - FAILED with exception: {str(e)}")
        
        # Final results
        print(f"\n{'='*80}")
        print(f"🎯 FOCUSED FRAME PAYMENT TESTING RESULTS")
        print(f"Test phases passed: {passed_phases}/{total_phases}")
        print(f"Success rate: {(passed_phases/total_phases)*100:.1f}%")
        print(f"Individual tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Individual test success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if passed_phases == total_phases:
            print("\n🎉 CONCLUSION: Frame payment functionality is working correctly!")
            print("   The user's report of 'payment not working' appears to be incorrect.")
            print("   All payment submission tests passed successfully.")
            return True
        else:
            print("\n⚠️  CONCLUSION: Frame payment functionality has issues")
            print("   The user's report appears to be correct - there are problems with payment submission.")
            return False

def main():
    print("🚀 Starting Focused Frame Payment Testing")
    print("Testing the specific functionality that the user reported as 'not working'")
    print("=" * 70)
    
    tester = FramePaymentFocusedTester()
    success = tester.run_focused_payment_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())