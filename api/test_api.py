"""
Test script for the FastAPI endpoints.
"""

import requests
import json

def test_health_check():
    """Test the health check endpoint."""
    try:
        response = requests.get("http://localhost:8000/api/v1/health")
        print(f"Health Check Status: {response.status_code}")
        print(f"Health Check Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return False

def test_shop_endpoint():
    """Test the shop endpoint."""
    try:
        payload = {
            "query": "I want a gaming laptop under $1500",
            "session_id": "test-session-123"
        }
        response = requests.post("http://localhost:8000/api/v1/shop", json=payload)
        print(f"Shop Endpoint Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Shop Result: {json.dumps(result, indent=2)}")
        else:
            print(f"Shop Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Shop Endpoint Failed: {e}")
        return False

def test_status_endpoint():
    """Test the status endpoint."""
    try:
        response = requests.get("http://localhost:8000/api/v1/status")
        print(f"Status Endpoint Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Status Result: {json.dumps(result, indent=2)}")
        else:
            print(f"Status Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Status Endpoint Failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing FastAPI Endpoints...")
    print("=" * 50)
    
    # Test health check first
    health_ok = test_health_check()
    print()
    
    if health_ok:
        # Test status endpoint
        status_ok = test_status_endpoint()
        print()
        
        # Test shop endpoint
        shop_ok = test_shop_endpoint()
        print()
        
        if shop_ok:
            print("✅ All tests passed!")
        else:
            print("❌ Shop endpoint test failed")
    else:
        print("❌ Health check failed - server may not be ready")