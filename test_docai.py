"""
test_docai.py
----------------------------------
Quick sanity test for Google Document AI connection.
Processes one local PDF and prints detected text length.
No GCS, fully local call.
"""

from google.cloud import documentai_v1 as documentai
import os

# === CONFIG ===
PROJECT_ID = "ai-form-416805"
LOCATION = "us"
PROCESSOR_ID = "8c59dbf065df1fa2"
SERVICE_ACCOUNT_FILE = r"C:\Users\HI\Desktop\intelligent-form-processor-local\backend\anjuman_backend\ai-form-416805-bdea6b1fbf2e.json"
SAMPLE_FILE = r"C:\Users\HI\Desktop\intelligent-form-processor-local\backend\anjuman_backend\incoming\sample_form.pdf"

# === SETUP ===
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

# === CLIENT ===
client = documentai.DocumentProcessorServiceClient()
name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"

# === PROCESS DOCUMENT ===
with open(SAMPLE_FILE, "rb") as f:
    document = {"content": f.read(), "mime_type": "application/pdf"}

print(f"[TEST] Sending {os.path.basename(SAMPLE_FILE)} to Document AI...")
result = client.process_document(request={"name": name, "raw_document": document})
doc = result.document

# === OUTPUT SUMMARY ===
print(f"[SUCCESS] Processed '{os.path.basename(SAMPLE_FILE)}'")
print(f"[INFO] Document text length: {len(doc.text)} characters")

# Optional: save raw OCR output
out_path = os.path.join(os.path.dirname(SAMPLE_FILE), "sample_form_ocr_output.json")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(documentai.Document.to_json(doc))
print(f"[INFO] OCR JSON saved to {out_path}")
