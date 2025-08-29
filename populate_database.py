import requests
import json

def populate_database():
    """Populate the backend database with extracted images"""
    
    # First, process all PDFs
    print("🔄 Processing all PDFs...")
    try:
        response = requests.post('http://localhost:8000/process-all/')
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF processing completed")
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error processing PDFs: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Then, get all images from database
    print("\n📊 Checking database contents...")
    try:
        response = requests.get('http://localhost:8000/api/images/')
        if response.status_code == 200:
            images = response.json()
            print(f"✅ Database contains {len(images)} images:")
            for img in images:
                print(f"  - {img.get('business_name', 'Unknown')} ({img.get('pdf_filename', 'Unknown')})")
        else:
            print(f"❌ Error getting images: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    populate_database() 