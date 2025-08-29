import requests
import json

def setup_database():
    """Set up the backend database with extracted images"""
    
    print("🔄 Setting up database...")
    
    # Step 1: Process all PDFs
    print("📄 Processing PDFs...")
    try:
        response = requests.post('http://localhost:8000/process-all/')
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF processing completed")
            print(f"   - Processed: {result.get('processed_files', 0)} files")
            print(f"   - Extracted: {result.get('total_images', 0)} images")
        else:
            print(f"❌ Error processing PDFs: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Step 2: Check database contents
    print("\n📊 Checking database...")
    try:
        response = requests.get('http://localhost:8000/api/images/')
        if response.status_code == 200:
            images = response.json()
            print(f"✅ Database contains {len(images)} images:")
            for img in images:
                business_name = img.get('business_name', 'Unknown')
                pdf_name = img.get('pdf_filename', 'Unknown')
                print(f"   - {business_name} ({pdf_name})")
        else:
            print(f"❌ Error getting images: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n🎉 Database setup completed successfully!")
    return True

if __name__ == "__main__":
    setup_database() 