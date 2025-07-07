import requests
import unittest
import json
import os
import sys
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://cf949044-8d90-433e-9ba9-2de4baf6fbdc.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class FinanceSpaceAPITester(unittest.TestCase):
    """Test suite for FinanceSpace API endpoints"""
    
    def test_01_health_check(self):
        """Test the API health check endpoint"""
        print("\n🔍 Testing API health check...")
        response = requests.get(f"{API_URL}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        print(f"✅ API health check passed: {data['message']}")
    
    def test_02_ai_query(self):
        """Test the AI query endpoint"""
        print("\n🔍 Testing AI query endpoint...")
        payload = {
            "query": "What is compound interest?",
            "type": "general"
        }
        response = requests.post(f"{API_URL}/query", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIn("id", data)
        self.assertEqual(data["query"], payload["query"])
        self.assertEqual(data["type"], "general")
        print(f"✅ AI query test passed")
        print(f"Query: {data['query']}")
        print(f"Response snippet: {data['response'][:100]}...")
    
    def test_03_search_query(self):
        """Test the search endpoint"""
        print("\n🔍 Testing search endpoint...")
        payload = {
            "query": "latest stock market trends",
            "type": "search"
        }
        response = requests.post(f"{API_URL}/search", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertIn("id", data)
        self.assertEqual(data["query"], payload["query"])
        self.assertTrue(len(data["results"]) > 0, "Search returned no results")
        print(f"✅ Search query test passed")
        print(f"Query: {data['query']}")
        print(f"Found {len(data['results'])} search results")
    
    def test_04_combined_query(self):
        """Test the combined search + AI endpoint"""
        print("\n🔍 Testing combined search + AI endpoint...")
        payload = {
            "query": "Mars exploration 2024",
            "type": "combined"
        }
        response = requests.post(f"{API_URL}/combined", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("search_results", data)
        self.assertIn("ai_summary", data)
        self.assertIn("id", data)
        self.assertEqual(data["query"], payload["query"])
        self.assertTrue(len(data["search_results"]) > 0, "Combined search returned no results")
        self.assertTrue(len(data["ai_summary"]) > 0, "AI summary is empty")
        print(f"✅ Combined query test passed")
        print(f"Query: {data['query']}")
        print(f"Found {len(data['search_results'])} search results")
        print(f"AI summary snippet: {data['ai_summary'][:100]}...")
    
    def test_05_history_retrieval(self):
        """Test the history retrieval endpoint"""
        print("\n🔍 Testing history retrieval endpoint...")
        response = requests.get(f"{API_URL}/history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            self.assertIn("query", data[0])
            self.assertIn("response", data[0])
            self.assertIn("type", data[0])
            self.assertIn("id", data[0])
            print(f"✅ History retrieval test passed")
            print(f"Retrieved {len(data)} history items")
            if len(data) > 0:
                print(f"Latest query: {data[0]['query']}")
        else:
            print("⚠️ History is empty, but endpoint works")
    
    def test_06_status_check(self):
        """Test the status check endpoints"""
        print("\n🔍 Testing status check endpoints...")
        
        # Test POST status
        client_name = f"test_client_{datetime.now().strftime('%H%M%S')}"
        payload = {
            "client_name": client_name
        }
        post_response = requests.post(f"{API_URL}/status", json=payload)
        self.assertEqual(post_response.status_code, 200)
        post_data = post_response.json()
        self.assertEqual(post_data["client_name"], client_name)
        self.assertIn("id", post_data)
        
        # Test GET status
        get_response = requests.get(f"{API_URL}/status")
        self.assertEqual(get_response.status_code, 200)
        get_data = get_response.json()
        self.assertIsInstance(get_data, list)
        
        # Check if our posted status is in the list
        found = False
        for status in get_data:
            if status.get("client_name") == client_name:
                found = True
                break
        
        self.assertTrue(found, "Posted status not found in status list")
        print(f"✅ Status check endpoints test passed")
        print(f"Created status for client: {client_name}")
        print(f"Retrieved {len(get_data)} status items")
    
    def test_07_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n🔍 Testing error handling...")
        
        # Test with empty query
        payload = {
            "query": "",
            "type": "general"
        }
        response = requests.post(f"{API_URL}/query", json=payload)
        # The API might return 200 with an error message or a 4xx status
        if response.status_code >= 400:
            print(f"✅ Empty query correctly rejected with status {response.status_code}")
        else:
            data = response.json()
            # Check if there's an error message in the response
            if "error" in data:
                print(f"✅ Empty query handled with error message: {data['error']}")
            else:
                print("⚠️ Empty query accepted without error")
        
        # Test with invalid endpoint
        response = requests.get(f"{API_URL}/nonexistent")
        self.assertGreaterEqual(response.status_code, 400)
        print(f"✅ Invalid endpoint correctly rejected with status {response.status_code}")

def run_tests():
    """Run all tests and print summary"""
    test_suite = unittest.TestLoader().loadTestsFromTestCase(FinanceSpaceAPITester)
    test_result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    print("\n" + "="*50)
    print(f"SUMMARY: Ran {test_result.testsRun} tests")
    print(f"✅ Passed: {test_result.testsRun - len(test_result.failures) - len(test_result.errors)}")
    print(f"❌ Failed: {len(test_result.failures)}")
    print(f"❌ Errors: {len(test_result.errors)}")
    print("="*50)
    
    return len(test_result.failures) + len(test_result.errors)

if __name__ == "__main__":
    print("="*50)
    print("FinanceSpace API Test Suite")
    print("="*50)
    sys.exit(run_tests())