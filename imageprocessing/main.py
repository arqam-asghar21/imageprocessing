from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from utils.pdf_utils import extract_images_from_pdf
from models import ExtractedImage, Business, DEXContent
from database import SessionLocal, engine, Base, get_db
from auth import get_db as auth_get_db
from business_api import router as business_api_router
from auth_api import router as auth_api_router
import shutil, os
from datetime import datetime
import glob
from PIL import Image
import io
import numpy as np
from typing import Optional
import json

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
app.mount("/static", StaticFiles(directory="web_app"), name="static")

# Include API routers
app.include_router(business_api_router)
app.include_router(auth_api_router)

def calculate_image_similarity(img1: Image.Image, img2: Image.Image) -> float:
    """Calculate similarity between two images using improved comparison"""
    try:
        # Resize images to same size for comparison
        size = (64, 64)  # Smaller size for faster processing
        img1_resized = img1.resize(size)
        img2_resized = img2.resize(size)
        
        # Convert to grayscale and numpy arrays
        img1_array = np.array(img1_resized.convert('L'))
        img2_array = np.array(img2_resized.convert('L'))
        
        # Calculate multiple similarity metrics
        
        # 1. Mean Squared Error (MSE)
        mse = np.mean((img1_array - img2_array) ** 2)
        max_mse = 255 ** 2
        mse_similarity = 1 - (mse / max_mse)
        
        # 2. Structural Similarity Index (SSIM-like)
        # Calculate local means
        kernel_size = 8
        img1_mean = np.mean(img1_array)
        img2_mean = np.mean(img2_array)
        
        # Calculate local variances
        img1_var = np.var(img1_array)
        img2_var = np.var(img2_array)
        
        # Calculate cross-correlation
        img1_centered = img1_array - img1_mean
        img2_centered = img2_array - img2_mean
        cross_corr = np.mean(img1_centered * img2_centered)
        
        # SSIM-like score
        if img1_var + img2_var == 0:
            ssim_similarity = 1.0 if np.allclose(img1_array, img2_array) else 0.0
        else:
            ssim_similarity = (2 * cross_corr + 0.01) / (img1_var + img2_var + 0.01)
            ssim_similarity = max(0, min(1, ssim_similarity))  # Clamp to [0,1]
        
        # 3. Histogram comparison
        hist1, _ = np.histogram(img1_array, bins=32, range=(0, 256))
        hist2, _ = np.histogram(img2_array, bins=32, range=(0, 256))
        
        # Normalize histograms
        hist1 = hist1 / np.sum(hist1)
        hist2 = hist2 / np.sum(hist2)
        
        # Calculate histogram intersection
        hist_similarity = np.sum(np.minimum(hist1, hist2))
        
        # 4. Edge detection comparison (fallback if scipy not available)
        try:
            from scipy import ndimage
            # Apply Sobel edge detection
            img1_edges = ndimage.sobel(img1_array)
            img2_edges = ndimage.sobel(img2_array)
            
            # Compare edge patterns
            edge_diff = np.mean(np.abs(img1_edges - img2_edges))
            edge_similarity = 1 - (edge_diff / 255)
            edge_similarity = max(0, edge_similarity)
        except ImportError:
            # Fallback: simple gradient comparison
            img1_grad = np.gradient(img1_array)
            img2_grad = np.gradient(img2_array)
            
            grad_diff = np.mean(np.abs(img1_grad[0] - img2_grad[0])) + np.mean(np.abs(img1_grad[1] - img2_grad[1]))
            edge_similarity = 1 - (grad_diff / 510)
            edge_similarity = max(0, edge_similarity)
        
        # Combine all metrics with weights
        final_similarity = (
            0.3 * mse_similarity +
            0.3 * ssim_similarity +
            0.2 * hist_similarity +
            0.2 * edge_similarity
        )
        
        return max(0, min(1, final_similarity))
        
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
        
        # Get all stored images (removed is_public filter for now)
        db = SessionLocal()
        stored_images = db.query(ExtractedImage).all()
        db.close()
        
        best_match = None
        best_similarity = 0.0
        threshold = 0.7  # Higher threshold for more accurate matching
        
        print(f"Processing {len(stored_images)} stored images...")
        
        # Add some randomization to avoid false positives
        import random
        random.seed(42)  # Fixed seed for reproducibility
        
        for stored_img in stored_images:
            try:
                # Load stored image
                if os.path.exists(stored_img.image_path):
                    stored_image = Image.open(stored_img.image_path)
                    
                    # Calculate similarity
                    similarity = calculate_image_similarity(uploaded_img, stored_image)
                    
                    # Add small random noise to break ties and avoid false positives
                    noise = random.uniform(-0.01, 0.01)
                    similarity += noise
                    similarity = max(0, min(1, similarity))
                    
                    print(f"Image {stored_img.image_path}: similarity = {similarity:.3f}")
                    
                    if similarity > best_similarity and similarity >= threshold:
                        best_similarity = similarity
                        best_match = stored_img
                        print(f"New best match: {stored_img.image_path} with similarity {similarity:.3f}")
                        
            except Exception as e:
                print(f"Error processing stored image {stored_img.image_path}: {e}")
                continue
        
        if best_match:
            # Check if similarity is suspiciously high (might be the same image)
            if best_similarity > 0.95:
                print(f"⚠️ Warning: Very high similarity ({best_similarity:.3f}) - possible duplicate image")
            
            # Get DEX content for the matched image
            db = SessionLocal()
            dex_content = db.query(DEXContent).filter(
                DEXContent.image_id == best_match.id,
                DEXContent.is_active == True
            ).first()
            db.close()
            
            response = {
                "match_found": True,
                "similarity_score": best_similarity,
                "match_confidence": best_similarity,
                "image_path": best_match.image_path,
                "business_name": best_match.business_name,
                "pdf_filename": best_match.pdf_filename,
                "page_number": best_match.page_number,
                "tags": best_match.tags,
                "image_type": best_match.image_type,
                "business_reference": best_match.business_reference,
                "print_design_id": best_match.print_design_id,
                "match_quality": "high" if best_similarity > 0.8 else "medium" if best_similarity > 0.6 else "low"
            }
            
            # Add DEX content if available with enhanced delivery options
            if dex_content:
                response["dex_content"] = {
                    "id": dex_content.id,
                    "title": dex_content.title,
                    "description": dex_content.description,
                    "content_type": dex_content.content_type,
                    "content_url": dex_content.content_url,
                    "content_data": dex_content.content_data,
                    "delivery_options": {
                        "ar_enabled": dex_content.content_type in ["ar", "3d_model"],
                        "video_available": dex_content.content_type == "video",
                        "webpage_available": dex_content.content_url is not None,
                        "direct_link": f"/dex/deliver/{dex_content.id}",
                        "ar_link": f"/dex/ar/{dex_content.id}" if dex_content.content_type in ["ar", "3d_model"] else None,
                        "qr_code": f"/dex/qr/{dex_content.id}"
                    }
                }
            else:
                # Provide fallback DEX options even without specific content
                response["dex_content"] = {
                    "id": None,
                    "title": f"Learn more about {best_match.business_name}",
                    "description": f"Discover more about this {best_match.image_type} from {best_match.business_name}",
                    "content_type": "webpage",
                    "content_url": f"/business/{best_match.business_reference}",
                    "content_data": None,
                    "delivery_options": {
                        "ar_enabled": False,
                        "video_available": False,
                        "webpage_available": True,
                        "direct_link": f"/business/{best_match.business_reference}",
                        "ar_link": None,
                        "qr_code": f"/dex/qr/business/{best_match.business_reference}"
                    }
                }
            
            return response
        else:
            return {
                "match_found": False,
                "message": "No match found above threshold"
            }
            
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
        with open("web_app/index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Web app files not found</h1>", status_code=404)

