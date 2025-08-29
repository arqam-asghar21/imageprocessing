import fitz  # PyMuPDF
import os

def extract_images_from_pdf(pdf_path, output_dir):
    doc = fitz.open(pdf_path)
    images_info = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        # Render the entire page as an image (full page snapshot)
        pix = page.get_pixmap(alpha=True)  # alpha=True for transparency if present
        image_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_page{page_number+1}.png"
        image_path = os.path.join(output_dir, image_filename)
        pix.save(image_path)
        images_info.append({
            "image_path": image_path,
            "page_number": page_number + 1
        })
    return images_info 