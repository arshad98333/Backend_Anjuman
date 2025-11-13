import os
import json
from threading import Lock

DB_FILE = os.path.join(os.path.dirname(__file__), "local_db.json")
_LOCK = Lock()


def _load_db():
    if not os.path.exists(DB_FILE):
        return {"last_app_id": 1000, "forms": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"last_app_id": 1000, "forms": []}


def _save_db(data):
    tmp = f"{DB_FILE}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DB_FILE)


def generate_application_id():
    with _LOCK:
        db = _load_db()
        db["last_app_id"] += 1
        _save_db(db)
        return db["last_app_id"]


def insert_form_record(form_json):
    with _LOCK:
        db = _load_db()
        db["forms"].append(form_json)
        _save_db(db)


def get_all_forms():
    db = _load_db()
    return db.get("forms", [])


def get_form_by_id(app_id):
    db = _load_db()
    for form in db.get("forms", []):
        if form.get("metadata", {}).get("app_id") == app_id:
            return form
    return None


def update_form(app_id, updated_json):
    with _LOCK:
        db = _load_db()
        for i, form in enumerate(db.get("forms", [])):
            if form.get("metadata", {}).get("app_id") == app_id:
                db["forms"][i] = updated_json
                _save_db(db)
                return True
    return False
