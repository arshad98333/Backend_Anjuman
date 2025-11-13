# pdf_report.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import json, textwrap, os
from config import REPORTS_DIR

def generate_pdf_report(app_id, filled_json, page_image_paths, output_path=None):
    if output_path is None:
        output_path = os.path.join(REPORTS_DIR, f"application_{app_id}_report.pdf")
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    y = height - margin
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, f"Application Report — {app_id}")
    y -= 18
    c.setFont("Helvetica", 9)
    # Metadata top block
    meta = filled_json.get('metadata', {})
    app_meta_text = f"Status: {filled_json.get('metadata', {}).get('status','draft')}"
    c.drawString(margin, y, app_meta_text)
    y -= 20
    # JSON content (pretty printed) - limited lines per page
    json_text = json.dumps(filled_json, ensure_ascii=False, indent=2)
    wrapped = textwrap.wrap(json_text, 120)
    c.setFont("Courier", 7)
    lines_per_page = 45
    idx = 0
    while idx < len(wrapped):
        if y < 80:
            c.showPage()
            y = height - margin
            c.setFont("Courier", 7)
        line = wrapped[idx]
        c.drawString(margin, y, line)
        y -= 12
        idx += 1
    # Add page thumbnails after JSON, one per PDF page
    for img_path in page_image_paths:
        c.showPage()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, height - margin - 12, f"Page image: {os.path.basename(img_path)}")
        try:
            img = ImageReader(img_path)
            # scale to fit A4 with margins
            max_w = width - 2*margin
            max_h = height - 2*margin - 20*mm
            iw, ih = img.getSize()
            scale = min(max_w/iw, max_h/ih, 1.0)
            w_img, h_img = iw*scale, ih*scale
            x = (width - w_img)/2
            y_img = (height - h_img)/2 - 20
            c.drawImage(img, x, y_img, w_img, h_img)
        except Exception:
            c.drawString(margin, height - margin - 40, "Error embedding image.")
    c.save()
    return output_path