@app.get("/app.js")
async def serve_app_js():
    """Serve the JavaScript file"""
    try:
        with open("web_app/app.js", "r", encoding="utf-8") as f:
            js_content = f.read()
        return HTMLResponse(content=js_content, media_type="application/javascript")
    except FileNotFoundError:
        return HTMLResponse(content="// File not found", status_code=404)

@app.get("/dex/{dex_id}")
async def deliver_dex(dex_id: int):
    """Deliver DEX content based on content type"""
    db = SessionLocal()
    dex_content = db.query(DEXContent).filter(
        DEXContent.id == dex_id,
        DEXContent.is_active == True
    ).first()
    db.close()
    
    if not dex_content:
        raise HTTPException(status_code=404, detail="DEX content not found")
    
    # Handle different content types
    if dex_content.content_type == "link":
        return RedirectResponse(url=dex_content.content_url)
    elif dex_content.content_type == "webpage":
        return RedirectResponse(url=dex_content.content_url)
    elif dex_content.content_type == "video":
        return RedirectResponse(url=dex_content.content_url)
    elif dex_content.content_type == "ar":
        # For AR content, return the content data
        return {
            "type": "ar",
            "title": dex_content.title,
            "description": dex_content.description,
            "content_data": dex_content.content_data,
            "content_url": dex_content.content_url
        }
    else:
        return {
            "type": "unknown",
            "title": dex_content.title,
            "description": dex_content.description,
            "content_url": dex_content.content_url
        }

