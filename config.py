import os

# =========================
# Google Document AI Configuration
# =========================

# Explicit configuration
PROJECT_ID = "ai-form-416805"
LOCATION = "us"  # valid regions: us, eu
PROCESSOR_ID = "8c59dbf065df1fa2"  # your FORM_PARSER_PROCESSOR
SERVICE_ACCOUNT_FILE = r"C:\Users\HI\Desktop\intelligent-form-processor-local\backend\anjuman_backend\ai-form-416805-bdea6b1fbf2e.json"

# Export environment variables to ensure client libraries work correctly
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
os.environ["GCP_PROJECT_ID"] = PROJECT_ID
os.environ["DOCUMENT_AI_LOCATION"] = LOCATION
os.environ["DOCUMENT_AI_PROCESSOR_ID"] = PROCESSOR_ID

# =========================
# Local Directories
# =========================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

INCOMING_DIR = os.path.join(BASE_DIR, "incoming")          # scanned images dropped here
WORK_DIR = os.path.join(BASE_DIR, "work")
PDFS_DIR = os.path.join(WORK_DIR, "pdfs")                  # converted 4-page PDFs
OCR_RAW_DIR = os.path.join(WORK_DIR, "ocr_raw")            # raw Document AI JSON
DRAFTS_DIR = os.path.join(BASE_DIR, "results", "drafts")   # structured JSON outputs
REPORTS_DIR = os.path.join(BASE_DIR, "results", "reports") # human-readable PDF summaries
TEMPLATE_FILE = os.path.join(BASE_DIR, "template.json")

# =========================
# Processing Settings
# =========================

# Detect footers to auto-group pages per application
PAGE_FOOTER_CROP_RATIO = 0.12  # bottom 12% of image height
FOOTER_PATTERNS = [
    "applicant acknowledgement slip",
    "acknowledgement slip",
    r"page\s*\d+\s*of\s*\d+"
]

# Document AI request polling
DOC_AI_POLL_INTERVAL = 3       # seconds between status checks
DOC_AI_TIMEOUT = 600           # max wait time (seconds) per document

# Confidence threshold for adjudication
CONFIDENCE_THRESHOLD = 0.75

# =========================
# Gemini (Optional Secondary AI)
# =========================
USE_GEMINI = False             # set True to enable Gemini adjudication
MAX_GEMINI_CALLS_PER_APP = 6   # max fallback calls per application

# =========================
# Ensure Directory Structure Exists
# =========================
for d in [INCOMING_DIR, WORK_DIR, PDFS_DIR, OCR_RAW_DIR, DRAFTS_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

print(f"[CONFIG] Loaded configuration for project: {PROJECT_ID}")
print(f"[CONFIG] Processor ID: {PROCESSOR_ID}")
print(f"[CONFIG] Service Account: {SERVICE_ACCOUNT_FILE}")
print(f"[CONFIG] Working directory: {BASE_DIR}")
