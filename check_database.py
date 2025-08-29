import requests
import json

def check_database():
    """Check the current database contents"""
    
    print("📊 Checking database contents...")
    
    try:
        response = requests.get('http://localhost:8000/api/images/')
        if response.status_code == 200:
            images = response.json()
            print(f"✅ Database contains {len(images)} images:")
            
            for i, img in enumerate(images, 1):
                business_name = img.get('business_name', 'Unknown')
                pdf_name = img.get('pdf_filename', 'Unknown')
                image_path = img.get('image_path', 'Unknown')
                print(f"   {i:2d}. {business_name}")
                print(f"       PDF: {pdf_name}")
                print(f"       Image: {image_path}")
                print()
            
            print(f"🎉 Database is ready with {len(images)} images!")
            return True
        else:
            print(f"❌ Error getting images: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_database() 