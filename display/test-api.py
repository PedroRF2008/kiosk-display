#!/usr/bin/env python3
"""
Simple API test script to verify the endpoints work
"""

import requests
import sys
import time

def test_endpoint(url, name):
    """Test a single endpoint"""
    try:
        print(f"Testing {name}...")
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

def main():
    print("🧪 Testing Flask API Endpoints")
    print("="*40)

    base_url = "http://localhost:5000"

    # Test if Flask server is running
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print("✅ Flask server is responding")
    except Exception as e:
        print(f"❌ Flask server not accessible: {e}")
        print("Make sure Flask is running on localhost:5000")
        sys.exit(1)

    # Test API endpoints
    endpoints = [
        ("/api/v1/display", "Display Data"),
        ("/api/v1/weather", "Weather Data"),
        ("/api/v1/birthdays", "Birthday Data"),
        ("/api/v1/media", "Media Data"),
    ]

    results = []
    for endpoint, name in endpoints:
        url = f"{base_url}{endpoint}"
        success = test_endpoint(url, name)
        results.append((name, success))

    print("\n📊 Results:")
    print("="*40)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:<15} {status}")

    # Summary
    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("🎉 All API endpoints working!")
    else:
        print("⚠️  Some endpoints failed - check your configuration")

if __name__ == "__main__":
    main()