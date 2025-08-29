from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
try:
    from database import Base
except ImportError:
    from .database import Base
from datetime import datetime
import secrets
import hashlib

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    user_type = Column(String, default="regular")  # "regular" or "business"
    company_name = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_uploads = relationship("UserUpload", back_populates="user")
    user_activities = relationship("UserActivity", back_populates="user")

class UserUpload(Base):
    __tablename__ = "user_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # "image" or "pdf"
    tags = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_uploads")

class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String, nullable=False)  # "upload", "match", "login", "profile", "delete"
    title = Column(String, nullable=False)
    description = Column(Text)
    activity_data = Column(Text)  # JSON data for additional info
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_activities")

class Business(Base):
    __tablename__ = "businesses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    api_key = Column(String, unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    extracted_images = relationship("ExtractedImage", back_populates="business")
    dex_content = relationship("DEXContent", back_populates="business")

class ExtractedImage(Base):
    __tablename__ = "extracted_images"
    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String, nullable=False)
    pdf_filename = Column(String, nullable=False)
    page_number = Column(Integer, nullable=False)
    tags = Column(String)
    image_type = Column(String)
    business_name = Column(String)
    business_reference = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # New fields for third-party integration
    business_id = Column(Integer, ForeignKey("businesses.id"))
    is_public = Column(Boolean, default=False)  # Whether this image is available for matching
    print_design_id = Column(String)  # Reference to print design in business system
    
    # Relationships
    business = relationship("Business", back_populates="extracted_images")
    dex_content = relationship("DEXContent", back_populates="image")

class DEXContent(Base):
    __tablename__ = "dex_content"
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    image_id = Column(Integer, ForeignKey("extracted_images.id"), nullable=False)
    
    # DEX content details
    title = Column(String, nullable=False)
    description = Column(Text)
    content_type = Column(String, nullable=False)  # 'ar', 'webpage', 'video', 'link'
    content_url = Column(String, nullable=False)
    content_data = Column(Text)  # JSON data for AR, custom content, etc.
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    business = relationship("Business", back_populates="dex_content")
    image = relationship("ExtractedImage", back_populates="dex_content")

class APIAccessLog(Base):
    __tablename__ = "api_access_logs"
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(Integer)
    response_time = Column(Integer)  # in milliseconds
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow) 