import os
import sys
sys.path.append('.')

from imageprocessing.database import engine, Base
from imageprocessing.models import ExtractedImage
from imageprocessing.batch_processor import process_all_pdfs

def clear_and_reprocess():
    """Clear database and re-process all PDFs with new filtering"""
    
    # Drop and recreate all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    print("Database cleared. Re-processing all PDFs with improved filtering...")
    
    # Re-process all PDFs
    process_all_pdfs()
    
    print("Re-processing complete!")

if __name__ == "__main__":
    clear_and_reprocess() 