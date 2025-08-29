"""
Third-party Business API for managing PDFs and DEX content
This module provides API endpoints for external businesses to integrate with the system
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from pydantic import BaseModel
from typing import Optional, List
import os
from datetime import datetime
import uuid

try:
    from .auth import get_business_from_api_key
    from .models import Business, ExtractedImage, DEXContent
    from .database import SessionLocal
    from .utils.pdf_utils import extract_images_from_pdf
except ImportError:
    # Fallback for direct execution
    from auth import get_business_from_api_key
    from models import Business, ExtractedImage, DEXContent
    from database import SessionLocal
    from utils.pdf_utils import extract_images_from_pdf

router = APIRouter(prefix="/api/v1/business", tags=["Business API"])

# Request/Response Models
class DEXContentCreate(BaseModel):
    title: str
    description: str
    content_type: str  # "video", "ar", "3d_model", "webpage", "pdf"
    content_url: Optional[str] = None
    content_data: Optional[str] = None

class DEXContentResponse(BaseModel):
    id: int
    image_id: int
    title: str
    description: str
    content_type: str
    content_url: Optional[str]
    is_active: bool
    created_at: datetime

class ImageResponse(BaseModel):
    id: int
    image_path: str
    business_name: str
    pdf_filename: str
    page_number: int
    tags: Optional[str]
    image_type: str
    dex_content: Optional[DEXContentResponse]

class BusinessStatsResponse(BaseModel):
    total_images: int
    total_dex_content: int
    active_dex_content: int
    recent_matches: int

# ===== BUSINESS AUTHENTICATION =====

@router.get("/profile")
async def get_business_profile(business: Business = Depends(get_business_from_api_key)):
    """Get business profile information"""
    db = SessionLocal()
    
    # Get statistics
    total_images = db.query(ExtractedImage).filter(
        ExtractedImage.business_name == business.name
    ).count()
    
    total_dex = db.query(DEXContent).join(ExtractedImage).filter(
        ExtractedImage.business_name == business.name
    ).count()
    
    active_dex = db.query(DEXContent).join(ExtractedImage).filter(
        ExtractedImage.business_name == business.name,
        DEXContent.is_active == True
    ).count()
    
    db.close()
    
    return {
        "business_name": business.name,
        "business_reference": business.name.lower().replace(" ", "_"),
        "api_key": business.api_key[:8] + "...",
        "created_at": business.created_at,
        "stats": {
            "total_images": total_images,
            "total_dex_content": total_dex,
            "active_dex_content": active_dex
        }
    }

# ===== PDF MANAGEMENT =====

@router.post("/pdf/upload")
async def upload_business_pdf(
    file: UploadFile = File(...),
    tags: str = Form(""),
    image_type: str = Form("logo"),
    business: Business = Depends(get_business_from_api_key)
):
    """Upload and process PDF for a business"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save uploaded file
        upload_dir = "uploaded_pdfs"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create unique filename
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract images from PDF
        try:
            # Create output directory for extracted images
            output_dir = os.path.join("extracted_images", business.name.lower().replace(" ", "_"))
            os.makedirs(output_dir, exist_ok=True)
            
            extracted_images = extract_images_from_pdf(file_path, output_dir)
            
            # Store extracted images in database
            db_images = SessionLocal()
            try:
                for img_info in extracted_images:
                    new_image = ExtractedImage(
                        business_name=business.name,
                        business_reference=business.name.lower().replace(" ", "_"),
                        pdf_filename=file.filename,
                        image_path=img_info["image_path"],
                        page_number=img_info["page_number"],
                        tags=tags,
                        image_type=image_type,
                        is_public=True
                    )
                    db_images.add(new_image)
                
                db_images.commit()
            except Exception as db_error:
                db_images.rollback()
                raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
            finally:
                db_images.close()
            
            # Clean up uploaded PDF
            os.remove(file_path)
            
            return {
                "message": f"Successfully processed PDF and extracted {len(extracted_images)} images",
                "extracted_images": len(extracted_images),
                "business_name": business.name,
                "pdf_filename": file.filename
            }
            
        except Exception as e:
            # Clean up on failure
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/images")
async def get_business_images(business: Business = Depends(get_business_from_api_key)) -> List[ImageResponse]:
    """Get all images for the authenticated business"""
    
    db = SessionLocal()
    
    images = db.query(ExtractedImage).filter(
        ExtractedImage.business_name == business.name
    ).all()
    
    result = []
    for image in images:
        # Get DEX content for this image
        dex_content = db.query(DEXContent).filter(
            DEXContent.image_id == image.id
        ).first()
        
        dex_response = None
        if dex_content:
            dex_response = DEXContentResponse(
                id=dex_content.id,
                image_id=dex_content.image_id,
                title=dex_content.title,
                description=dex_content.description,
                content_type=dex_content.content_type,
                content_url=dex_content.content_url,
                is_active=dex_content.is_active,
                created_at=dex_content.created_at
            )
        
        result.append(ImageResponse(
            id=image.id,
            image_path=image.image_path,
            business_name=image.business_name,
            pdf_filename=image.pdf_filename,
            page_number=image.page_number,
            tags=image.tags,
            image_type=image.image_type,
            dex_content=dex_response
        ))
    
    db.close()
    return result