@app.post("/upload-pdf/")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    business_name: str = Form(...),
    business_reference: str = Form(""),
    tags: str = Form(""),
    image_type: str = Form("logo")
):
    """Upload and process PDF file"""
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded file temporarily
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create output directory for extracted images
        output_dir = os.path.join(IMAGE_DIR, business_reference or business_name.lower().replace(" ", "_"))
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract images from PDF using the correct function signature
        extracted_images_info = extract_images_from_pdf(temp_file_path, output_dir)
        
        # Store extracted images in database
        db = SessionLocal()
        stored_images = []
        
        try:
            for img_info in extracted_images_info:
                # Create new ExtractedImage record
                new_image = ExtractedImage(
                    business_name=business_name,
                    business_reference=business_reference or business_name.lower().replace(" ", "_"),
                    pdf_filename=file.filename,
                    image_path=img_info["image_path"],
                    page_number=img_info["page_number"],
                    tags=tags,
                    image_type=image_type,
                    is_public=True
                )
                db.add(new_image)
                stored_images.append(new_image)
            
            db.commit()
            
            # Get the stored images with IDs
            for img in stored_images:
                db.refresh(img)
            
        except Exception as db_error:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        finally:
            db.close()
        
        # Also store in user uploads if user is authenticated
        try:
            # Try to get user from request headers
            from auth_api import verify_token
            from models import User, UserUpload, UserActivity
            import json
            
            # Get user from Authorization header
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    # Decode token to get user ID
                    import jwt
                    payload = jwt.decode(token, "your-secret-key-here", algorithms=["HS256"])
                    user_id = int(payload.get("sub"))
                    
                    # Get user from database
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        # Create user upload records for each extracted image
                        for img_info in extracted_images_info:
                            # Create a user upload record for the extracted image
                            user_upload = UserUpload(
                                user_id=user_id,
                                filename=f"{file.filename}_page{img_info['page_number']}.png",
                                file_path=img_info["image_path"],
                                content_type="image",
                                tags=f"PDF: {file.filename}, Page: {img_info['page_number']}, {tags}"
                            )
                            db.add(user_upload)
                        
                        # Log activity
                        activity = UserActivity(
                            user_id=user_id,
                            activity_type="upload",
                            title="PDF Processed",
                            description=f"PDF '{file.filename}' processed, {len(extracted_images_info)} images extracted",
                            activity_data=json.dumps({
                                "pdf_filename": file.filename,
                                "extracted_images": len(extracted_images_info),
                                "tags": tags
                            })
                        )
                        db.add(activity)
                        
                        db.commit()
                        print(f"✅ User upload records created for user {user_id}")
                        
                except Exception as user_error:
                    print(f"⚠️ Could not create user upload records: {user_error}")
                    # Continue without user uploads - this is not critical
                    
        except Exception as user_upload_error:
            print(f"⚠️ Error in user upload creation: {user_upload_error}")
            # This is not critical, continue with the main functionality
        
        # Clean up temporary PDF file
        os.remove(temp_file_path)
        
        return {
            "message": "PDF processed successfully",
            "filename": file.filename,
            "business_name": business_name,
            "business_reference": business_reference or business_name.lower().replace(" ", "_"),
            "extracted_images": len(extracted_images_info),
            "stored_images": [
                {
                    "id": img.id,
                    "image_path": img.image_path,
                    "page_number": img.page_number
                } for img in stored_images
            ]
        }
        
    except Exception as e:
        # Clean up if there's an error
        temp_file_path = os.path.join(UPLOAD_DIR, file.filename)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "PDF Image Extraction API with DEX Delivery",
        "endpoints": {
            "upload_pdf": "POST /upload-pdf/ - Upload PDF and extract images",
            "upload": "POST /upload/ - Upload PDF and extract images",
            "process_all": "POST /process-all/ - Process all PDFs in folder",
            "get_images": "GET /api/images/ - Get all extracted images",
            "match_image": "POST /match-image/ - Match uploaded image against database",
            "get_image_by_id": "GET /api/images/{id}/ - Get specific image by ID",
            "dex_delivery": "GET /dex/{id} - Deliver DEX content",
            "third_party_api": "GET /docs - Third-party API documentation"
        }
    }

@app.get("/test-match")
async def test_match():
    """Test endpoint to check if matching logic works"""
    try:
        db = SessionLocal()
        image_count = db.query(ExtractedImage).count()
        db.close()
        
        return {
            "status": "ok",
            "database_images": image_count,
            "message": f"Database contains {image_count} images for matching"
        }
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}

