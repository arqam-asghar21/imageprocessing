import requests
import socket

def test_backend_connection():
    """Test if the backend is accessible from the network"""
    
    # Get local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Local IP: {local_ip}")
    
    # Test URLs
    test_urls = [
        f"http://{local_ip}:8000/",
        "http://localhost:8000/",
        "http://127.0.0.1:8000/"
    ]
    
    for url in test_urls:
        try:
            print(f"Testing: {url}")
            response = requests.get(url, timeout=5)
            print(f"✅ Success: {url} - Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ Failed: {url} - Error: {e}")
        print()

if __name__ == "__main__":
    test_backend_connection() 