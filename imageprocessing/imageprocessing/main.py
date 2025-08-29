from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from utils.pdf_utils import extract_images_from_pdf
from models import ExtractedImage
from database import SessionLocal, engine, Base
import shutil, os
from datetime import datetime
import glob
from PIL import Image
import io
import numpy as np
from typing import Optional

UPLOAD_DIR = "pdfs/"
IMAGE_DIR = "extracted_images/"

app = FastAPI(title="PDF Image Extraction API", description="API for extracting images from PDFs")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Mount static files for images
app.mount("/images", StaticFiles(directory=IMAGE_DIR), name="images")

# Mount static files for web app
app.mount("/static", StaticFiles(directory="../web_app"), name="static")

def calculate_image_similarity(img1: Image.Image, img2: Image.Image) -> float:
    """Calculate similarity between two images using basic pixel comparison"""
    try:
        # Resize images to same size for comparison
        size = (100, 100)
        img1_resized = img1.resize(size)
        img2_resized = img2.resize(size)
        
        # Convert to grayscale and numpy arrays
        img1_array = np.array(img1_resized.convert('L'))
        img2_array = np.array(img2_resized.convert('L'))
        
        # Calculate mean squared error
        mse = np.mean((img1_array - img2_array) ** 2)
        
        # Convert to similarity score (0-1, where 1 is identical)
        max_mse = 255 ** 2
        similarity = 1 - (mse / max_mse)
        
        return max(0, similarity)
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0

@app.post("/match-image/")
async def match_image(image: UploadFile = File(...)):
    """Match uploaded image against stored images"""
    try:
        # Read uploaded image
        image_data = await image.read()
        uploaded_img = Image.open(io.BytesIO(image_data))
        
        # Get all stored images
        db = SessionLocal()
        stored_images = db.query(ExtractedImage).all()
        db.close()
        
        best_match = None
        best_similarity = 0.0
        threshold = 0.7  # Minimum similarity threshold
        
        for stored_img in stored_images:
            try:
                # Load stored image
                if os.path.exists(stored_img.image_path):
                    stored_image = Image.open(stored_img.image_path)
                    
                    # Calculate similarity
                    similarity = calculate_image_similarity(uploaded_img, stored_image)
                    
                    if similarity > best_similarity and similarity >= threshold:
                        best_similarity = similarity
                        best_match = stored_img
                        
            except Exception as e:
                print(f"Error processing stored image {stored_img.image_path}: {e}")
                continue
        
        if best_match:
            return {
                "id": best_match.id,
                "image_path": best_match.image_path,
                "pdf_filename": best_match.pdf_filename,
                "page_number": best_match.page_number,
                "tags": best_match.tags,
                "image_type": best_match.image_type,
                "business_name": best_match.business_name,
                "business_reference": best_match.business_reference,
                "uploaded_at": best_match.uploaded_at.isoformat() if best_match.uploaded_at else None,
                "match_confidence": best_similarity
            }
        else:
            return {"error": "No match found"}
            
    except Exception as e:
        return {"error": f"Error processing image: {str(e)}"}

@app.post("/upload/")
async def upload_pdf(
    file: UploadFile = File(...),
    business_name: str = Form(...),
    business_reference: str = Form(...),
    tags: str = Form(""),
    image_type: str = Form("logo")
):
    """Upload a PDF and extract images"""
    db = SessionLocal()
    
    pdf_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    images_info = extract_images_from_pdf(pdf_path, IMAGE_DIR)

    for info in images_info:
        image_record = ExtractedImage(
            image_path=info["image_path"],
            pdf_filename=file.filename,
            page_number=info["page_number"],
            tags=tags,
            image_type=image_type,
            business_name=business_name,
            business_reference=business_reference,
            uploaded_at=datetime.utcnow()
        )
        db.add(image_record)
    db.commit()
    db.close()

    return {"message": f"{len(images_info)} image(s) extracted and stored."}

@app.post("/process-all/")
async def process_all_pdfs():
    """Process all PDFs in the pdfs folder"""
    from imageprocessing.batch_processor import process_all_pdfs
    process_all_pdfs()
    return {"message": "All PDFs processed successfully"}

@app.get("/api/images/")
async def get_images():
    """API endpoint to get all extracted images"""
    db = SessionLocal()
    images = db.query(ExtractedImage).all()
    db.close()
    
    return [
        {
            "id": img.id,
            "image_path": img.image_path,
            "pdf_filename": img.pdf_filename,
            "page_number": img.page_number,
            "tags": img.tags,
            "image_type": img.image_type,
            "business_name": img.business_name,
            "business_reference": img.business_reference,
            "uploaded_at": img.uploaded_at.isoformat() if img.uploaded_at else None
        }
        for img in images
    ]

@app.get("/api/images/{image_id}/")
async def get_image_by_id(image_id: int):
    """Get specific image by ID"""
    db = SessionLocal()
    image = db.query(ExtractedImage).filter(ExtractedImage.id == image_id).first()
    db.close()
    
    if image:
        return {
            "id": image.id,
            "image_path": image.image_path,
            "pdf_filename": image.pdf_filename,
            "page_number": image.page_number,
            "tags": image.tags,
            "image_type": image.image_type,
            "business_name": image.business_name,
            "business_reference": image.business_reference,
            "uploaded_at": image.uploaded_at.isoformat() if image.uploaded_at else None
        }
    else:
        return {"error": "Image not found"}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web application"""
    try:
        with open("../web_app/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Web app files not found</h1>", status_code=404)

@app.get("/app.js")
async def serve_app_js():
    """Serve the JavaScript file"""
    try:
        with open("../web_app/app.js", "r", encoding="utf-8") as f:
            js_content = f.read()
        return HTMLResponse(content=js_content, media_type="application/javascript")
    except FileNotFoundError:
        return HTMLResponse(content="// File not found", status_code=404)

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "PDF Image Extraction API",
        "endpoints": {
            "upload": "POST /upload/ - Upload PDF and extract images",
            "process_all": "POST /process-all/ - Process all PDFs in folder",
            "get_images": "GET /api/images/ - Get all extracted images",
            "match_image": "POST /match-image/ - Match uploaded image against database",
            "get_image_by_id": "GET /api/images/{id}/ - Get specific image by ID"
        }
    } 