@app.get("/debug-similarity")
async def debug_similarity():
    """Debug endpoint to test similarity calculation with sample images"""
    try:
        # Get first two images from database for testing
        db = SessionLocal()
        images = db.query(ExtractedImage).limit(2).all()
        db.close()
        
        if len(images) < 2:
            return {"error": "Need at least 2 images in database for testing"}
        
        # Load the images
        img1 = Image.open(images[0].image_path)
        img2 = Image.open(images[1].image_path)
        
        # Calculate similarity
        similarity = calculate_image_similarity(img1, img2)
        
        return {
            "image1": images[0].image_path,
            "image2": images[1].image_path,
            "similarity": similarity,
            "message": f"Similarity between {images[0].pdf_filename} and {images[1].pdf_filename}: {similarity:.3f}"
        }
        
    except Exception as e:
        return {"error": f"Debug error: {str(e)}"}

# Debug endpoint to test authentication
@app.get("/debug-auth")
async def debug_auth(request: Request):
    """Debug endpoint to test authentication"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return {"error": "No X-API-Key header found"}
    
    db = SessionLocal()
    try:
        business = db.query(Business).filter(
            Business.api_key == api_key,
            Business.is_active == True
        ).first()
        
        if business:
            return {
                "success": True,
                "business_name": business.name,
                "api_key_found": True,
                "business_active": business.is_active
            }
        else:
            return {
                "success": False,
                "api_key_found": False,
                "error": "No business found with this API key or business is inactive"
            }
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}
    finally:
        db.close()

# ===== AUTHENTICATION ROUTES =====

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page"""
    try:
        with open("web_app/login.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Login page not found</h1>", status_code=404)

@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    """Serve the signup page"""
    try:
        with open("web_app/signup.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Signup page not found</h1>", status_code=404)