@router.delete("/images/{image_id}")
async def delete_business_image(
    image_id: int, 
    business: Business = Depends(get_business_from_api_key)
):
    """Delete an image owned by the authenticated business"""
    
    db = SessionLocal()
    
    # Check if image belongs to this business
    image = db.query(ExtractedImage).filter(
        ExtractedImage.id == image_id,
        ExtractedImage.business_name == business.name
    ).first()
    
    if not image:
        db.close()
        raise HTTPException(status_code=404, detail="Image not found or not owned by this business")
    
    # Delete associated DEX content first
    db.query(DEXContent).filter(DEXContent.image_id == image_id).delete()
    
    # Delete image file if it exists
    if os.path.exists(image.image_path):
        os.remove(image.image_path)
    
    # Delete image record
    db.delete(image)
    db.commit()
    db.close()
    
    return {"message": "Image and associated DEX content deleted successfully"}

# ===== DEX CONTENT MANAGEMENT =====

@router.post("/images/{image_id}/dex")
async def create_dex_content(
    image_id: int,
    dex_data: DEXContentCreate,
    business: Business = Depends(get_business_from_api_key)
):
    """Create DEX content for an image"""
    
    db = SessionLocal()
    
    # Verify image belongs to this business
    image = db.query(ExtractedImage).filter(
        ExtractedImage.id == image_id,
        ExtractedImage.business_name == business.name
    ).first()
    
    if not image:
        db.close()
        raise HTTPException(status_code=404, detail="Image not found or not owned by this business")
    
    # Check if DEX content already exists
    existing_dex = db.query(DEXContent).filter(DEXContent.image_id == image_id).first()
    if existing_dex:
        db.close()
        raise HTTPException(status_code=400, detail="DEX content already exists for this image")
    
    # Create DEX content
    dex_content = DEXContent(
        image_id=image_id,
        title=dex_data.title,
        description=dex_data.description,
        content_type=dex_data.content_type,
        content_url=dex_data.content_url,
        content_data=dex_data.content_data,
        is_active=True,
        created_at=datetime.now()
    )
    
    db.add(dex_content)
    db.commit()
    db.refresh(dex_content)
    db.close()
    
    return {
        "message": "DEX content created successfully",
        "dex_id": dex_content.id,
        "image_id": image_id,
        "delivery_url": f"/dex/deliver/{dex_content.id}",
        "ar_url": f"/dex/ar/{dex_content.id}" if dex_data.content_type in ["ar", "3d_model"] else None,
        "qr_code_url": f"/dex/qr/{dex_content.id}"
    }

