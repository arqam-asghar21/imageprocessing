#!/usr/bin/env python3
import sys
import os
import requests
import json

# Add the imageprocessing directory to the path
sys.path.append('imageprocessing')

try:
    from imageprocessing.main import app
    print("✅ Backend imports successfully!")
    print("✅ FastAPI app created successfully!")
    print("✅ Ready to start server with: uvicorn imageprocessing.main:app --host 0.0.0.0 --port 8000")
except Exception as e:
    print(f"❌ Error importing backend: {e}")
    import traceback
    traceback.print_exc() 

def test_backend():
    """Test the backend endpoints to identify issues"""
    
    print("🔍 Testing backend endpoints...")
    
    # Test 1: Check if backend is running
    print("\n1. Testing backend connection...")
    try:
        response = requests.get('http://localhost:8000/')
        if response.status_code == 200:
            print("✅ Backend is running")
            print(f"   Response: {response.text[:200]}...")
        else:
            print(f"❌ Backend error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False
    
    # Test 2: Check database status
    print("\n2. Testing database...")
    try:
        response = requests.get('http://localhost:8000/api/images/')
        if response.status_code == 200:
            images = response.json()
            print(f"✅ Database accessible - {len(images)} images")
        else:
            print(f"❌ Database error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # Test 3: Check PDF processing endpoint
    print("\n3. Testing PDF processing...")
    try:
        response = requests.post('http://localhost:8000/process-all/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF processing successful")
            print(f"   Result: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ PDF processing failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ PDF processing error: {e}")
    
    return True

if __name__ == "__main__":
    test_backend() 