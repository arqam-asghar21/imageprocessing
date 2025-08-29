from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime

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