@router.put("/images/{image_id}/dex")
async def update_dex_content(
    image_id: int,
    dex_data: DEXContentCreate,
    business: Business = Depends(get_business_from_api_key)
):
    """Update DEX content for an image"""
    
    db = SessionLocal()
    
    # Verify image belongs to this business
    image = db.query(ExtractedImage).filter(
        ExtractedImage.id == image_id,
        ExtractedImage.business_name == business.name
    ).first()
    
    if not image:
        db.close()
        raise HTTPException(status_code=404, detail="Image not found or not owned by this business")
    
    # Find existing DEX content
    dex_content = db.query(DEXContent).filter(DEXContent.image_id == image_id).first()
    if not dex_content:
        db.close()
        raise HTTPException(status_code=404, detail="DEX content not found for this image")
    
    # Update DEX content
    dex_content.title = dex_data.title
    dex_content.description = dex_data.description
    dex_content.content_type = dex_data.content_type
    dex_content.content_url = dex_data.content_url
    dex_content.content_data = dex_data.content_data
    
    db.commit()
    db.close()
    
    return {
        "message": "DEX content updated successfully",
        "dex_id": dex_content.id,
        "image_id": image_id
    }

@router.delete("/images/{image_id}/dex")
async def delete_dex_content(
    image_id: int,
    business: Business = Depends(get_business_from_api_key)
):
    """Delete DEX content for an image"""
    
    db = SessionLocal()
    
    # Verify image belongs to this business
    image = db.query(ExtractedImage).filter(
        ExtractedImage.id == image_id,
        ExtractedImage.business_name == business.name
    ).first()
    
    if not image:
        db.close()
        raise HTTPException(status_code=404, detail="Image not found or not owned by this business")
    
    # Find and delete DEX content
    dex_content = db.query(DEXContent).filter(DEXContent.image_id == image_id).first()
    if not dex_content:
        db.close()
        raise HTTPException(status_code=404, detail="DEX content not found for this image")
    
    db.delete(dex_content)
    db.commit()
    db.close()
    
    return {"message": "DEX content deleted successfully"}

@router.patch("/images/{image_id}/dex/toggle")
async def toggle_dex_content(
    image_id: int,
    business: Business = Depends(get_business_from_api_key)
):
    """Toggle DEX content active status"""
    
    db = SessionLocal()
    
    # Verify image belongs to this business
    image = db.query(ExtractedImage).filter(
        ExtractedImage.id == image_id,
        ExtractedImage.business_name == business.name
    ).first()
    
    if not image:
        db.close()
        raise HTTPException(status_code=404, detail="Image not found or not owned by this business")
    
    # Find DEX content
    dex_content = db.query(DEXContent).filter(DEXContent.image_id == image_id).first()
    if not dex_content:
        db.close()
        raise HTTPException(status_code=404, detail="DEX content not found for this image")
    
    # Toggle active status
    dex_content.is_active = not dex_content.is_active
    db.commit()
    db.close()
    
    return {
        "message": f"DEX content {'activated' if dex_content.is_active else 'deactivated'}",
        "is_active": dex_content.is_active
    }

# ===== ANALYTICS =====

@router.get("/stats")
async def get_business_stats(business: Business = Depends(get_business_from_api_key)) -> BusinessStatsResponse:
    """Get business statistics"""
    
    db = SessionLocal()
    
    total_images = db.query(ExtractedImage).filter(
        ExtractedImage.business_name == business.name
    ).count()
    
    total_dex = db.query(DEXContent).join(ExtractedImage).filter(
        ExtractedImage.business_name == business.name
    ).count()
    
    active_dex = db.query(DEXContent).join(ExtractedImage).filter(
        ExtractedImage.business_name == business.name,
        DEXContent.is_active == True
    ).count()
    
    db.close()
    
    return BusinessStatsResponse(
        total_images=total_images,
        total_dex_content=total_dex,
        active_dex_content=active_dex,
        recent_matches=0  # This would require tracking match logs
    )
