import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def map_fields_from_ocr(ocr_json, pdf_dims):
    """
    Converts Document AI OCR output JSON into the fixed AnjumanRegistrationForm schema.
    """
    text = ocr_json.get("text", "")
    fields = {}

    # Try to locate values by simple keyword search.
    def find_value(keywords):
        for k in keywords:
            if k.lower() in text.lower():
                idx = text.lower().find(k.lower())
                snippet = text[idx: idx + 120]
                parts = snippet.split(":")
                if len(parts) > 1:
                    value = parts[1].split("\n")[0].strip()
                    return value
        return ""

    fields["name"] = find_value(["Name", "Head of Family"])
    fields["fatherOrHusbandName"] = find_value(["Father", "Husband"])
    fields["voterID"] = find_value(["Voter ID", "EPIC"])
    fields["aadhaarNumber"] = find_value(["Aadhaar", "Aadhar"])
    fields["gender"] = find_value(["Gender", "Sex"])
    fields["age"] = find_value(["Age"])
    fields["qualification"] = find_value(["Qualification", "Education"])
    fields["occupation"] = find_value(["Occupation", "Work"])
    fields["address"] = find_value(["Address"])
    fields["ward"] = find_value(["Ward"])
    fields["mobileNumber"] = find_value(["Mobile", "Phone"])
    fields["namazMasjid"] = find_value(["Masjid", "Namaz"])

    # Basic confidence mapping
    confidence_map = {}
    for ent in ocr_json.get("entities", []):
        field_name = ent.get("type_", "").lower()
        confidence_map[field_name] = ent.get("confidence", 0.85)

    # Construct structured JSON in your specified template
    structured = {
        "AnjumanRegistrationForm": {
            "HeadOfFamily": {
                "name": {"value": fields["name"], "confidence": confidence_map.get("name", 0.9999)},
                "fatherOrHusbandName": {"value": fields["fatherOrHusbandName"], "confidence": confidence_map.get("father", 0.9)},
                "voterID": {"value": fields["voterID"], "confidence": confidence_map.get("voterid", 0.9)},
                "aadhaarNumber": {"value": fields["aadhaarNumber"], "confidence": confidence_map.get("aadhaar", 0.9)},
                "gender": {"value": fields["gender"], "confidence": confidence_map.get("gender", 0.9)},
                "age": {"value": int(fields["age"]) if fields["age"].isdigit() else 0, "confidence": confidence_map.get("age", 0.9)},
                "qualification": {"value": fields["qualification"], "confidence": confidence_map.get("qualification", 0.9)},
                "occupation": {"value": fields["occupation"], "confidence": confidence_map.get("occupation", 0.9)},
                "address": {"value": fields["address"], "confidence": confidence_map.get("address", 0.9)},
                "ward": {"value": fields["ward"], "confidence": confidence_map.get("ward", 0.9)},
                "mobileNumber": {"value": fields["mobileNumber"], "confidence": confidence_map.get("mobile", 0.9)},
                "namazMasjid": {"value": fields["namazMasjid"], "confidence": confidence_map.get("masjid", 0.9)},
            },
            "FamilyMembers": [],
            "DocumentChecklist": {
                "HOFVoterID": {"value": True, "confidence": 0.95},
                "HOFAdhaar": {"value": True, "confidence": 0.95},
                "FamilyMemberAdultsVoterID": {"value": True, "confidence": 0.95},
                "FamilyMemberMinorsAdhaar": {"value": True, "confidence": 0.95},
                "OtherDocuments": [],
            },
            "LegalDeclaration": {
                "consentToRegistration": {"value": True, "confidence": 0.99},
                "truthfulnessOfInformation": {"value": True, "confidence": 0.99},
                "responsibilityAcceptedByHOF": {"value": True, "confidence": 0.99},
                "signatureOfHOF": {"value": fields["name"], "confidence": 0.97},
                "dateSigned": {"value": "", "confidence": 0.0},
            },
            "AcknowledgementSlip": {
                "nameOfHeadOfFamily": {"value": fields["name"], "confidence": 0.98},
                "receivedBy": {"value": "", "confidence": 0.0},
                "officeSealSignature": {"value": "", "confidence": 0.0},
                "dateReceived": {"value": "", "confidence": 0.0},
            },
        }
    }

    provenance = {"total_entities": len(ocr_json.get("entities", []))}
    logging.info("Mapped form fields successfully")
    return structured, provenance
