from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import json
import os
from typing import Optional

# Import models and database
from models import User, UserUpload, UserActivity
from database import get_db

# Create router
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Security configuration
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()

# Utility functions
def verify_password(plain_password, hashed_password):
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Verify JWT token and return user"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def log_user_activity(db: Session, user_id: int, activity_type: str, title: str, description: str = None, activity_data: dict = None):
    """Log user activity for monitoring"""
    try:
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            title=title,
            description=description,
            activity_data=json.dumps(activity_data) if activity_data else None
        )
        db.add(activity)
        db.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")
        db.rollback()

# Authentication endpoints

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    user_type: str = "regular"
    company_name: Optional[str] = None
    industry: Optional[str] = None

@router.post("/signup")
async def signup(
    signup_data: SignupRequest,
    db: Session = Depends(get_db)
):
    first_name = signup_data.first_name
    last_name = signup_data.last_name
    email = signup_data.email
    password = signup_data.password
    user_type = signup_data.user_type
    company_name = signup_data.company_name
    industry = signup_data.industry
    """User registration endpoint"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Validate user type
    if user_type not in ["regular", "business"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user type"
        )
    
    # Validate business fields
    if user_type == "business":
        if not company_name or not industry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name and industry are required for business users"
            )
    
    try:
        # Create new user
        hashed_password = get_password_hash(password)
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hashed_password,
            user_type=user_type,
            company_name=company_name,
            industry=industry
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Log activity
        log_user_activity(
            db=db,
            user_id=user.id,
            activity_type="signup",
            title="Account Created",
            description=f"New {user_type} account created",
            activity_data={"user_type": user_type, "company_name": company_name}
        )
        
        return {
            "message": "User created successfully",
            "user_id": user.id,
            "email": user.email,
            "user_type": user.user_type
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    email = login_data.email
    password = login_data.password
    """User login endpoint"""
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Log activity
    log_user_activity(
        db=db,
        user_id=user.id,
        activity_type="login",
        title="User Login",
        description="User logged in successfully"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "user_type": user.user_type,
            "company_name": user.company_name,
            "industry": user.industry
        }
    }

@router.get("/profile")
async def get_profile(current_user: User = Depends(verify_token)):
    """Get current user profile"""
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "user_type": current_user.user_type,
        "company_name": current_user.company_name,
        "industry": current_user.industry,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }

@router.put("/profile")
async def update_profile(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    if first_name is not None:
        current_user.first_name = first_name
    if last_name is not None:
        current_user.last_name = last_name
    
    current_user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(current_user)
        
        # Log activity
        log_user_activity(
            db=db,
            user_id=current_user.id,
            activity_type="profile",
            title="Profile Updated",
            description="User profile information updated"
        )
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": current_user.id,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "email": current_user.email,
                "user_type": current_user.user_type
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )

@router.post("/logout")
async def logout(current_user: User = Depends(verify_token), db: Session = Depends(get_db)):
    """User logout endpoint"""
    
    # Log activity
    log_user_activity(
        db=db,
        user_id=current_user.id,
        activity_type="logout",
        title="User Logout",
        description="User logged out successfully"
    )
    
    return {"message": "Logged out successfully"}

# User upload endpoints
@router.post("/upload")
async def upload_content(
    file: UploadFile,
    content_type: str = Form(...),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload content (image or PDF) for the authenticated user"""
    
    # Validate content type
    if content_type not in ["image", "pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content type. Must be 'image' or 'pdf'"
        )
    
    # Validate file type
    if content_type == "image" and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    if content_type == "pdf" and file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = f"user_uploads/{current_user.id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = f"{upload_dir}/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create upload record
        upload = UserUpload(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            content_type=content_type,
            tags=tags
        )
        
        db.add(upload)
        db.commit()
        db.refresh(upload)
        
        # Log activity
        log_user_activity(
            db=db,
            user_id=current_user.id,
            activity_type="upload",
            title="Content Uploaded",
            description=f"{content_type.title()} file uploaded: {file.filename}",
            activity_data={"filename": file.filename, "content_type": content_type, "tags": tags}
        )
        
        return {
            "message": f"{content_type.title()} uploaded successfully",
            "upload_id": upload.id,
            "filename": upload.filename,
            "file_path": upload.file_path
        }
        
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.get("/uploads")
async def get_user_uploads(current_user: User = Depends(verify_token), db: Session = Depends(get_db)):
    """Get all uploads for the authenticated user"""
    
    uploads = db.query(UserUpload).filter(UserUpload.user_id == current_user.id).order_by(UserUpload.uploaded_at.desc()).all()
    
    return [
        {
            "id": upload.id,
            "filename": upload.filename,
            "file_path": upload.file_path,
            "content_type": upload.content_type,
            "tags": upload.tags,
            "uploaded_at": upload.uploaded_at
        }
        for upload in uploads
    ]

@router.get("/uploads/{upload_id}")
async def get_user_upload(
    upload_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get a specific user upload by ID"""
    
    upload = db.query(UserUpload).filter(
        UserUpload.id == upload_id,
        UserUpload.user_id == current_user.id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    return {
        "id": upload.id,
        "filename": upload.filename,
        "file_path": upload.file_path,
        "content_type": upload.content_type,
        "tags": upload.tags,
        "uploaded_at": upload.uploaded_at
    }

@router.delete("/uploads/{upload_id}")
async def delete_user_upload(
    upload_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a user upload"""
    
    upload = db.query(UserUpload).filter(
        UserUpload.id == upload_id,
        UserUpload.user_id == current_user.id
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    try:
        # Delete file from disk
        if os.path.exists(upload.file_path):
            os.remove(upload.file_path)
        
        # Delete from database
        db.delete(upload)
        db.commit()
        
        # Log activity
        log_user_activity(
            db=db,
            user_id=current_user.id,
            activity_type="delete",
            title="Content Deleted",
            description=f"Upload deleted: {upload.filename}",
            activity_data={"filename": upload.filename, "content_type": upload.content_type}
        )
        
        return {"message": "Upload deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting upload: {str(e)}"
        )

# User statistics and activity endpoints
@router.get("/statistics")
async def get_user_statistics(current_user: User = Depends(verify_token), db: Session = Depends(get_db)):
    """Get user statistics"""
    
    # Count uploads
    total_uploads = db.query(UserUpload).filter(UserUpload.user_id == current_user.id).count()
    total_pdfs = db.query(UserUpload).filter(
        UserUpload.user_id == current_user.id,
        UserUpload.content_type == "pdf"
    ).count()
    
    # Calculate days active
    days_active = (datetime.utcnow() - current_user.created_at).days + 1
    
    return {
        "total_uploads": total_uploads,
        "total_pdfs": total_pdfs,
        "total_matches": 0,  # TODO: Implement match counting
        "days_active": days_active
    }

@router.get("/activity")
async def get_user_activity(current_user: User = Depends(verify_token), db: Session = Depends(get_db)):
    """Get user activity timeline"""
    
    activities = db.query(UserActivity).filter(
        UserActivity.user_id == current_user.id
    ).order_by(UserActivity.timestamp.desc()).limit(50).all()
    
    return [
        {
            "id": activity.id,
            "type": activity.activity_type,
            "title": activity.title,
            "description": activity.description,
            "activity_data": json.loads(activity.activity_data) if activity.activity_data else None,
            "timestamp": activity.timestamp
        }
        for activity in activities
    ]