@app.get("/dashboard", response_class=HTMLResponse)
async def user_dashboard():
    """Serve the user dashboard"""
    try:
        with open("web_app/dashboard.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)

# ===== USER UPLOADS ROUTES =====

@app.get("/user_uploads/{user_id}/{filename}")
async def serve_user_upload(user_id: str, filename: str):
    """Serve user uploaded files"""
    try:
        file_path = f"user_uploads/{user_id}/{filename}"
        if os.path.exists(file_path):
            return FileResponse(file_path)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")

# ===== BUSINESS DASHBOARD ROUTES =====

@app.get("/business-dashboard", response_class=HTMLResponse)
async def business_dashboard():
    """Serve the business dashboard"""
    try:
        with open("web_app/business-dashboard.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Business dashboard not found</h1>", status_code=404)

@app.get("/dashboard.js")
async def serve_dashboard_js():
    """Serve the dashboard JavaScript file"""
    try:
        with open("web_app/dashboard.js", "r", encoding="utf-8") as f:
            js_content = f.read()
        return Response(content=js_content, media_type="application/javascript")
    except FileNotFoundError:
        return Response(content="// Dashboard JS not found", status_code=404, media_type="application/javascript")

@app.get("/business-dashboard.js")
async def serve_business_dashboard_js():
    """Serve the business dashboard JavaScript file"""
    try:
        with open("web_app/business-dashboard.js", "r", encoding="utf-8") as f:
            js_content = f.read()
        return Response(content=js_content, media_type="application/javascript")
    except FileNotFoundError:
        return Response(content="// Business dashboard JS not found", status_code=404, media_type="application/javascript")

# ===== DEX DELIVERY ENDPOINTS =====

@app.get("/dex/deliver/{dex_id}")
async def deliver_dex(dex_id: int):
    """Deliver DEX content based on type"""
    try:
        db = SessionLocal()
        dex_content = db.query(DEXContent).filter(DEXContent.id == dex_id).first()
        db.close()
        
        if not dex_content:
            raise HTTPException(status_code=404, detail="DEX content not found")
        
        if not dex_content.is_active:
            raise HTTPException(status_code=404, detail="DEX content is not active")
        
        # Return appropriate response based on content type
        response = {
            "id": dex_content.id,
            "title": dex_content.title,
            "description": dex_content.description,
            "content_type": dex_content.content_type,
            "content_url": dex_content.content_url,
            "content_data": dex_content.content_data,
            "delivery_timestamp": datetime.now().isoformat(),
            "actions": []
        }
        
        # Add specific actions based on content type
        if dex_content.content_type == "video":
            response["actions"].append({
                "type": "play_video",
                "url": dex_content.content_url,
                "autoplay": True
            })
        elif dex_content.content_type in ["ar", "3d_model"]:
            response["actions"].append({
                "type": "launch_ar",
                "ar_url": f"/dex/ar/{dex_id}",
                "model_url": dex_content.content_url
            })
        elif dex_content.content_type == "webpage":
            response["actions"].append({
                "type": "open_webpage",
                "url": dex_content.content_url,
                "target": "_blank"
            })
        elif dex_content.content_type == "pdf":
            response["actions"].append({
                "type": "download_pdf",
                "url": dex_content.content_url,
                "filename": f"{dex_content.title}.pdf"
            })
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error delivering DEX: {str(e)}")

@app.get("/dex/ar/{dex_id}")
async def ar_viewer(dex_id: int):
    """Serve AR viewer for DEX content"""
    try:
        db = SessionLocal()
        dex_content = db.query(DEXContent).filter(
            DEXContent.id == dex_id,
            DEXContent.content_type.in_(["ar", "3d_model"])
        ).first()
        db.close()
        
        if not dex_content:
            raise HTTPException(status_code=404, detail="AR content not found")
        
        # Return AR viewer HTML
        ar_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{dex_content.title} - AR Viewer</title>
            <script src="https://aframe.io/releases/1.4.0/aframe.min.js"></script>
            <script src="https://cdn.jsdelivr.net/gh/AR-js-org/AR.js/aframe/build/aframe-ar.js"></script>
            <style>
                body {{ margin: 0; font-family: Arial, sans-serif; }}
                .ar-info {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 5px; z-index: 1000; }}
            </style>
        </head>
        <body>
            <div class="ar-info">
                <h3>{dex_content.title}</h3>
                <p>{dex_content.description}</p>
                <p>Point your camera at the target image</p>
            </div>
            <a-scene embedded arjs="sourceType: webcam; debugUIEnabled: false;">
                <a-marker preset="hiro">
                    <a-entity
                        geometry="primitive: box; width: 1; height: 1; depth: 1"
                        material="color: #4facfe"
                        animation="property: rotation; to: 0 360 0; loop: true; dur: 10000">
                    </a-entity>
                    <a-text
                        value="{dex_content.title}"
                        position="0 1.5 0"
                        align="center"
                        color="#ffffff">
                    </a-text>
                </a-marker>
                <a-entity camera></a-entity>
            </a-scene>
        </body>
        </html>
        """
        
        return HTMLResponse(content=ar_html)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading AR viewer: {str(e)}")

@app.get("/dex/qr/{dex_id}")
async def generate_qr_code(dex_id: int):
    """Generate QR code for DEX content"""
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        # Generate QR code for the DEX delivery URL
        qr_url = f"{request.base_url}dex/deliver/{dex_id}"
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "qr_code_url": qr_url,
            "qr_code_image": f"data:image/png;base64,{qr_base64}",
            "instructions": "Scan this QR code to access the DEX content"
        }
        
    except ImportError:
        return {
            "qr_code_url": f"/dex/deliver/{dex_id}",
            "qr_code_image": None,
            "instructions": "QR code generation requires qrcode library. Use the URL directly.",
            "direct_url": f"/dex/deliver/{dex_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")

@app.get("/business/{business_reference}")
async def business_page(business_reference: str):
    """Serve business information page"""
    try:
        db = SessionLocal()
        business = db.query(Business).filter(Business.business_reference == business_reference).first()
        
        if not business:
            # Create a fallback page
            business_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Business Information</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; border-radius: 10px; }}
                    .content {{ margin-top: 20px; }}
                    .contact {{ background: #f0f9ff; padding: 15px; border-radius: 8px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Business Information</h1>
                    <p>Reference: {business_reference}</p>
                </div>
                <div class="content">
                    <h2>Welcome!</h2>
                    <p>Thank you for your interest in our business. We're excited to share more information with you.</p>
                    <div class="contact">
                        <h3>Contact Information</h3>
                        <p>For more details, please contact us directly.</p>
                        <p>Business Reference: {business_reference}</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            business_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{business.business_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; border-radius: 10px; }}
                    .content {{ margin-top: 20px; }}
                    .contact {{ background: #f0f9ff; padding: 15px; border-radius: 8px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{business.business_name}</h1>
                    <p>Welcome to our business portal</p>
                </div>
                <div class="content">
                    <h2>About Us</h2>
                    <p>Thank you for scanning our image! We're excited to share more about our business with you.</p>
                    <div class="contact">
                        <h3>Contact Information</h3>
                        <p><strong>Business:</strong> {business.business_name}</p>
                        <p><strong>Reference:</strong> {business.business_reference}</p>
                        <p><strong>API Key:</strong> {business.api_key[:8]}...</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        db.close()
        return HTMLResponse(content=business_html)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading business page: {str(e)}") 