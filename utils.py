import os
import re
import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageEnhance
from PyPDF2 import PdfMerger


def preprocess_image(input_path, output_path):
    """
    Preprocess a single image page (enhancement, denoise, contrast).
    If input is PDF, extracts first page as an image automatically.
    """
    ext = os.path.splitext(input_path)[1].lower()

    if ext == ".pdf":
        doc = fitz.open(input_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(output_path.replace(".pdf", ".jpg"), "JPEG", quality=95)
        doc.close()
        return output_path.replace(".pdf", ".jpg")

    # Standard image processing for scans
    image = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Failed to read image: {input_path}")

    image = cv2.bilateralFilter(image, 9, 75, 75)
    _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    enhanced = cv2.convertScaleAbs(image, alpha=1.2, beta=10)
    cv2.imwrite(output_path, enhanced)
    return output_path


def detect_footer_text(file_path, crop_ratio=0.12):
    """
    Extracts bottom text region (footer) to detect 'Acknowledgement Slip' or 'Page X of Y'
    for automatic grouping.
    Works for PDFs and images.
    """
    ext = os.path.splitext(file_path)[1].lower()
    img = None

    if ext == ".pdf":
        doc = fitz.open(file_path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        doc.close()
    else:
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)

    if img is None:
        return ""

    h = img.shape[0]
    footer = img[int(h * (1 - crop_ratio)) : h, :]
    text = extract_text_from_image(footer)
    if re.search(r"(acknowledgement slip|page\s*\d+\s*of\s*\d+)", text, re.IGNORECASE):
        return text.strip()
    return ""


def extract_text_from_image(image):
    """Simple OCR using pytesseract if available."""
    try:
        import pytesseract
        return pytesseract.image_to_string(image)
    except Exception:
        return ""


def images_to_pdf(input_paths, output_path):
    """
    Converts a list of files (PDF or images) into a single merged PDF.
    Handles PDFs directly; converts images automatically.
    """
    merger = PdfMerger()
    temp_files = []

    for p in input_paths:
        ext = os.path.splitext(p)[1].lower()
        if ext == ".pdf":
            merger.append(p)
        else:
            im = Image.open(p).convert("RGB")
            temp_pdf = p + ".tmp.pdf"
            im.save(temp_pdf, "PDF", resolution=100.0)
            merger.append(temp_pdf)
            temp_files.append(temp_pdf)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merger.write(output_path)
    merger.close()

    for tmp in temp_files:
        if os.path.exists(tmp):
            os.remove(tmp)
    return output_path


def convert_pdf_to_images(pdf_path, output_dir):
    """
    Converts a full PDF (multi-page) into individual page images.
    Returns list of image file paths.
    """
    doc = fitz.open(pdf_path)
    out_images = []
    os.makedirs(output_dir, exist_ok=True)

    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_path = os.path.join(output_dir, f"page_{i:02d}.jpg")
        pix.save(img_path)
        out_images.append(img_path)

    doc.close()
    return out_images
