# main.py
from fastapi import FastAPI, BackgroundTasks, UploadFile, File
from worker import run_once
import os
from config import DRAFTS_DIR, REPORTS_DIR, INCOMING_DIR
import shutil

app = FastAPI(title="Anjuman Backend")

@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):
    """
    Trigger a background one-shot run. For continuous processing, run worker service separately.
    """
    background_tasks.add_task(run_once)
    return {"status":"accepted", "message":"Ingestion job started in background."}

@app.post("/upload-zip")
async def upload_zip(file: UploadFile = File(...)):
    """
    Optional: upload a zip file from UI/operator machine; server extracts to incoming dir and triggers processing.
    """
    save_path = os.path.join(INCOMING_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())
    # If zip, extract
    import zipfile
    if zipfile.is_zipfile(save_path):
        with zipfile.ZipFile(save_path, 'r') as z:
            z.extractall(INCOMING_DIR)
        os.remove(save_path)
    return {"status":"uploaded"}

@app.get("/results/list")
def list_results():
    jsons = [os.path.basename(p) for p in os.listdir(DRAFTS_DIR) if p.endswith(".json")]
    pdfs = [os.path.basename(p) for p in os.listdir(REPORTS_DIR) if p.endswith(".pdf")]
    return {"jsons": jsons, "pdfs": pdfs}

@app.get("/results/json/{fname}")
def get_json(fname: str):
    path = os.path.join(DRAFTS_DIR, fname)
    if not os.path.exists(path):
        return {"error":"not found"}
    import json
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/results/report/{fname}")
def get_report(fname: str):
    path = os.path.join(REPORTS_DIR, fname)
    if not os.path.exists(path):
        return {"error":"not found"}
    return {"path": path}
