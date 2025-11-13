from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import cv2
import easyocr
from ultralytics import YOLO
import re
from collections import defaultdict
import numpy as np
from PIL import Image
import io
import json
from typing import Optional, Dict, List
from difflib import SequenceMatcher
import os
import uuid

app = FastAPI(title="OCR Text Extraction & Verification API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize models
MODEL_PATH = "Mymodel.pt"
yolo_model = None
ocr_reader = None

def initialize_models():
    global yolo_model, ocr_reader
    if yolo_model is None:
        if os.path.exists(MODEL_PATH):
            try:
                print(f"📦 Loading YOLOv8 model from {MODEL_PATH}...")
                yolo_model = YOLO(MODEL_PATH)
                print("✅ YOLOv8 model loaded successfully!")
            except Exception as e:
                print(f"❌ Error loading YOLOv8 model: {e}")
                yolo_model = None
        else:
            print(f"⚠️  Warning: {MODEL_PATH} not found. Some features may not work.")
            print(f"   Please ensure the model file is in the root directory.")
    if ocr_reader is None:
        try:
            print("📦 Initializing EasyOCR reader...")
            ocr_reader = easyocr.Reader(['en'])
            print("✅ EasyOCR reader initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing EasyOCR: {e}")
            ocr_reader = None

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    print("\n🔧 Initializing models on startup...")
    initialize_models()
    print("✅ Startup complete!\n")

# Class mapping
class_map = {
    1: "Surname", 2: "Name", 3: "Nationality", 4: "Sex", 5: "Date of Birth",
    6: "Place of Birth", 7: "Issue Date", 8: "Expiry Date", 9: "Issuing Office",
    10: "Height", 11: "Type", 12: "Country", 13: "Passport No",
    14: "Personal No", 15: "Card No"
}

field_equivalents = {
    "Country": ["Country", "Code of State", "Code of Issuing State", "Codeof Issulng State", "ICode of State"],
    "Issuing Office": ["Issuing Office", "Issuing Authority", "Issuing office", "Iss. office", "Authority", "authoricy", "Iss office", "issuing authority"],
    "Passport No": ["Passport No", "Document No", "IPassport No", "Passport Number"],
    "Personal No": ["Personal No", "National ID"],
    "Date of Birth": ["Date of Birth", "DOB", "Date ofbimn", "of birth", "ofbimn", "of pirth"],
    "Issue Date": ["Issue Date", "Date of Issue", "dale"],
    "Expiry Date": ["Expiry Date", "Date of Expiry", "of expiny"],
    "Name": ["Name", "Given Name", "Given", "nane", "Given name", "IGiven"],
    "Surname": ["Surname", "Last Name", "Sumname"],
    "Place of Birth": ["Place of Birth", "Place of binth"],
    "Card No": ["Card No", "card no_"],
    "Nationality": ["Nationalitv"],
    "Height": ["IHeight"],
    "Sex": ["ISex"]
}

equivalent_to_standard = {}
for standard, equivalents in field_equivalents.items():
    for equiv in equivalents:
        equivalent_to_standard[equiv.lower()] = standard

def iou(boxA, boxB):
    xA, yA = max(boxA[0], boxB[0]), max(boxA[1], boxB[1])
    xB, yB = min(boxA[2], boxB[2]), min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    unionArea = boxAArea + boxBArea - interArea
    return interArea / unionArea if unionArea else 0

def non_max_suppression_area(boxes, iou_thresh=0.4):
    boxes = sorted(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
    final_boxes = []
    for box in boxes:
        if all(iou(box, kept) < iou_thresh for kept in final_boxes):
            final_boxes.append(box)
    return final_boxes

def clean_ocr_text(field, text):
    if not text:
        return ""
    for equiv in field_equivalents.get(field, []) + [field]:
        text = re.sub(rf"(?i)\b{re.escape(equiv)}\b", '', text)

    if "Date" in field:
        text = re.sub(r'[^0-9./a-zA-Z -]', '', text)
        match = re.search(r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b', text)
        return match.group() if match else ""

    return re.sub(r'[^A-Za-z0-9\s/-]', '', text).strip()

def detect_unknown_fields(text):
    field_markers = {
        'Phone No': ['phone', 'mobile', 'tel'],
        'Driving License': ['driving', 'license'],
        'Aadhar': ['aadhar', 'uid'],
        'Email': ['email', '@'],
        'Address': ['address', 'location', 'street']
    }
    detected = {}
    for field, markers in field_markers.items():
        if any(marker in text.lower() for marker in markers):
            detected[field] = text.split(':')[-1].strip() if ':' in text else text
    return detected

def process_image(image_bytes: bytes):
    """Process image and extract text fields"""
    initialize_models()
    
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    if yolo_model is None:
        raise HTTPException(status_code=500, detail="YOLO model not loaded")
    
    results = yolo_model(img)[0]
    boxes = results.boxes
    
    # Process class 0 (general text)
    raw_boxes = []
    for box in boxes:
        class_id = int(box.cls[0])
        if class_id == 0:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            raw_boxes.append((x1, y1, x2, y2))
    
    general_text = []
    if raw_boxes:
        filtered_boxes = non_max_suppression_area(raw_boxes)
        for x1, y1, x2, y2 in filtered_boxes:
            crop = img[y1:y2, x1:x2]
            ocr_result = ocr_reader.readtext(crop, detail=0)
            for line in ocr_result:
                cleaned = line.strip()
                if cleaned:
                    general_text.append(cleaned)
    
    # Process ID card fields (class 3+)
    raw_fields = defaultdict(set)
    all_texts = []
    found_idcard = False
    
    for box in boxes:
        class_id = int(box.cls[0])
        if class_id not in class_map:
            continue
        found_idcard = True
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        crop = img[y1:y2, x1:x2]
        ocr_result = ocr_reader.readtext(crop, detail=0)
        extracted = " ".join(ocr_result).strip()
        field = class_map[class_id]
        cleaned_value = clean_ocr_text(field, extracted)
        all_texts.append(extracted)
        if cleaned_value:
            raw_fields[field].add(cleaned_value)
    
    final_fields = {}
    if found_idcard:
        for field, values in raw_fields.items():
            standard_field = equivalent_to_standard.get(field.strip().lower(), field.strip())
            filtered_values = [v for v in values if len(v) > 1]
            if filtered_values:
                final_fields[standard_field] = max(filtered_values, key=len)
        
        for text in all_texts:
            final_fields.update(detect_unknown_fields(text))
    
    return {
        "general_text": general_text,
        "extracted_fields": final_fields,
        "found_idcard": found_idcard
    }

@app.get("/")
async def root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "OCR API is running. Please ensure index.html exists in the root directory."}

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload and process image for OCR"""
    try:
        contents = await file.read()
        result = process_image(contents)
        return JSONResponse(content={
            "success": True,
            "filename": file.filename,
            **result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify")
async def verify_data(
    extracted_data: str = Form(...),
    original_data: str = Form(...)
):
    """Verify extracted data against original source"""
    try:
        extracted = json.loads(extracted_data)
        original = json.loads(original_data)
        
        verification_results = {}
        confidence_scores = {}
        
        for field, extracted_value in extracted.items():
            original_value = original.get(field, "")
            if original_value:
                similarity = SequenceMatcher(None, 
                    str(extracted_value).lower(), 
                    str(original_value).lower()
                ).ratio()
                confidence_scores[field] = similarity * 100
                verification_results[field] = {
                    "extracted": extracted_value,
                    "original": original_value,
                    "match": similarity > 0.8,
                    "confidence": round(similarity * 100, 2)
                }
            else:
                verification_results[field] = {
                    "extracted": extracted_value,
                    "original": None,
                    "match": None,
                    "confidence": None
                }
        
        overall_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0
        
        return JSONResponse(content={
            "success": True,
            "verification_results": verification_results,
            "overall_confidence": round(overall_confidence, 2),
            "fields_verified": len(verification_results)
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/autofill")
async def autofill_form(
    form_fields: str = Form(...),
    extracted_data: str = Form(...)
):
    """Match extracted data to form fields"""
    try:
        form_fields_list = json.loads(form_fields)
        extracted = json.loads(extracted_data)
        
        field_aliases = {
            "passport no": ["passport number", "document number", "passport num"],
            "date of birth": ["dob", "birthdate"],
            "issue date": ["issued on", "date of issue"],
            "expiry date": ["expires on", "expiration date"],
            "personal no": ["national id", "id number"]
        }
        
        matches = {}
        used_fields = set()
        
        def best_match(question_text, data_dict, threshold=0.7):
            best_match = None
            best_score = 0
            question_text = question_text.lower()
            
            for field_key, field_val in data_dict.items():
                field_key_lower = field_key.lower()
                if field_key_lower in used_fields:
                    continue
                field_variants = [field_key_lower] + field_aliases.get(field_key_lower, [])
                for variant in field_variants:
                    score = SequenceMatcher(None, variant, question_text).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = (field_key, field_val, score)
            if best_score >= threshold:
                return best_match
            return None
        
        for form_field in form_fields_list:
            match = best_match(form_field, extracted, threshold=0.7)
            if match:
                key, val, score = match
                matches[form_field] = {
                    "matched_field": key,
                    "value": val,
                    "confidence": round(score * 100, 2)
                }
                used_fields.add(key.lower())
            else:
                matches[form_field] = {
                    "matched_field": None,
                    "value": None,
                    "confidence": 0
                }
        
        return JSONResponse(content={
            "success": True,
            "matches": matches,
            "fields_matched": len([m for m in matches.values() if m["matched_field"]])
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": yolo_model is not None,
        "ocr_loaded": ocr_reader is not None
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting OCR Text Extraction Server...")
    print("="*60)
    print(f"📡 Server running at: http://localhost:8000")
    print(f"📡 Alternative: http://127.0.0.1:8000")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)

