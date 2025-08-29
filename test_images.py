import requests
import json

def test_images():
    """Test if images are accessible from the backend"""
    
    print("🖼️ Testing image accessibility...")
    
    # Get list of images from database
    try:
        response = requests.get('http://localhost:8000/api/images/')
        if response.status_code == 200:
            images = response.json()
            print(f"✅ Found {len(images)} images in database")
            
            # Test first few images
            for i, img in enumerate(images[:3]):
                image_path = img.get('image_path', '')
                image_filename = image_path.split('/')[-1] if '/' in image_path else image_path
                image_url = f'http://localhost:8000/images/{image_filename}'
                
                print(f"\n📸 Testing image {i+1}: {image_filename}")
                print(f"   URL: {image_url}")
                
                try:
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        size_kb = len(img_response.content) / 1024
                        print(f"   ✅ Accessible ({size_kb:.1f} KB)")
                    else:
                        print(f"   ❌ Not accessible ({img_response.status_code})")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            print(f"\n🎉 Image testing completed!")
            return True
        else:
            print(f"❌ Error getting images: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_images() 