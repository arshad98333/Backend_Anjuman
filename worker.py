import os
import sys
import time
import json
import shutil
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    INCOMING_DIR,
    WORK_DIR,
    PDFS_DIR,
    OCR_RAW_DIR,
    DRAFTS_DIR,
    REPORTS_DIR,
)
from utils import preprocess_image, detect_footer_text, images_to_pdf, convert_pdf_to_images
from document_ai_client import process_pdf_local
from mapper import map_fields_from_ocr
from pdf_report import generate_pdf_report
from local_db_manager import generate_application_id, insert_form_record


# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

ARCHIVE_DIR = os.path.join(WORK_DIR, "archive")
for d in [ARCHIVE_DIR, PDFS_DIR, OCR_RAW_DIR, DRAFTS_DIR, REPORTS_DIR, INCOMING_DIR]:
    os.makedirs(d, exist_ok=True)


# ----------------------------------------------------------------------
# File discovery and grouping
# ----------------------------------------------------------------------
def list_incoming_files():
    """List all PDF files in the incoming directory."""
    files = sorted(Path(INCOMING_DIR).glob("*.pdf"))
    return [str(f) for f in files]


def group_pdfs_into_apps(file_paths):
    """Each PDF is treated as one application."""
    grouped = []
    for path in file_paths:
        grouped.append([path])
    return grouped


# ----------------------------------------------------------------------
# Preprocessing
# ----------------------------------------------------------------------
def preprocess_group(file_paths, work_subdir):
    """
    Handles PDFs: splits each into page images and enhances them.
    Returns list of page image paths.
    """
    os.makedirs(work_subdir, exist_ok=True)
    processed = []

    for src in file_paths:
        try:
            # Convert each PDF page to image
            pages = convert_pdf_to_images(src, work_subdir)
            for page_img in pages:
                base = os.path.basename(page_img)
                out_path = os.path.join(work_subdir, base)
                processed_img = preprocess_image(page_img, out_path)
                processed.append(processed_img)
        except Exception as e:
            logging.exception("Failed to preprocess %s", src)

    return processed


# ----------------------------------------------------------------------
# PDF build
# ----------------------------------------------------------------------
def build_pdf_from_images(image_paths, pdf_path):
    """Combine processed images into a single PDF."""
    try:
        if not image_paths:
            raise ValueError("No images found for PDF build")
        images_to_pdf(image_paths, pdf_path)
        return pdf_path
    except Exception as e:
        logging.exception("PDF build failed: %s", e)
        return None


def safe_write_json(path, data):
    """Write JSON safely with atomic replace."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ----------------------------------------------------------------------
# Core processing
# ----------------------------------------------------------------------
def process_application_group(group_paths):
    """Process one PDF form and extract structured JSON."""
    job_start = time.time()
    app_id = generate_application_id()
    work_subdir = os.path.join(WORK_DIR, f"app_{app_id}")
    os.makedirs(work_subdir, exist_ok=True)

    try:
        logging.info("Processing application %s", app_id)

        processed_images = preprocess_group(group_paths, work_subdir)
        if not processed_images:
            logging.error("No pages extracted for app %s", app_id)
            return None

        pdf_path = os.path.join(PDFS_DIR, f"app_{app_id}.pdf")
        if not build_pdf_from_images(processed_images, pdf_path):
            logging.error("Failed to create merged PDF for %s", app_id)
            return None

        # Call Document AI locally
        ocr_json_path = process_pdf_local(pdf_path)
        if not ocr_json_path or not os.path.exists(ocr_json_path):
            logging.error("OCR JSON missing for app %s", app_id)
            return None

        with open(ocr_json_path, "r", encoding="utf-8") as f:
            ocr_json = json.load(f)

        # Map OCR output to template
        filled_json, provenance = map_fields_from_ocr(ocr_json, {})
        filled_json.setdefault("metadata", {})
        filled_json["metadata"].update(
            {
                "app_id": app_id,
                "source_pdf": pdf_path,
                "status": "draft",
                "processing_started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(job_start)),
                "processing_completed": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )

        hof = (
            filled_json.get("AnjumanRegistrationForm", {})
            .get("HeadOfFamily", {})
            .get("name", {})
            .get("value", "HOF")
        )
        safe_hof = "".join([c if c.isalnum() or c in (" ", "_") else "_" for c in hof]).strip().replace(" ", "_")

        json_path = os.path.join(DRAFTS_DIR, f"application_{app_id}_{safe_hof}.json")
        safe_write_json(json_path, filled_json)

        # Store in local database
        insert_form_record(filled_json)

        # Generate visual PDF report
        report_path = generate_pdf_report(
            app_id,
            filled_json,
            processed_images,
            output_path=os.path.join(REPORTS_DIR, f"application_{app_id}_report.pdf"),
        )

        # Move processed PDF to archive
        for f in group_paths:
            try:
                shutil.move(f, os.path.join(ARCHIVE_DIR, os.path.basename(f)))
            except Exception:
                pass
        shutil.rmtree(work_subdir, ignore_errors=True)

        logging.info("Completed app %s -> JSON %s | Report %s", app_id, json_path, report_path)
        return {"app_id": app_id, "json": json_path, "report": report_path}

    except Exception:
        logging.exception("Unhandled error processing %s", app_id)
        shutil.rmtree(work_subdir, ignore_errors=True)
        return None


# ----------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------
def run_once(parallel_workers=1):
    """Run pipeline on all incoming PDFs."""
    files = list_incoming_files()
    if not files:
        logging.info("No PDFs in incoming folder.")
        return []

    groups = group_pdfs_into_apps(files)
    logging.info("Found %d application PDFs", len(groups))

    results = []
    with ThreadPoolExecutor(max_workers=parallel_workers) as ex:
        futures = {ex.submit(process_application_group, g): g for g in groups}
        for fut in as_completed(futures):
            res = fut.result()
            if res:
                results.append(res)

    logging.info("Processing complete: %d succeeded of %d", len(results), len(groups))
    return results


# ----------------------------------------------------------------------
# Main entry
# ----------------------------------------------------------------------
if __name__ == "__main__":
    run_once(parallel_workers=1)
