"""
document_ai_client.py  –  Offline/local-first Document AI client
---------------------------------------------------------------
Processes each PDF locally (synchronous mode) with Google Document AI.
No Cloud Storage is used; all I/O happens on local disk.

Requirements:
    pip install google-cloud-documentai
"""

import os
import json
import time
from google.cloud import documentai_v1 as documentai
from config import (
    PROJECT_ID,
    LOCATION,
    PROCESSOR_ID,
    SERVICE_ACCOUNT_FILE,
    OCR_RAW_DIR,
    DOC_AI_POLL_INTERVAL,
    DOC_AI_TIMEOUT,
)

# Explicitly load credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

# Instantiate client once
client = documentai.DocumentProcessorServiceClient()

def process_pdf_local(pdf_path):
    """
    Processes a single PDF synchronously using Document AI.
    Works offline (no GCS) and writes output JSON locally.
    """
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
    print(f"[INFO] Processing {os.path.basename(pdf_path)} via Document AI processor {PROCESSOR_ID}")

    with open(pdf_path, "rb") as f:
        raw_document = {"content": f.read(), "mime_type": "application/pdf"}

    request = {"name": name, "raw_document": raw_document}

    start = time.time()
    result = client.process_document(request=request)
    elapsed = time.time() - start
    print(f"[INFO] Completed {os.path.basename(pdf_path)} in {elapsed:.1f}s")

    document = result.document
    out_path = os.path.join(OCR_RAW_DIR, os.path.basename(pdf_path).replace(".pdf", "_ocr.json"))
    os.makedirs(OCR_RAW_DIR, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(documentai.Document.to_json(document))

    return out_path


def process_batch_local(pdf_paths):
    """
    Sequentially process multiple PDFs using local Document AI calls.
    """
    results = []
    for idx, pdf in enumerate(pdf_paths, start=1):
        try:
            print(f"[BATCH] ({idx}/{len(pdf_paths)}) {os.path.basename(pdf)}")
            ocr_path = process_pdf_local(pdf)
            results.append((ocr_path, pdf))
        except Exception as e:
            print(f"[ERROR] {pdf}: {e}")
        time.sleep(DOC_AI_POLL_INTERVAL)  # polite spacing
    return results
