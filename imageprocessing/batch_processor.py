import os
import fitz
from datetime import datetime
import sys
sys.path.append('.')

from models import ExtractedImage
from database import SessionLocal, engine, Base
from utils.pdf_utils import extract_images_from_pdf

def process_all_pdfs():
    """Process all PDFs in the pdfs folder and extract images"""
    pdf_dir = "pdfs/"
    image_dir = "extracted_images/"
    
    # Create directories if they don't exist
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in pdfs/ folder")
        return
    
    db = SessionLocal()
    total_images = 0
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        print(f"Processing: {pdf_file}")
        
        try:
            # Extract images from PDF
            images_info = extract_images_from_pdf(pdf_path, image_dir)
            
            # Generate business info from filename
            business_name = os.path.splitext(pdf_file)[0].replace('_', ' ').title()
            business_reference = os.path.splitext(pdf_file)[0].upper()
            
            # Store each image in database
            for info in images_info:
                image_record = ExtractedImage(
                    image_path=info["image_path"],
                    pdf_filename=pdf_file,
                    page_number=info["page_number"],
                    tags="logo, extracted",
                    image_type="logo",
                    business_name=business_name,
                    business_reference=business_reference,
                    uploaded_at=datetime.utcnow()
                )
                db.add(image_record)
                total_images += 1
                print(f"  - Extracted image: {os.path.basename(info['image_path'])}")
            
            db.commit()
            print(f"  ✓ Successfully processed {len(images_info)} image(s)")
            
        except Exception as e:
            print(f"  ✗ Error processing {pdf_file}: {str(e)}")
            db.rollback()
    
    db.close()
    print(f"\nBatch processing complete! Total images extracted: {total_images}")

if __name__ == "__main__":
    # Create database tables
    Base.metadata.create_all(bind=engine)
    process_all_pdfs() 