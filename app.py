from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import cv2
import re
from collections import defaultdict
import numpy as np
from PIL import Image
import io
import json
from typing import Optional, Dict, List, Any, Tuple
import base64
from difflib import SequenceMatcher
import os
import uuid
from datetime import datetime
import requests
import quality_score
from ocr_verifier import OCRVerifier
from job_form_filler import JobFormFiller
from config import SELECTED_LANGUAGE
from paddle_ocr_module import PaddleOCRWrapper
from trocr_handwritten import TrOCRWrapper
from language_support import LanguageLoader
from spatial_extraction import extract_spatial_key_values
from enhanced_field_parser import parse_text_to_json_with_logging
import ocr_confidence

# MOSIP Integration imports (runtime - won't break app if unavailable)
try:
    from packet_handler import PacketHandler
    from mosip_field_mapper import MosipFieldMapper
    MOSIP_AVAILABLE = True
    print("✅ MOSIP modules loaded successfully")
except ImportError as e:
    print(f"⚠️ MOSIP modules not available: {e}")
    MOSIP_AVAILABLE = False
    PacketHandler = None
    MosipFieldMapper = None

# Import GoogleFormHandler only when needed (lazy import)
# This prevents importing the Streamlit app.py from Auto-Job-Form-Filler-Agent
import sys
import os

# Store original path to restore later
_original_path = sys.path.copy()

# Lazy import function - only adds path when needed
def get_google_form_handler():
    _agent_path = os.path.dirname(__file__)
    
    if not os.path.exists(_agent_path):
        return None
    
    if _agent_path not in sys.path:
        sys.path.insert(0, _agent_path)
    
    try:
        from google_form_handler import GoogleFormHandler
        return GoogleFormHandler
    except ImportError:
        return None

app = FastAPI(title="OCR Text Extraction & Verification API")

# CORS middleware - specific origins required when using credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount uploads directory for serving uploaded images
if not os.path.exists("uploads"):
    os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# MOSIP OCR Demo Page
@app.get("/mosip-demo")
async def mosip_demo():
    """Serve the MOSIP OCR Integration Demo page"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "mosip_ocr_demo.html")
    if os.path.exists(template_path):
        return FileResponse(template_path, media_type="text/html")
    return {"error": "Demo page not found"}

# In-memory storage for uploaded images and region data (for streaming)
uploaded_images = {}  # {image_id: image_bytes}
region_data_cache = {}  # {image_id: [regions]}

# In-memory storage for MOSIP pre-registration applications
mosip_applications = {}  # {prid: application_data}

# Initialize OCR models
paddle_ocr = None
trocr_ocr = None
language_loader = LanguageLoader(SELECTED_LANGUAGE)
verifier = OCRVerifier(SELECTED_LANGUAGE)

# Initialize MOSIP components
PACKETS_DIR = "mock_packets"
if MOSIP_AVAILABLE:
    os.makedirs(PACKETS_DIR, exist_ok=True)
    packet_handler = PacketHandler(PACKETS_DIR)
    mosip_mapper = MosipFieldMapper()
    print(f"✅ MOSIP components initialized (packets dir: {PACKETS_DIR})")
else:
    packet_handler = None
    mosip_mapper = None

def initialize_models():
    global paddle_ocr, trocr_ocr

    if paddle_ocr is None:
        try:
            print("📦 Initializing PaddleOCR...")
            # Map language codes to PaddleOCR format
            lang_map = {
                'en': 'en',
                'ar': 'arabic',
                'hi': 'devanagari'
            }
            ocr_lang = lang_map.get(SELECTED_LANGUAGE, 'en')
            paddle_ocr = PaddleOCRWrapper(lang=ocr_lang)
            print(f"✅ PaddleOCR initialized successfully with language: {ocr_lang}")
        except Exception as e:
            print(f"❌ Error initializing PaddleOCR: {e}")
            paddle_ocr = None
    
    # Note: TrOCR is initialized on-demand due to large model size

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    print("\n🔧 Initializing models on startup...")
    initialize_models()
    print("✅ Startup complete!\n")

@app.get("/api/config")
async def get_config():
    """Get configuration and translations"""
    return {
        "language": language_loader.current_language,
        "translations": language_loader.get_all_translations()
    }

@app.post("/api/set-language")
async def set_language(language: str = Form(...)):
    """Set the current language"""
    if language_loader.set_language(language):
        # Update global verifier language too
        verifier.language = language
        return {
            "success": True,
            "language": language_loader.current_language,
            "translations": language_loader.get_all_translations()
        }
    return {"success": False, "message": "Invalid language"}


# Class mapping and field equivalents are now dynamic based on language
def get_field_equivalents():
    # This function returns the regex patterns for the current language
    # We map them to the standard field names expected by the system
    patterns = language_loader.get_regex_patterns()
    equivalents = {}
    for field, regex_list in patterns.items():
        # In this system, we use the field name itself as the key for equivalents
        # The regex patterns are used for extraction
        equivalents[field] = [field] 
    return equivalents

def get_equivalent_to_standard():
    # Map localized field names back to standard English keys
    # This is a bit complex because we need to know which localized string maps to which standard key
    # For now, we rely on the regex patterns structure which is keyed by standard names
    return {} # Not strictly needed if we use standard keys internally



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
    
    # Basic cleaning
    text = text.strip()
    
    # Remove field name from value if present (using regex patterns)
    patterns = language_loader.get_regex_patterns()
    if field in patterns:
        # This is a simplification. Ideally we use the regex to extract, not just clean.
        pass

    if "Date" in field:
        # Keep Arabic digits if present, convert to standard if needed
        # For now, just standard cleaning
        text = re.sub(r'[^0-9./a-zA-Z\u0660-\u0669 -]', '', text)
        match = re.search(r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b', text)
        return match.group() if match else text

    return re.sub(r'[^A-Za-z0-9\s/\-\u0600-\u06FF]', '', text).strip()

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

def extract_text_with_paddle(image_bytes: bytes) -> str:
    """
    Extract raw text using PaddleOCR.
    Returns the raw extracted text as a string.
    """
    try:
        if paddle_ocr is None:
            print("❌ PaddleOCR not initialized")
            return ""

        print("🔍 Starting PaddleOCR inference...")
        # PaddleOCR expects a file path or numpy array. We'll use numpy array.
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Save to temp file because PaddleOCR works best with paths or we need to adapt the wrapper
        # The wrapper I wrote takes a path. Let's update the wrapper or save to temp.
        # Actually, let's check the wrapper I wrote. It takes image_path. 
        # I should probably update the wrapper to accept numpy array or save to temp here.
        # For now, let's save to a temp file.
        import tempfile
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # File is closed now, safe to write
            cv2.imwrite(temp_path, img)
            extracted_text = paddle_ocr.extract_text(temp_path)
        finally:
            # Clean up
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
        
        # Clean up
        try:
            os.remove(temp_path)
        except:
            pass
        
        if not extracted_text:
            print("No text detected by PaddleOCR")
            return ""
            
        print(f"✅ PaddleOCR extracted text ({len(extracted_text)} chars)")
        
        # Return raw text directly
        return extracted_text
            
    except Exception as e:
        print(f"PaddleOCR error: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""

def extract_text_with_trocr(image_bytes: bytes) -> Tuple[str, Dict[str, float]]:
    """
    Hybrid extraction: Use PaddleOCR for detection (boxes) and TrOCR for recognition (text).
    This is much more accurate for full pages than passing the whole image to TrOCR.
    Returns:
        Tuple[str, Dict[str, float]]: (full_text, line_confidences)
    """
    global trocr_ocr, paddle_ocr
    try:
        # Initialize TrOCR
        if trocr_ocr is None:
            print("📦 Initializing TrOCR (this may take a moment on first run)...")
            try:
                trocr_ocr = TrOCRWrapper()
                print("✅ TrOCR initialized successfully!")
            except Exception as e:
                print(f"❌ Error initializing TrOCR: {e}")
                return ""
        
        # Initialize PaddleOCR if needed (for detection)
        if paddle_ocr is None:
            print("📦 Initializing PaddleOCR for detection...")
            try:
                paddle_ocr = PaddleOCRWrapper(lang='en')
                print("✅ PaddleOCR initialized successfully!")
            except Exception as e:
                print(f"❌ Error initializing PaddleOCR: {e}")
                return ""

        print("🔍 Starting Hybrid TrOCR inference (Paddle Detection + TrOCR Recognition)...")
        
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 1. Detect text regions using PaddleOCR
        # We use the wrapper's extract_data method which handles the API details
        # It returns [{'text':..., 'confidence':..., 'box':...}]
        print("  Calling PaddleOCR for detection...")
        paddle_results = paddle_ocr.extract_data(img)
        
        if not paddle_results:
            print("⚠️ No text regions detected by PaddleOCR")
            return ""
            
        # Extract just the boxes
        boxes = [item['box'] for item in paddle_results]
        print(f"✅ Detected {len(boxes)} text regions")
        
        # 2. Group boxes into lines
        # Simple sorting isn't enough. We need to group boxes that are on the same line.
        # Algorithm:
        # 1. Sort by Y-coordinate
        # 2. Iterate and group boxes that have significant Y-overlap
        
        # Sort by top-left Y first
        boxes.sort(key=lambda b: b[0][1])
        
        lines = []
        current_line = []
        
        for box in boxes:
            if not current_line:
                current_line.append(box)
                continue
            
            # Check if this box belongs to the current line
            # We compare the Y-center of this box with the Y-center of the first box in the line
            box_y_center = (box[0][1] + box[2][1]) / 2
            line_y_center = (current_line[0][0][1] + current_line[0][2][1]) / 2
            
            # If Y-centers are close (within 20px), it's the same line
            if abs(box_y_center - line_y_center) < 20:
                current_line.append(box)
            else:
                # New line started
                lines.append(current_line)
                current_line = [box]
        
        if current_line:
            lines.append(current_line)
            
        print(f"✅ Grouped into {len(lines)} text lines")
        
        # 3. Process each line
        full_text = []
        full_confidences = []
        
        for line_idx, line_boxes in enumerate(lines):
            # Sort boxes in this line by X-coordinate
            line_boxes.sort(key=lambda b: b[0][0])
            
            # Determine the bounding box of the entire line
            min_x = min(b[0][0] for b in line_boxes)
            min_y = min(b[0][1] for b in line_boxes)
            max_x = max(b[2][0] for b in line_boxes)
            max_y = max(b[2][1] for b in line_boxes)
            
            # Add padding (increased to 15px to capture full ascenders/descenders)
            h, w = img.shape[:2]
            pad = 15
            x1 = int(max(0, min_x - pad))
            y1 = int(max(0, min_y - pad))
            x2 = int(min(w, max_x + pad))
            y2 = int(min(h, max_y + pad))
            
            # Crop the full line
            crop = img[y1:y2, x1:x2]
            
            # Preprocessing: Use CLAHE (Contrast Limited Adaptive Histogram Equalization)
            # This enhances contrast without destroying details like aggressive binarization
            try:
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                enhanced = clahe.apply(gray)
                # Denoise slightly
                denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
                crop_rgb = cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)
            except Exception:
                # Fallback
                crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                
            pil_crop = Image.fromarray(crop_rgb)
            
            # Recognize
            text, conf = trocr_ocr.extract_text_from_image(pil_crop)
            if text and len(text.strip()) > 0:
                full_text.append(text)
                full_confidences.append(conf)
                print(f"  Line {line_idx+1}: {text} (Conf: {conf:.2f})")
        
        final_text = "\n".join(full_text)
        print(f"✅ TrOCR extracted {len(final_text)} chars from {len(full_text)} lines")
        
        # Return both text and field confidence map
        # We need to map the confidence scores to the lines
        line_confidences = {}
        for i, text in enumerate(full_text):
            # Use the text content as key (or part of it) to map back later
            # This is a simple heuristic since we don't have field names yet
            line_confidences[text] = full_confidences[i]
            
        return final_text, line_confidences
            
    except Exception as e:
        print(f"TrOCR error: {str(e)}")
        import traceback
        traceback.print_exc()
        return "", {}

def parse_trocr_direct_v2(text: str, line_confidences: Dict[str, float] = None) -> Tuple[Dict, Dict]:
    """
    Direct parser for TrOCR extracted text - returns exactly what was extracted
    without regex cleaning or normalization. Preserves the raw OCR output.
    Also maps confidence scores to fields.
    """
    import re
    
    result = {}
    field_confidences = {}
    
    if line_confidences is None:
        line_confidences = {}
    
    # Field name normalization map
    field_normalization = {
        # Name variations
        'first name': 'Name', 'name': 'Name', 'full name': 'Name', 'given name': 'Name',
        'middle name': 'Middle Name', 'midde name': 'Middle Name',
        'last name': 'Last Name', 'surname': 'Last Name', 'family name': 'Last Name',
        
        # Personal Details
        'gender': 'Gender', 'cender': 'Gender', 'brender': 'Gender', 'sender': 'Gender', 'sex': 'Gender',
        'date of birth': 'Date of Birth', 'dob': 'Date of Birth', 'birth date': 'Date of Birth',
        'nationality': 'Nationality', 'citizenship': 'Nationality',
        'religion': 'Religion', 'occupation': 'Occupation', 'marital status': 'Marital Status',
        'place of birth': 'Place of Birth', 'pob': 'Place of Birth',
        
        # ID Numbers
        'passport no': 'Passport Number', 'passport number': 'Passport Number',
        'id number': 'ID Number', 'identity number': 'ID Number', 'card number': 'Card Number',
        'license number': 'License Number', 'dl no': 'License Number', 'driver license': 'License Number',
        'pan': 'PAN', 'aadhaar': 'Aadhaar', 'ssn': 'SSN',
        
        # Dates
        'issue date': 'Issue Date', 'date of issue': 'Issue Date',
        'expiry date': 'Expiry Date', 'date of expiry': 'Expiry Date', 'valid until': 'Expiry Date', 'valid thru': 'Expiry Date',
        
        # Family
        'father name': 'Father Name', 'fathers name': 'Father Name',
        'mother name': 'Mother Name', 'mothers name': 'Mother Name',
        'spouse name': 'Spouse Name', 'husband name': 'Spouse Name', 'wife name': 'Spouse Name',
        
        # Physical
        'height': 'Height', 'weight': 'Weight', 'eye color': 'Eye Color', 'hair color': 'Hair Color', 'blood group': 'Blood Group',
        
        # Address
        'address line !': 'Address Line 1', 'address line 1': 'Address Line 1', 'road': 'Address Line 1', 'street': 'Address Line 1',
        'address line 2': 'Address Line 2', 'area': 'Address Line 2', 'layout': 'Address Line 2',
        'city': 'City', 'town': 'City',
        'state': 'State', 'province': 'State', 'stale': 'State',
        'country': 'Country',
        'pin code': 'Pin Code', 'pincode': 'Pin Code', 'zip code': 'Pin Code', 'postal code': 'Pin Code',
        
        # Contact
        'phone number': 'Phone', 'phone': 'Phone', 'mobile': 'Phone', 'contact': 'Phone',
        'email id': 'Email', 'email': 'Email', 'e-mail': 'Email',
        
        # Authority
        'authority': 'Authority', 'issuing authority': 'Authority', 'place of issue': 'Place of Issue',
    }
    
    lines = text.strip().split('\n')
    for line in lines:
        original_line = line
        line = line.strip()
        if not line:
            continue
            
        field_name = None
        field_value = None
        
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                field_name = parts[0].strip().lower()
                field_value = parts[1].strip()
        else:
            # Fallback: Check if line starts with a known field name (space separated)
            line_lower = line.lower()
            # Sort keys by length descending to match longest fields first (e.g. "address line 1" before "address")
            sorted_keys = sorted(field_normalization.keys(), key=len, reverse=True)
            
            for key in sorted_keys:
                if line_lower.startswith(key + ' ') or line_lower == key:
                    field_name = key
                    # Extract value: everything after the key
                    # Use case-insensitive replacement or slicing
                    field_value = line[len(key):].strip()
                    break
        
        if field_name and field_value:
                normalized_field = field_normalization.get(field_name, field_name.title())
                field_value = ' '.join(field_value.split())
                
                if normalized_field == 'Email' and '@' not in field_value:
                    field_value = field_value.replace(' great-com', '@gmail.com')
                    field_value = field_value.replace(' great', '@gmail')
                    field_value = field_value.replace('O@', '@')
                    
                result[normalized_field] = field_value
                
                # Map confidence score
                matched_confidence = None
                
                # 1. Exact match
                if line in line_confidences:
                    matched_confidence = line_confidences[line]
                # 2. Original line match
                elif original_line.strip() in line_confidences:
                    matched_confidence = line_confidences[original_line.strip()]
                # 3. Fuzzy match by field name
                else:
                    for conf_line, conf_value in line_confidences.items():
                        if ':' in conf_line:
                            conf_field_name = conf_line.split(':', 1)[0].strip().lower()
                            if conf_field_name == field_name:
                                matched_confidence = conf_value
                                break
                
                if matched_confidence is not None:
                    field_confidences[normalized_field] = matched_confidence
                else:
                    field_confidences[normalized_field] = 0.85
    
    return result, field_confidences

def parse_text_to_json_advanced(text: str, blocks_data: List[Dict] = None) -> Dict:
    """
    Advanced parsing of extracted text into structured JSON format
    Uses both pattern matching and block-based extraction with fuzzy matching
    """
    import difflib
    
    result = {}
    lines = text.split('\n')
    
    # Enhanced field patterns with better matching
    patterns = language_loader.get_regex_patterns()
    
    # Standard fields we expect
    STANDARD_FIELDS = language_loader.get_field_types()
    
    # Helper to find closest standard key
    def get_standard_key(ocr_key):
        ocr_key = ocr_key.lower().strip()
        best_match = None
        max_len = 0
        
        # Direct check with "best match" logic
        for std_key, variations in STANDARD_FIELDS.items():
            if ocr_key in variations:
                return std_key
            for var in variations:
                if var in ocr_key:
                    if len(var) > max_len:
                        max_len = len(var)
                        best_match = std_key
        
        if best_match:
            return best_match
        
        # Fuzzy check
        all_variations = []
        for variations in STANDARD_FIELDS.values():
            all_variations.extend(variations)
            
        matches = difflib.get_close_matches(ocr_key, all_variations, n=1, cutoff=0.7)
        if matches:
            match = matches[0]
            for std_key, variations in STANDARD_FIELDS.items():
                if match in variations:
                    return std_key
        return None

    # --- STEP 1: SPATIAL EXTRACTION (HIGHEST PRIORITY) ---
    # We run this FIRST because it uses geometric proximity which is much more accurate
    # for forms where "Name" and "Age" might be on the same line but separate blocks.
    if blocks_data:
        print("🔍 Running Spatial Extraction...")
        try:
            spatial_results = extract_spatial_key_values(blocks_data, STANDARD_FIELDS)
            if spatial_results:
                print(f"🎯 Spatial extraction found: {spatial_results}")
                result.update(spatial_results)
        except Exception as e:
            print(f"⚠️ Spatial extraction error: {e}")

    # --- STEP 2: REGEX PATTERN MATCHING (FALLBACK) ---
    # Only run for fields we haven't found yet
    for field, field_patterns in patterns.items():
        if field in result:
            continue # Skip if already found by spatial extraction
            
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Clean up value
                value = re.sub(r'[^\w\s@./-\u0600-\u06FF]', '', value).strip()
                if value and len(value) > 1:
                    result[field] = value
                    break
    
    # --- STEP 3: BLOCK-BASED REGEX (SECONDARY FALLBACK) ---
    if blocks_data:
        for block in blocks_data:
            block_text = block.get("text", "")
            if not block_text:
                continue
            
            for field, field_patterns in patterns.items():
                if field in result:
                    continue
                for pattern in field_patterns:
                    match = re.search(pattern, block_text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        value = re.sub(r'[^\w\s@./-\u0600-\u06FF]', '', value).strip()
                        if value and len(value) > 1:
                            result[field] = value
                            break
    
    # --- STEP 4: LINE-BY-LINE FUZZY MATCHING (LAST RESORT) ---
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key_raw = parts[0].strip()
                value = parts[1].strip()
                
                # Clean value
                value = value.replace('"', '').replace("'", "").strip(" .,!")
                val_lower = value.lower()
                
                # Email fixes
                if '@' in value or 'gmail' in val_lower:
                    value = value.replace('Gymail', 'gmail').replace(' ', '')
                    if '@' not in value and 'gmail' in value:
                        value = value.replace('gmail', '@gmail')
                
                std_key = get_standard_key(key_raw)
                
                if std_key:
                    # Only overwrite if we don't have it, or if the current value looks wrong
                    if std_key not in result:
                        result[std_key] = value
                    elif std_key == 'Name':
                        # Special handling for Name: if we have a very long name (likely concatenated)
                        # and this line gives a shorter, cleaner name, take it.
                        current_val = result[std_key]
                        if len(current_val) > len(value) + 10 and value in current_val:
                             result[std_key] = value
                else:
                    clean_key = key_raw.title().replace('_', ' ')
                    if clean_key not in result:
                        result[clean_key] = value

    # --- FINAL CLEANUP ---
    cleaned_result = {}
    field_metadata = {}
    
    # Normalize keys
    for key, value in result.items():
        std_key = get_standard_key(key)
        final_key = std_key if std_key else key.title().replace('_', ' ')
        
        # Deduplication: prefer existing value if it's "better" (heuristic)
        if final_key in cleaned_result:
            # If we already have a value, usually keep it (since we prioritized spatial)
            # But if the new value is an Email and the old one wasn't, take the email
            if 'Email' in final_key and '@' in value and '@' not in cleaned_result[final_key]:
                cleaned_result[final_key] = value
        else:
            cleaned_result[final_key] = value

    # Remove subset keys (e.g. "Name" vs "First Name")
    keys = list(cleaned_result.keys())
    for k1 in keys:
        for k2 in keys:
            if k1 != k2 and k1 in k2 and k1 in cleaned_result and k2 in cleaned_result:
                # e.g. k1="Name", k2="First Name". Usually keep "Name" if it covers everything.
                # But here we just want to avoid duplicates.
                pass

    # Build metadata
    for key, value in cleaned_result.items():
        if value and len(value.strip()) > 0:
            confidence = 0.95 if blocks_data else 0.85
            source = "spatial" if blocks_data else "regex"
            field_metadata[key] = {"confidence": confidence, "source": source}
    
    # FINAL CLEANUP: Strip trailing field names from values
    # e.g. "Ananya SharmaAge" -> "Ananya Sharma"
    print(f"🧹 CLEANUP: Checking {len(cleaned_result)} fields for trailing keys...")
    all_field_variations = []
    for variations in STANDARD_FIELDS.values():
        all_field_variations.extend([v.lower() for v in variations])
    
    for key, value in list(cleaned_result.items()):
        if not value or not isinstance(value, str):
            continue
        original_value = value
        value_cleaned = value.replace('\n', ' ').replace('\r', ' ').strip()
        
        for field_name in all_field_variations:
            if value_cleaned.lower().endswith(field_name):
                potential_clean = value_cleaned[:-(len(field_name))].strip()
                if len(potential_clean) > 2:
                    print(f"   ✂️ '{key}': '{value}' -> '{potential_clean}' (stripped '{field_name}')")
                    cleaned_result[key] = potential_clean
                    value_cleaned = potential_clean
    
    return cleaned_result, field_metadata
def process_image(image_bytes: bytes):
    """Process image and extract text fields using PaddleOCR"""
    try:
        initialize_models()
    except Exception as e:
        raise Exception(f"Failed to initialize models: {str(e)}")
    
    # Convert bytes to numpy array
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        raise Exception(f"Failed to decode image: {str(e)}")
    
    if img is None:
        raise Exception("Invalid image file - could not decode")
    
    if paddle_ocr is None:
        raise Exception("PaddleOCR not initialized.")
    
    # Save to temp file for PaddleOCR (wrapper expects path)
    import tempfile
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_path = temp_file.name
        cv2.imwrite(temp_path, img)
        
        # Extract data using PaddleOCR
        # Returns [{'text': '...', 'confidence': 0.99, 'box': [[x1,y1], ...]}, ...]
        print("🔍 Starting PaddleOCR extraction...")
        ocr_results = paddle_ocr.extract_data(temp_path)
        print(f"✅ PaddleOCR found {len(ocr_results)} text regions")
        
    except Exception as e:
        print(f"❌ PaddleOCR error: {e}")
        ocr_results = []
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

    # Aggregate full text
    general_text = [item['text'] for item in ocr_results if item['text'].strip()]
    full_text = "\n".join(general_text)
    
    # DEBUG: Show raw OCR output
    print("\n" + "=" * 60)
    print("🔍 DEBUG: RAW OCR TEXT EXTRACTED BY PADDLEOCR")
    print("=" * 60)
    print(full_text)
    print("=" * 60 + "\n")
    
    # Extract structured fields from full text (WITH ENHANCED LOGGING)
    print("🔍 Parsing structured fields with enhanced logging...")
    extracted_fields, extracted_metadata = parse_text_to_json_with_logging(
        text=full_text,
        blocks_data=ocr_results,
        patterns=language_loader.get_regex_patterns(),
        STANDARD_FIELDS=language_loader.get_field_types(),
        extract_spatial_key_values_func=extract_spatial_key_values
    )
    
    # FALLBACK: Catch standalone fields that spatial extraction missed
    print("🔍 Checking for missed standalone fields...")
    
    # Fallback for Aadhaar (12 digits with spaces)
    if 'Aadhaar' not in extracted_fields:
        aadhaar_match = re.search(r'\b(\d{4}\s\d{4}\s\d{4})\b', full_text)
        if aadhaar_match:
            extracted_fields['Aadhaar'] = aadhaar_match.group(1)
            print(f"✅ Fallback: Found Aadhaar: {aadhaar_match.group(1)}")
    
    
    # DEBUG: Show what was extracted before cleaning
    print("\n" + "=" * 60)
    print("📋 EXTRACTED FIELDS BEFORE CLEANING:")
    print("=" * 60)
    for key, value in extracted_fields.items():
        print(f"  {key}: {value}")
    print("=" * 60 + "\n")
    
    # POST-PROCESSING: Clean the extracted data
    print("🧹 Cleaning extracted data...")
    try:
        from data_cleaner import clean_ocr_data, get_data_quality
        cleaned_fields = clean_ocr_data(extracted_fields)
        quality_metrics = get_data_quality(cleaned_fields, extracted_fields)
        print(f"✅ Data cleaned: {quality_metrics['valid_fields']}/{quality_metrics['total_extracted']} fields retained")
        if quality_metrics['removed_field_names']:
            print(f"   Removed: {', '.join(quality_metrics['removed_field_names'])}")
        
        # Use cleaned fields instead of raw extracted_fields
        extracted_fields = cleaned_fields
        
        # Add quality info to metadata
        extracted_metadata['data_quality'] = quality_metrics
    except Exception as e:
        print(f"⚠️ Data cleaning error (using uncleaned data): {e}")
        import traceback
        traceback.print_exc()
    
    # FALLBACK FOR NAME - Run AFTER cleaning in case cleaner removed institutional text
    if 'Name' not in extracted_fields:
        print("🔍 Name missing after cleaning, trying fallback...")
        
        # Strategy 1: Look for name near DOB pattern (common in Aadhaar)
        dob_section = re.search(r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*.*?\s*(?:DOB|Date of Birth|जन्म)', full_text, re.IGNORECASE | re.DOTALL)
        if dob_section:
            potential_name = dob_section.group(1)
            if not any(word in potential_name.lower() for word in ['government', 'india', 'of']):
                extracted_fields['Name'] = potential_name
                print(f"✅ Fallback Strategy 1: Found Name near DOB: {potential_name}")
        
        # Strategy 2: Find any proper capitalized name (if strategy 1 failed)
        if 'Name' not in extracted_fields:
            name_matches = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', full_text)
            for name in name_matches:
                name_lower = name.lower().replace(' ', '')
                # Skip institutional/header words
                bad_words = ['government', 'india', 'of', 'bharath', 'bharat', 'republic']
                if not any(word in name_lower for word in bad_words) and len(name) > 5:
                    extracted_fields['Name'] = name
                    print(f"✅ Fallback Strategy 2: Found Name: {name}")
                    break
    
    # Check if ID card found (heuristic based on fields)
    found_idcard = len(extracted_fields) > 0
    
    return {
        "general_text": general_text,
        "extracted_fields": extracted_fields,
        "extracted_metadata": extracted_metadata,
        "found_idcard": found_idcard,
        "raw_text": full_text
    }

@app.get("/")
async def root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "OCR API is running. Please ensure index.html exists in the root directory."}

@app.get("/api/config")
async def get_config():
    """Get current configuration and translations"""
    return {
        "language": language_loader.current_language,
        "translations": language_loader.get_all_translations(),
        "supported_languages": language_loader.SUPPORTED_LANGUAGES
    }

@app.post("/api/set-language")
async def set_language(language: str = Form(...)):
    """Set application language and reload models"""
    global paddle_ocr
    
    if language_loader.set_language(language):
        # Update verifier language
        verifier.set_language(language)

        # Reload PaddleOCR model with new language
        try:
            print(f"🔄 Reloading PaddleOCR with language: {language}")
            paddle_ocr = PaddleOCRWrapper(lang=language if language in ['en', 'ch', 'fr', 'german', 'korean', 'japan'] else 'en')
            print("✅ PaddleOCR reloaded successfully!")
            
            return {
                "success": True,
                "language": language,
                "translations": language_loader.get_all_translations()
            }
        except Exception as e:
            print(f"❌ Error reloading PaddleOCR: {e}")
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"Failed to reload models: {str(e)}"}
            )
    else:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Unsupported language"}
        )

@app.get("/api/test-json")
async def test_json():
    """Test endpoint to verify JSON response format"""
    test_data = {
        "success": True,
        "extracted_fields": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "1234567890"
        },
        "general_text": ["Test line 1", "Test line 2"],
        "found_idcard": True,
        "ai_converted": False
    }
    return JSONResponse(content=test_data)

def convert_pdf_to_images(pdf_bytes: bytes) -> List[np.ndarray]:
    """Convert PDF pages to images"""
    try:
        import fitz  # PyMuPDF
        import io
        
        # Open PDF from bytes
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        images = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            # Render page to image (pixmap)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            # Convert to numpy array
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            img_array = np.array(img)
            # Convert RGB to BGR for OpenCV
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            images.append(img_array)
        
        pdf_document.close()
        return images
    except ImportError:
        # Fallback to pdf2image if PyMuPDF not available
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(pdf_bytes, dpi=200)
            image_arrays = []
            for img in images:
                img_array = np.array(img)
                if len(img_array.shape) == 3:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                image_arrays.append(img_array)
            return image_arrays
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="PDF processing requires PyMuPDF or pdf2image. Install with: pip install PyMuPDF pdf2image"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting PDF: {str(e)}")

def process_pdf(pdf_bytes: bytes, use_openai: bool = False) -> Dict:
    """Process PDF file - convert pages to images and extract text"""
    try:
        # Convert PDF to images
        page_images = convert_pdf_to_images(pdf_bytes)
        
        if not page_images:
            return {
                "success": False,
                "error": "Could not extract pages from PDF"
            }
        
        print(f"Processing PDF with {len(page_images)} pages")
        
        # Process each page
        all_extracted_fields = {}
        all_general_text = []
        found_idcard = False
        
        for page_num, img_array in enumerate(page_images):
            print(f"Processing page {page_num + 1}/{len(page_images)}")
            
            # Convert numpy array to bytes for processing
            _, img_encoded = cv2.imencode('.png', img_array)
            img_bytes = img_encoded.tobytes()
            
            if use_openai:
                print(f"Using combined OCR for page {page_num + 1}")
                
                # Run PaddleOCR for full text
                try:
                    paddle_page_text = extract_text_with_paddle(img_bytes)
                    if paddle_page_text:
                        all_general_text.append(f"--- Page {page_num + 1} (PaddleOCR) ---")
                        all_general_text.append(paddle_page_text)
                except Exception as e:
                    print(f"⚠️ PaddleOCR error on page {page_num + 1}: {e}")
            else:
                _, img_encoded = cv2.imencode('.png', img_array)
                img_bytes = img_encoded.tobytes()
                
                page_result = process_image(img_bytes)
                if page_result.get('extracted_fields'):
                    all_extracted_fields.update(page_result['extracted_fields'])
                if page_result.get('general_text'):
                    all_general_text.extend(page_result['general_text'])
                if page_result.get('found_idcard'):
                    found_idcard = True
        
        
        return {
            "success": True,
            "extracted_fields": all_extracted_fields,
            "general_text": all_general_text,
            "found_idcard": found_idcard,
            "total_pages": len(page_images),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.get("/api/ocr_stream")
async def ocr_stream(
    image_id: str = Query(...),
    use_openai: bool = Query(False),
    use_trocr: bool = Query(False)
):
    """
    Stream OCR results with confidence scores as Server-Sent Events (SSE).
    Progressive updates for each detected region.
    """
    import asyncio
    import time
    import tempfile
    
    async def event_generator():
        try:
            # Retrieve uploaded image from cache
            if image_id not in uploaded_images:
                yield f"event: error\ndata: {{\"error\": \"Image not found. Upload image first.\"}}\n\n"
                return
            
            image_bytes = uploaded_images[image_id]
            
            # Initialize models if needed
            initialize_models()
            
            global trocr_ocr, paddle_ocr
            
            # Initialize specific models if requested
            if use_trocr and trocr_ocr is None:
                try:
                    print("Initializing TrOCR for streaming...")
                    trocr_ocr = TrOCRWrapper()
                except Exception as e:
                    print(f"Failed to init TrOCR: {e}")
            
            if use_openai and paddle_ocr is None:
                try:
                    print("Initializing PaddleOCR for streaming...")
                    paddle_ocr = PaddleOCRWrapper(lang=SELECTED_LANGUAGE if SELECTED_LANGUAGE in ['en', 'ch', 'fr', 'german', 'korean', 'japan'] else 'en')
                except Exception as e:
                    print(f"Failed to init PaddleOCR: {e}")

            # Use PaddleOCR for detection and recognition
            # We can use extract_data which gives us everything we need
            
            # Decode image first (needed for cropping later)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                yield f"event: error\ndata: {{\"error\": \"Failed to decode image\"}}\n\n"
                return

            import tempfile
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                    tf.write(image_bytes)
                    temp_path = tf.name
                
                print("🔍 Starting PaddleOCR streaming extraction...")
                paddle_results = paddle_ocr.extract_data(temp_path)
                print(f"✅ PaddleOCR found {len(paddle_results)} regions for streaming")
                
            except Exception as e:
                print(f"❌ PaddleOCR streaming error: {e}")
                paddle_results = []
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass

            regions = []
            region_idx = 0
            
            for item in paddle_results:
                try:
                    text = item['text']
                    confidence = item['confidence']
                    box = item['box'] # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    
                    # Convert polygon box to rect [x, y, w, h]
                    xs = [p[0] for p in box]
                    ys = [p[1] for p in box]
                    x1, y1 = int(min(xs)), int(min(ys))
                    x2, y2 = int(max(xs)), int(max(ys))
                    w, h = x2 - x1, y2 - y1
                    
                    # Crop for quality metrics (optional, but good for consistency)
                    crop = img[y1:y2, x1:x2]
                    _, crop_encoded = cv2.imencode('.png', crop)
                    crop_bytes = crop_encoded.tobytes()
                    
                    ocr_method_used = 'paddle'
                    avg_ocr_conf = confidence
                    
                    # Compute confidence using ocr_confidence module
                    confidence_data = ocr_confidence.get_region_confidence(
                        ocr_result=(text, avg_ocr_conf) if text else "",
                        crop_image_bytes=crop_bytes,
                        ocr_method=ocr_method_used
                    )
                    
                    # Create region data
                    region_id = f"r{region_idx}"
                    region = {
                        "region_id": region_id,
                        "box": [x1, y1, x2 - x1, y2 - y1],  # [x, y, w, h]
                        "text": confidence_data['text'],
                        "confidence": confidence_data['confidence'],
                        "ocr_confidence": confidence_data['ocr_confidence'],
                        "blur_score": confidence_data['blur_score'],
                        "lighting_score": confidence_data['lighting_score'],
                        "image_quality": confidence_data['image_quality'],
                        "text_quality": confidence_data['text_quality'],
                        "suggestions": confidence_data['suggestions']
                    }
                    
                    regions.append(region)
                    region_idx += 1
                    
                    # Stream this region
                    region_json = json.dumps(region)
                    yield f"event: region\ndata: {region_json}\n\n"
                    
                    # Small delay to simulate progressive rendering
                    await asyncio.sleep(0.01)
                    
                except Exception as e:
                    print(f"Error processing region: {e}")
                    continue
            
            # Calculate document-level confidence
            doc_confidence = ocr_confidence.compute_document_confidence(regions)
            
            # Cache regions for later correction
            region_data_cache[image_id] = regions
            
            # Aggregate text from all regions
            all_text_lines = [r['text'] for r in regions if r['text'].strip()]
            full_text = "\n".join(all_text_lines)
            
            # Parse text into structured fields
            extracted_fields, extracted_metadata = parse_text_to_json_advanced(full_text)
            
            # Send final done event with full data
            done_data = {
                "document_confidence": doc_confidence,
                "total_regions": len(regions),
                "extracted_fields": extracted_fields,
                "extracted_metadata": extracted_metadata,
                "general_text": all_text_lines,
                "success": True,
                "quality": {
                    "overall_score": doc_confidence * 100,
                    "blur_score": sum(r['blur_score'] for r in regions) / len(regions) if regions else 0,
                    "lighting_score": sum(r['lighting_score'] for r in regions) / len(regions) if regions else 0
                }
            }
            done_json = json.dumps(done_data)
            yield f"event: done\ndata: {done_json}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_data = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/region_correct")
async def region_correct(
    image_id: str = Form(...),
    region_id: str = Form(...),
    corrected_text: str = Form(...)
):
    """
    Update a region's text after manual correction and recalculate confidence.
    """
    try:
        # Get cached regions for this image
        if image_id not in region_data_cache:
            raise HTTPException(status_code=404, detail="Image regions not found. Please process image first.")
        
        regions = region_data_cache[image_id]
        
        # Find the region
        region_found = False
        for region in regions:
            if region['region_id'] == region_id:
                # Update text and set confidence to 1.0 (human-corrected)
                region['text'] = corrected_text
                region['confidence'] = 1.0
                region['ocr_confidence'] = 1.0
                region['text_quality'] = 1.0
                # Keep image quality metrics as they were
                region_found = True
                break
        
        if not region_found:
            raise HTTPException(status_code=404, detail=f"Region {region_id} not found")
        
        # Recalculate document confidence
        doc_confidence = ocr_confidence.compute_document_confidence(regions)
        
        # Update cache
        region_data_cache[image_id] = regions
        
        return JSONResponse(content={
            "success": True,
            "region_id": region_id,
            "confidence": 1.0,
            "document_confidence": doc_confidence
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




def extract_text_with_paddle(image_bytes: bytes) -> str:
    global paddle_ocr
    if paddle_ocr is None:
        print("Initializing PaddleOCR...")
        paddle_ocr = PaddleOCRWrapper(lang=SELECTED_LANGUAGE if SELECTED_LANGUAGE in ['en', 'ch', 'fr', 'german', 'korean', 'japan'] else 'en')
    
    import tempfile
    import os
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            tf.write(image_bytes)
            temp_path = tf.name
        
        return paddle_ocr.extract_text(temp_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


def extract_text_with_tesseract(image_bytes: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
        import io
        
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except ImportError:
        print("pytesseract not installed")
        return ""
    except Exception as e:
        print(f"Tesseract error: {e}")
        return ""

def parse_trocr_direct(text: str, confidence: float) -> Tuple[Dict, Dict]:
    extracted_fields, extracted_metadata = parse_text_to_json_advanced(text)
    
    # Create field confidences dict
    field_confidences = {}
    for key in extracted_fields:
        field_confidences[key] = confidence
        
    return extracted_fields, field_confidences

@app.post("/api/extract")
async def extract_for_mosip(
    file: UploadFile = File(...)
):
    """
    OCR extraction endpoint for MOSIP integration.
    Returns extracted data in format compatible with MOSIP pre-registration forms.
    """
    import traceback
    
    try:
        file_bytes = await file.read()
        file_name = file.filename.lower()
        
        # Determine if PDF or image
        if file_name.endswith('.pdf'):
            # Handle PDF
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(file_bytes, dpi=200)
            if images:
                import io
                buffer = io.BytesIO()
                images[0].save(buffer, format='PNG')
                image_bytes = buffer.getvalue()
            else:
                return JSONResponse(content={
                    "success": False,
                    "error": "Could not convert PDF"
                }, status_code=400)
        else:
            image_bytes = file_bytes
        
        # Process with OCR - returns a dict with extracted_fields
        result = process_image(image_bytes)
        
        # Get extracted fields from result
        extracted_fields = result.get("extracted_fields", {})
        
        # Format response for MOSIP with confidence scores
        response_data = {}
        for field, value in extracted_fields.items():
            response_data[field] = {
                "value": value,
                "confidence": 0.85  # Default confidence
            }
        
        return {
            "success": True,
            "extracted_data": response_data,
            "processing_time": 1.5
        }
        
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    use_openai: Optional[str] = Form(None),
    stream: Optional[str] = Form(None),
    use_trocr: Optional[str] = Form(None)
):
    """Upload and process image or PDF for OCR"""
    import traceback
    import sys
    
    # Force flush output immediately
    sys.stdout.flush()
    sys.stderr.flush()
    
    try:
        print("UPLOAD REQUEST RECEIVED")
        sys.stdout.flush()
        
        contents = await file.read()
        filename = file.filename or "uploaded_file"
        
        # Check if streaming mode is requested
        stream_mode = stream and stream.lower() == 'true'
        
        print(f"File: {filename}, Size: {len(contents)} bytes, Stream: {stream_mode}")
        sys.stdout.flush()
        
        # If streaming mode, save image and return image_id
        if stream_mode and not filename.lower().endswith('.pdf'):
            import datetime
            image_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_filename = f"{timestamp}_{image_id}.jpg"
            filepath = os.path.join("uploads", save_filename)
            
            with open(filepath, "wb") as f:
                f.write(contents)
            
            # Cache image bytes for streaming endpoint
            uploaded_images[image_id] = contents
            
            # Construct stream URL with flags
            use_openai_flag = use_openai and use_openai.lower() == 'true'
            use_trocr_flag = use_trocr and use_trocr.lower() == 'true'
            
            stream_query = f"?image_id={image_id}"
            if use_openai_flag:
                stream_query += "&use_openai=true"
            if use_trocr_flag:
                stream_query += "&use_trocr=true"
            
            return JSONResponse(content={
                "success": True,
                "image_id": image_id,
                "image_path": f"/uploads/{save_filename}",
                "stream_url": f"/api/ocr_stream{stream_query}"
            })
        
        # Check if it's a PDF
        is_pdf = filename.lower().endswith('.pdf')
        use_openai_flag = use_openai and use_openai.lower() == 'true'
        use_trocr_flag = use_trocr and use_trocr.lower() == 'true'
        
        print(f"Is PDF: {is_pdf}, Use OpenAI: {use_openai_flag}, Use TrOCR: {use_trocr_flag}")
        sys.stdout.flush()
        
        # Calculate quality score for images
        quality_report = None
        if not is_pdf:
            print("Calculating image quality score...")
            quality_report = quality_score.get_quality_report(contents)
            print(f"Quality Report: {quality_report}")
            sys.stdout.flush()
        
        if is_pdf:
            print("Processing PDF...")
            sys.stdout.flush()
            result = process_pdf(contents, use_openai=use_openai_flag)
            if not result.get("success"):
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": result.get("error", "PDF processing failed")}
                )
            result["filename"] = filename
            result["file_type"] = "pdf"
            print("PDF processing successful")
            sys.stdout.flush()
            return JSONResponse(content={"success": True, **result})
        
        # Process image with TrOCR for handwritten documents
        if use_trocr_flag:
            print("Using TrOCR for HANDWRITTEN text...")
            sys.stdout.flush()
            
            # Run TrOCR for handwritten text
            try:
                trocr_text, trocr_line_confidences = extract_text_with_trocr(contents)
                print(f"✅ TrOCR extracted {len(trocr_text)} chars for handwritten text")
                print(f"🔍 Raw line confidences: {trocr_line_confidences}")
                
                # Parse the extracted text using v2 parser (with improved confidence mapping)
                parsed_fields, field_confidences = parse_trocr_direct_v2(trocr_text, trocr_line_confidences)
                print(f"🔍 Parsed field confidences: {field_confidences}")
                
                # POST-PROCESSING: Clean the extracted data
                print("🧹 Cleaning extracted TrOCR data...")
                try:
                    from data_cleaner import clean_ocr_data, get_data_quality
                    cleaned_fields = clean_ocr_data(parsed_fields)
                    quality_metrics = get_data_quality(cleaned_fields, parsed_fields)
                    print(f"✅ Data cleaned: {quality_metrics['valid_fields']}/{quality_metrics['total_extracted']} fields retained")
                    if quality_metrics.get('removed_field_names'):
                        print(f"   Removed: {', '.join(quality_metrics['removed_field_names'])}")
                    
                    # Use cleaned fields
                    parsed_fields = cleaned_fields
                    parsed_metadata = {'data_quality': quality_metrics}
                except Exception as clean_err:
                    print(f"⚠️ Data cleaning error (using uncleaned data): {clean_err}")
                    parsed_metadata = {}
                
                # Return TrOCR results with proper confidence format
                return JSONResponse(content={
                    "success": True,
                    "filename": filename,
                    "extracted_fields": parsed_fields,
                    "extracted_metadata": parsed_metadata,
                    "trocr_confidence": field_confidences,  # Changed from field_confidence to trocr_confidence
                    "general_text": [trocr_text],
                    "trocr_text": trocr_text,
                    "found_idcard": len(parsed_fields) > 0,
                    "method": "trocr_handwritten",
                    "file_type": "image",
                    "quality": quality_report
                })
            except Exception as trocr_err:
                print(f"⚠️ TrOCR error: {str(trocr_err)}")
                import traceback
                traceback.print_exc()
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": f"TrOCR processing failed: {str(trocr_err)}"
                    }
                )
        
        # Process image with BOTH methods when PaddleOCR is enabled  
        if use_openai_flag:
            sys.stdout.flush()
            
            
            # Run PaddleOCR for full text
            try:
                paddle_text = extract_text_with_paddle(contents)
                print(f"✅ PaddleOCR extracted {len(paddle_text)} chars")
            except Exception as paddle_err:
                print(f"⚠️ PaddleOCR error: {str(paddle_err)}")
                paddle_text = ""
            
            # Also run TrOCR to calculate confidence scores for printed text
            trocr_confidences = {}
            try:
                print("🔍 Running TrOCR for confidence scoring on printed text...")
                trocr_text, trocr_line_confidences = extract_text_with_trocr(contents)
                print(f"✅ TrOCR extracted {len(trocr_text)} chars for confidence calculation")
                print(f"🔍 Raw line confidences: {trocr_line_confidences}")
                
                # Parse TrOCR results to get field-level confidences
                trocr_fields, trocr_field_confidences = parse_trocr_direct_v2(trocr_text, trocr_line_confidences)
                print(f"🔍 Parsed field confidences: {trocr_field_confidences}")
                
                # Extract just the numeric confidence values
                # trocr_field_confidences should be {field_name: confidence_value}
                for field_name, conf_value in trocr_field_confidences.items():
                    # If conf_value is a dict (wrong format), try to extract a number
                    if isinstance(conf_value, dict):
                        # Try to find a numeric value in the dict
                        # This handles cases where the confidence is nested
                        numeric_values = [v for v in conf_value.values() if isinstance(v, (int, float))]
                        if numeric_values:
                            trocr_confidences[field_name] = max(numeric_values)  # Use the highest confidence
                        else:
                            trocr_confidences[field_name] = 0.85  # Default
                    elif isinstance(conf_value, (int, float)):
                        trocr_confidences[field_name] = conf_value
                    else:
                        trocr_confidences[field_name] = 0.85  # Default
                
                print(f"📊 TrOCR confidence scores: {trocr_confidences}")
            except Exception as trocr_err:
                print(f"⚠️ TrOCR confidence calculation error: {str(trocr_err)}")
                import traceback
                traceback.print_exc()
                # Continue without TrOCR confidence scores
            
            # Also extract structured blocks data for spatial extraction
            paddle_blocks = []
            try:
                # Use PaddleOCR wrapper to get blocks with bounding boxes
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                    temp_path = temp_file.name
                    temp_file.write(contents)
                paddle_blocks = paddle_ocr.extract_data(temp_path)
                os.remove(temp_path)
                print(f"✅ Got {len(paddle_blocks)} blocks for spatial extraction")
            except Exception as e:
                print(f"⚠️ Could not get blocks: {e}")
            
            # Parse text into structured fields WITH blocks for spatial extraction
            extracted_fields, extracted_metadata = parse_text_to_json_advanced(paddle_text, blocks_data=paddle_blocks)
            
            # POST-PROCESSING: Clean the extracted data
            print("🧹 Cleaning extracted data...")
            try:
                from data_cleaner import clean_ocr_data, get_data_quality
                cleaned_fields = clean_ocr_data(extracted_fields)
                quality_metrics = get_data_quality(cleaned_fields, extracted_fields)
                print(f"✅ Data cleaned: {quality_metrics['valid_fields']}/{quality_metrics['total_extracted']} fields retained")
                if quality_metrics.get('removed_field_names'):
                    print(f"   Removed: {', '.join(quality_metrics['removed_field_names'])}")
                
                # Use cleaned fields instead of raw extracted_fields
                extracted_fields = cleaned_fields
                
                # Add quality info to metadata
                extracted_metadata['data_quality'] = quality_metrics
            except Exception as clean_err:
                print(f"⚠️ Data cleaning error (using uncleaned data): {clean_err}")
                import traceback
                traceback.print_exc()
            
            # Merge TrOCR confidence scores into metadata
            # For each field extracted by PaddleOCR, add TrOCR confidence if available
            for field_name in extracted_fields:
                if field_name in trocr_confidences:
                    # Update metadata with TrOCR confidence (just the numeric value)
                    if field_name not in extracted_metadata:
                        extracted_metadata[field_name] = {}
                    extracted_metadata[field_name]['trocr_confidence'] = trocr_confidences[field_name]
            
            # Construct best_result manually
            best_result = {
                "extracted_fields": extracted_fields,
                "extracted_metadata": extracted_metadata,
                "general_text": [paddle_text] if paddle_text else [],
                "found_idcard": len(extracted_fields) > 0,
                "best_method": "paddle",
                "comparison": "PaddleOCR selected via flag"
            }
            
            # Compare and select best result
            print(f"🏆 Best OCR method: PaddleOCR")
            
            # Return best result with both options available
            return JSONResponse(content={
                "success": True,
                "filename": filename,
                "extracted_fields": best_result.get("extracted_fields", {}),
                "extracted_metadata": best_result.get("extracted_metadata", {}),
                "trocr_confidence": trocr_confidences,  # Add TrOCR confidence scores
                "general_text": best_result.get("general_text", []),
                "paddle_text": paddle_text,
                "found_idcard": best_result.get("found_idcard", False),
                "tesseract_converted": True,
                "method": "combined_auto_best",
                "best_method": best_result.get("best_method"),
                "comparison": best_result.get("comparison"),
                "file_type": "image",
                "quality": quality_report
            })
        
        sys.stdout.flush()
        try:
            result = process_image(contents)
            result["file_type"] = "image"
            sys.stdout.flush()
            return JSONResponse(content={
                "success": True,
                "filename": filename,
                "quality": quality_report,
                "extracted_metadata": result.get("extracted_metadata", {}),
                **result
            })
        except Exception as img_err:
            error_msg = str(img_err)
            error_type = type(img_err).__name__
            print("\n" + "=" * 70)
            print(f"ERROR in process_image: {error_type}: {error_msg}")
            print("TRACEBACK:")
            traceback.print_exc()
            print("=" * 70 + "\n")
            sys.stdout.flush()
            sys.stderr.flush()
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"Image processing failed: {error_msg}",
                    "error_type": error_type
                }
            )
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"EXCEPTION in upload_image: {error_type}: {error_msg}")
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"{error_type}: {error_msg}",
                "detail": "Check server console for full traceback"
            }
        )

@app.post("/api/camera_upload")
async def camera_upload(
    image: UploadFile = File(...),
    use_openai: Optional[str] = Form(None),
    stream: Optional[str] = Form(None)
):
    """Handle camera captured image upload"""
    import sys
    import shutil
    from datetime import datetime
    
    try:
        print("\n" + "=" * 70)
        print("CAMERA UPLOAD RECEIVED")
        print("=" * 70)
        
        # Create uploads directory if not exists
        os.makedirs("uploads", exist_ok=True)
        
        # Check if streaming mode is requested
        stream_mode = stream and stream.lower() == 'true'
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_id = str(uuid.uuid4()) if stream_mode else ""
        filename = f"camera_{timestamp}_{image_id}.jpg" if stream_mode else f"camera_{timestamp}.jpg"
        filepath = os.path.join("uploads", filename)
        
        # Read content
        contents = await image.read()
        
        # Save to file
        with open(filepath, "wb") as f:
            f.write(contents)
            
        print(f"Saved camera image to {filepath}, Stream: {stream_mode}")
        
        # Calculate quality score
        print("Calculating image quality score...")
        quality_report = quality_score.get_quality_report(contents)
        print(f"Quality Report: {quality_report}")
        
        # If streaming mode, cache image and return image_id
        if stream_mode:
            uploaded_images[image_id] = contents
            return JSONResponse(content={
                "success": True,
                "image_id": image_id,
                "image_path": f"/uploads/{filename}",
                "stream_url": f"/api/ocr_stream?image_id={image_id}",
                "quality": quality_report
            })
        # Process image
        use_openai_flag = use_openai and use_openai.lower() == 'true'
        
        if use_openai_flag:
            
            
            # Run Tesseract for full text
            try:
                tesseract_text = extract_text_with_tesseract(contents)
                print(f"✅ Tesseract extracted {len(tesseract_text)} chars")
            except Exception as tesseract_err:
                print(f"⚠️ Tesseract error: {str(tesseract_err)}")
                tesseract_text = ""
            
            result = {
                "tesseract_text": tesseract_text,  # Full text from Tesseract
                "tesseract_converted": True
            }
        else:
            result = process_image(contents)
            
        result["file_type"] = "image"
        result["success"] = True
        result["image_path"] = f"/uploads/{filename}"
        result["quality"] = quality_report
        
        return JSONResponse(content=result)

    except Exception as e:
        print(f"❌ Error processing camera upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False, 
                "error": str(e),
                "detail": str(e)
            }
        )

@app.post("/api/verify")
async def verify_data(
    extracted_data: str = Form(...),
    original_data: Optional[str] = Form(None),
    ocr_text_block: Optional[str] = Form(None)
):
    """
    Advanced OCR Verification Engine
    Validates and verifies structured data extracted from scanned documents
    """
    try:
        # Validate extracted_data is not empty
        if not extracted_data or not extracted_data.strip():
            raise HTTPException(status_code=400, detail="extracted_data cannot be empty")
        
        # Parse extracted data with better error handling
        try:
            structured_data = json.loads(extracted_data.strip())
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid JSON in extracted_data: {str(e)}. Please provide valid JSON format like {{\"field\": \"value\"}}"
            )
        
        # Validate it's a dictionary/object
        if not isinstance(structured_data, dict):
            raise HTTPException(
                status_code=400,
                detail=f"extracted_data must be a JSON object/dictionary, got {type(structured_data).__name__}"
            )
        
        if len(structured_data) == 0:
            raise HTTPException(status_code=400, detail="extracted_data cannot be an empty object")
        
        # Parse original data if provided
        original_dict = None
        if original_data and original_data.strip():
            try:
                original_dict = json.loads(original_data.strip())
                if not isinstance(original_dict, dict):
                    # If not a dict, wrap it
                    original_dict = {"raw_text": str(original_dict)}
            except json.JSONDecodeError:
                # If not JSON, treat as string
                original_dict = {"raw_text": original_data.strip()}
        
        # Initialize verifier
        verifier = OCRVerifier()
        
        # Perform verification
        result = verifier.verify_all_fields(
            structured_data=structured_data,
            original_data=original_dict,
            ocr_text_block=ocr_text_block.strip() if ocr_text_block else None
        )
        
        return JSONResponse(content={
            "success": True,
            "cleaned_data": result["cleaned_data"],
            "verification_report": result["verification_report"],
            "overall_verification_status": result["overall_verification_status"],
            "summary": result["summary"]
        })
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")

@app.post("/api/autofill")
async def autofill_form(
    form_fields: str = Form(...),
    extracted_data: str = Form(...)
):
    """Match extracted data to form fields"""
    try:
        # Parse form fields
        try:
            form_fields_list = json.loads(form_fields)
        except json.JSONDecodeError:
            # If not JSON, treat as line-separated list
            form_fields_list = [f.strip() for f in form_fields.split('\n') if f.strip()]
        
        if not form_fields_list:
            raise HTTPException(status_code=400, detail="Form fields cannot be empty")
        
        # Parse extracted data
        try:
            extracted = json.loads(extracted_data)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid JSON in extracted_data: {str(e)}. Please provide valid JSON format."
            )
        
        if not isinstance(extracted, dict):
            raise HTTPException(
                status_code=400,
                detail="extracted_data must be a JSON object/dictionary"
            )
        
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

# Initialize JobFormManager
from job_form_manager import JobFormManager
job_manager = JobFormManager()

@app.post("/api/job-form/analyze")
async def analyze_job_form(form_url: str = Form(...)):
    """Analyze a Google Form and return its questions"""
    try:
        result = job_manager.analyze_form(form_url)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/job-form/fill")
async def fill_job_form(
    form_url: str = Form(...),
    extracted_data: str = Form(...),
    use_ai: bool = Form(False)
):
    """Fill a job application form with OCR extracted data or AI-powered filling"""
    try:
        extracted = json.loads(extracted_data)
        result = await job_manager.fill_form(form_url, extracted, use_ai)
        return JSONResponse(content=result)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/job-form/submit")
async def submit_job_form(
    form_url: str = Form(...),
    form_data: str = Form(...)
):
    """Submit a filled job application form"""
    try:
        filled_data = json.loads(form_data)
        
        # Ensure form_data is a flat dictionary with entry IDs as keys
        if not isinstance(filled_data, dict):
            raise HTTPException(status_code=400, detail="Form data must be a dictionary")
        
        result = job_manager.submit_form(form_url, filled_data)
        return JSONResponse(content=result)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resume/process")
async def process_resume(file: UploadFile = File(...)):
    """Process a resume PDF and create searchable index"""
    try:
        content = await file.read()
        result = await job_manager.process_resume(content)
        
        if result.get("success"):
            return JSONResponse(content=result)
        else:
            # Check if it's a 503 service unavailable (missing dependencies)
            if "install" in result.get("error", "").lower():
                return JSONResponse(status_code=503, content=result)
            else:
                raise HTTPException(status_code=400, detail=result.get("error", "Failed to process resume"))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/job-form/fill-ai")
async def fill_job_form_ai(
    form_url: str = Form(...),
    resume_index_path: str = Form(...),
    model: str = Form(None)
):
    """Fill job form using AI-powered RAG workflow with resume"""
    try:
        result = await job_manager.fill_form_ai_full(form_url, resume_index_path, model)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/job-form/get-filled")
async def get_filled_form(form_url: str):
    """Get filled form data (for testing/debugging)"""
    try:
        result = job_manager.get_filled_form_structure(form_url)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== MOSIP Integration Endpoints ==========

@app.post("/api/mosip/send")
async def send_to_mosip(data: Dict[str, Any]):
    """Convert OCR extracted data to MOSIP format and create a packet."""
    if not MOSIP_AVAILABLE:
        raise HTTPException(status_code=503, detail="MOSIP integration not available. Missing packet_handler or mosip_field_mapper modules.")
    
    try:
        extracted_fields = data.get("extracted_fields", {})
        extracted_metadata = data.get("extracted_metadata", {}) # New: Confidence scores
        
        if not extracted_fields:
            raise HTTPException(status_code=400, detail="No extracted_fields provided")
        
        # Map OCR data to MOSIP schema
        mosip_data = mosip_mapper.map_to_mosip_schema(extracted_fields)
        
        # Map metadata (confidence scores) to MOSIP schema
       # Build comprehensive field confidence map
        field_confidence = {}
        if extracted_metadata:
            # Extract TrOCR confidence scores
            trocr_conf = extracted_metadata.get('trocr_confidence', {})
            field_metadata = extracted_metadata.get('field_metadata', {})
            
            # Combine TrOCR and regular confidence scores
            for field_name in extracted_fields.keys():
                field_confidence[field_name] = {}
                
                # Add TrOCR confidence if available
                if field_name in trocr_conf:
                    field_confidence[field_name]['trocr_confidence'] = trocr_conf[field_name]
                

                
                # Add any other metadata
                if field_name in field_metadata:
                    for key, value in field_metadata[field_name].items():
                        if key != 'confidence':
                            field_confidence[field_name][key] = value
            
            # Also try mapping through mosip_mapper if it exists
            try:
                mapped_metadata = mosip_mapper.map_metadata(extracted_metadata)
                for field, meta in mapped_metadata.items():
                    if field not in field_confidence:
                        field_confidence[field] = {}
                    field_confidence[field].update(meta)
            except Exception as e:
                print(f"Warning: Could not map metadata: {e}")
        
        if not mosip_data:
            raise HTTPException(status_code=400, detail="No valid fields to map to MOSIP schema")
        
        # Generate packet ID
        packet_id = str(uuid.uuid4())[:8]
        
        # Create packet directory structure
        packet_dir = os.path.join(PACKETS_DIR, packet_id)
        os.makedirs(packet_dir, exist_ok=True)
        
        # Create ID.json with demographic data
        id_json_path = os.path.join(packet_dir, "ID.json")
        with open(id_json_path, "w") as f:
            json.dump({"identity": mosip_data}, f, indent=2)
        
        # Prepare OCR result for packet handler
        ocr_result = {
            "mosip_data": mosip_data,
            "quality_scores": data.get("quality_scores", {}),
            "field_confidence": field_confidence, # New: Field-level confidence
            "raw_ocr_data": {"full_text": data.get("raw_text", "")}
        }
        
        # Add OCR artifacts to packet
        packet_handler.add_ocr_to_packet(packet_id, ocr_result)
        
        return {
            "success": True,
            "packet_id": packet_id,
            "mosip_data": mosip_data,
            "message": f"MOSIP packet {packet_id} created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating MOSIP packet: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create MOSIP packet: {str(e)}")

@app.get("/api/mosip/packets")
async def list_mosip_packets():
    """List all MOSIP packets in the mock_packets directory."""
    if not MOSIP_AVAILABLE:
        raise HTTPException(status_code=503, detail="MOSIP integration not available")
    
    try:
        if not os.path.exists(PACKETS_DIR):
            return {"packets": []}
        
        packets = []
        for packet_id in os.listdir(PACKETS_DIR):
            packet_path = os.path.join(PACKETS_DIR, packet_id)
            if not os.path.isdir(packet_path):
                continue
            
            # Try to read ID.json to get basic info
            id_json_path = os.path.join(packet_path, "ID.json")
            packet_info = {
                "id": packet_id,
                "created": os.path.getctime(packet_path)
            }
            
            if os.path.exists(id_json_path):
                try:
                    with open(id_json_path, "r") as f:
                        data = json.load(f)
                        identity = data.get("identity", {})
                        packet_info["fields"] = list(identity.keys())
                        packet_info["field_count"] = len(identity)
                except:
                    pass
            
            packets.append(packet_info)
        
        # Sort by creation time (newest first)
        packets.sort(key=lambda x: x.get("created", 0), reverse=True)
        
        return {"packets": packets}
    except Exception as e:
        print(f"Error listing MOSIP packets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list packets: {str(e)}")

@app.get("/api/mosip/packet/{packet_id}")
async def get_mosip_packet(packet_id: str):
    """Get details of a specific MOSIP packet."""
    if not MOSIP_AVAILABLE:
        raise HTTPException(status_code=503, detail="MOSIP integration not available")
    
    try:
        packet_path = os.path.join(PACKETS_DIR, packet_id)
        if not os.path.exists(packet_path) or not os.path.isdir(packet_path):
            raise HTTPException(status_code=404, detail="Packet not found")
        
        # Read all JSON files in the packet
        packet_data = {}
        
        for filename in os.listdir(packet_path):
            if filename.endswith(".json"):
                file_path = os.path.join(packet_path, filename)
                try:
                    with open(file_path, "r") as f:
                        packet_data[filename] = json.load(f)
                except:
                    pass
        
        return {
            "packet_id": packet_id,
            "data": packet_data
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting MOSIP packet: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get packet: {str(e)}")

@app.post("/api/mosip/upload/{packet_id}")
async def upload_packet_to_mosip(packet_id: str):
    """
    Upload a locally created packet to MOSIP Pre-Registration server.
    Uses the official MOSIP API format found in DemographicController.java
    """
    if not MOSIP_AVAILABLE:
        # Even in mock mode, we can simulate upload
        from mosip_client import MosipClient
        client = MosipClient(mock_mode=True)
    else:
        from mosip_client import MosipClient
        client = MosipClient(mock_mode=False)
    
    try:
        # Load packet data
        packet_path = os.path.join(PACKETS_DIR, packet_id)
        if not os.path.exists(packet_path):
            raise HTTPException(status_code=404, detail="Packet not found")
        
        # Read ID.json (demographic data)
        id_json_path = os.path.join(packet_path, "ID.json")
        if not os.path.exists(id_json_path):
            raise HTTPException(status_code=400, detail="Packet missing ID.json")
        
        with open(id_json_path, "r") as f:
            id_data = json.load(f)
        
        demographic_data = id_data.get("identity", {})
        
        # Authenticate with MOSIP
        if not client.authenticate():
            raise HTTPException(status_code=503, detail="MOSIP authentication failed")
        
        # Upload to MOSIP using official API format
        result = client.create_application(demographic_data)
        
        if result.get("errors"):
            raise HTTPException(
                status_code=500, 
                detail=f"MOSIP API error: {result['errors']}"
            )
        
        # Extract PRID (Pre-Registration ID) from response
        prid = result.get("response", {}).get("preRegistrationId")
        
        if not prid:
            raise HTTPException(status_code=500, detail="No PRID returned from MOSIP")
        
        # Save PRID and upload status to metadata
        metadata_path = os.path.join(packet_path, "metadata.json")
        metadata = {
            "packet_id": packet_id,
            "mosip_prid": prid,
            "upload_timestamp": datetime.now().isoformat(),
            "upload_status": "success",
            "mosip_response": result
        }
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "success": True,
            "packet_id": packet_id,
            "mosip_prid": prid,
            "message": f"Packet uploaded successfully to MOSIP. PRID: {prid}",
            "response": result.get("response", {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading to MOSIP: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ocr_loaded": ocr_reader is not None
    }

# =============================================================================
# MOCK MOSIP PRE-REGISTRATION BACKEND ENDPOINTS
# These endpoints allow the Angular Pre-Registration UI to work locally
# =============================================================================

@app.get("/preregistration/v1/login/config")
async def mosip_login_config():
    """Mock MOSIP login configuration"""
    return {
        "response": {
            "mosip.kernel.otp.expiry-time": "180",
            "mosip.kernel.otp.length": "6",
            "mosip.kernel.otp.default-length": "6",
            "mosip.kernel.otp.validation-attempt-threshold": "10",
            "mosip.supported-languages": "eng,ara,fra",
            "mosip.mandatory-languages": "eng",
            "mosip.optional-languages": "ara,fra",
            "mosip.primary-language": "eng",
            "mosip.secondary-language": "ara",
            "mosip.left_to_right_orientation": "eng,fra",
            "mosip.id.validation.identity.dateOfBirth": "[0-9]{4}/[0-9]{2}/[0-9]{2}",
            "mosip.login.mode": "email,mobile",
            "mosip.preregistration.login.email.regex": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            "mosip.preregistration.login.mobile.regex": "^[0-9]{10,15}$",
            "mosip.preregistration.captcha.enable": "false",
            "mosip.country.code": "MOR",
            "preregistration.auto.logout.idle": "180",
            "preregistration.auto.logout.timeout": "60",
            "preregistration.auto.logout.ping": "30",
            "preregistration.recommended.centers.locCode": "5",
            "preregistration.availability.sync": "10",
            "preregistration.availability.noOfDays": "30",
            "preregistration.nearby.centers": "10",
            "preregistration.identity.name": "fullName",
            "preregistration.workflow.demographic": "true",
            "preregistration.workflow.documentupload": "true",
            "preregistration.workflow.booking": "true",
            "preregistration.preview.fields": "fullName,fatherName,motherName,dateOfBirth,gender,residenceStatus,addressLine1,region,province,city,postalCode,phone,email,referenceIdentityNumber",
            "preregistration.documentupload.allowed.file.type": "application/pdf,image/jpeg,image/png,image/jpg",
            "preregistration.documentupload.allowed.file.size": "2000000",
            "preregistration.documentupload.allowed.file.name.length": "50",
            "mosip.notificationtype": "EMAIL|SMS"
        },
        "errors": None
    }

@app.post("/preregistration/v1/login/sendOtp")
async def mosip_send_otp(request: dict = None):
    """Mock send OTP for login"""
    from datetime import datetime
    return {
        "response": {
            "message": "OTP sent successfully",
            "status": "true"
        },
        "responsetime": datetime.utcnow().isoformat() + "Z",
        "errors": None
    }

@app.post("/preregistration/v1/login/sendOtp/langcode/{lang_code}")
async def mosip_send_otp_lang(lang_code: str, request: dict = None):
    """Mock send OTP with language"""
    from datetime import datetime
    return {
        "response": {
            "message": "OTP sent successfully",
            "status": "true"
        },
        "responsetime": datetime.utcnow().isoformat() + "Z",
        "errors": None
    }

@app.post("/preregistration/v1/login/sendOtpWithCaptcha")
async def mosip_send_otp_captcha(request: dict = None):
    """Mock send OTP with captcha for login"""
    from datetime import datetime
    return {
        "response": {
            "message": "OTP sent successfully",
            "status": "true"
        },
        "responsetime": datetime.utcnow().isoformat() + "Z",
        "errors": None
    }

@app.post("/preregistration/v1/login/validateOtp")
async def mosip_validate_otp(request: dict = None):
    """Mock validate OTP - auto-approve for testing"""
    return {
        "response": {
            "message": "OTP validated successfully",
            "userId": "test@example.com",
            "status": "true"
        },
        "errors": None
    }

@app.post("/preregistration/v1/login/invalidateToken")
async def mosip_invalidate_token(request: dict = None):
    """Mock invalidate token for logout"""
    from datetime import datetime
    return {
        "response": {
            "message": "Token invalidated successfully",
            "status": "true"
        },
        "responsetime": datetime.utcnow().isoformat() + "Z",
        "errors": None
    }

@app.get("/preregistration/v1/applications/config")
async def mosip_app_config():
    """Mock application configuration"""
    return {
        "response": {
            "mosip.left-to-right-orientation": "eng,fra",
            "mosip.supported-languages": "eng,ara,fra",
            "mosip.primary-language": "eng",
            "preregistration.document.extention": "pdf,jpg,jpeg,png"
        },
        "errors": None
    }

@app.get("/preregistration/v1/sync/masterdata")
async def mosip_masterdata():
    """Mock master data sync"""
    return {
        "response": {
            "languages": [
                {"code": "eng", "name": "English"},
                {"code": "ara", "name": "Arabic"},
                {"code": "fra", "name": "French"}
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/templates/{lang_code}/TOSP")
async def mosip_templates(lang_code: str):
    """Mock templates"""
    return {
        "response": {"templates": []},
        "errors": None
    }

@app.get("/preregistration/v1/applications")
async def mosip_get_applications():
    """Mock get applications list"""
    return {
        "response": {
            "basicDetails": [],
            "totalRecords": 0
        },
        "errors": None
    }

@app.get("/preregistration/v1/uispec/latest")
async def mosip_uispec():
    """Mock UI specification with proper labelName structure"""
    # Each field needs labelName with language keys
    def make_field(field_id, label_eng, label_ara, control_type, field_type="simpleType", required=True, is_dynamic=False, alignment_group=1, location_hierarchy_level=None):
        field = {
            "id": field_id,
            "inputRequired": True,
            "controlType": control_type,
            "type": field_type,
            "required": required,
            "validators": [],
            "labelName": {"eng": label_eng, "ara": label_ara, "fra": label_eng},
            "fieldType": "dynamic" if is_dynamic else "default",
            "alignmentGroup": alignment_group,
            "isVisible": True
        }
        if location_hierarchy_level is not None:
            field["locationHierarchyLevel"] = location_hierarchy_level
        return field
    
    return {
        "response": {
            "jsonSpec": {
                "identity": {
                    "identity": [
                        make_field("fullName", "Full Name", "الاسم الكامل", "textbox", alignment_group=1),
                        make_field("dateOfBirth", "Date of Birth", "تاريخ الولادة", "ageDate", "string", alignment_group=1),
                        make_field("gender", "Gender", "جنس", "dropdown", is_dynamic=True, alignment_group=1),
                        make_field("fatherName", "Father's Name", "اسم الأب", "textbox", required=False, alignment_group=2),
                        make_field("motherName", "Mother's Name", "اسم الأم", "textbox", required=False, alignment_group=2),
                        make_field("residenceStatus", "Residence Status", "حالة الإقامة", "dropdown", is_dynamic=True, alignment_group=2),
                        make_field("addressLine1", "Address Line 1", "العنوان", "textbox", required=False, alignment_group=3),
                        make_field("region", "Region", "منطقة", "dropdown", alignment_group=4, location_hierarchy_level=1),
                        make_field("province", "Province", "مقاطعة", "dropdown", alignment_group=4, location_hierarchy_level=2),
                        make_field("city", "City", "مدينة", "dropdown", alignment_group=4, location_hierarchy_level=5),
                        make_field("postalCode", "Postal Code", "الرمز البريدي", "textbox", "string", required=False, alignment_group=4),
                        make_field("phone", "Phone", "هاتف", "textbox", "string", required=False, alignment_group=5),
                        make_field("email", "Email", "بريد إلكتروني", "textbox", "string", required=False, alignment_group=5),
                        make_field("referenceIdentityNumber", "Reference ID Number", "رقم الهوية المرجعية", "textbox", "string", required=False, alignment_group=5),
                    ],
                    "locationHierarchy": ["region", "province", "city"]
                }
            },
            "idSchemaVersion": "0.1"
        },
        "errors": None
    }

@app.get("/preregistration/v1/applications/prereg")
async def mosip_prereg_applications():
    """Mock pre-registration applications list - returns stored applications"""
    import uuid
    from datetime import datetime
    
    # If no applications exist, create a default one
    if not mosip_applications:
        default_prid = str(uuid.uuid4())[:14].replace("-", "").upper()
        mosip_applications[default_prid] = {
            "preRegistrationId": default_prid,
            "statusCode": "Pending_Appointment",
            "createdDateTime": datetime.now().isoformat() + "Z",
            "demographicDetails": {
                "identity": {
                    "fullName": [{"language": "eng", "value": "Test User"}],
                    "dateOfBirth": "1990/01/01",
                    "gender": [{"language": "eng", "value": "Male"}],
                    "phone": "0612345678",
                    "email": "test@example.com",
                    "postalCode": "10000"
                }
            }
        }
    
    # Build the response from stored applications
    basic_details = []
    for prid, app_data in mosip_applications.items():
        demo_details = app_data.get("demographicDetails", {})
        identity = demo_details.get("identity", demo_details)
        
        basic_details.append({
            "preRegistrationId": prid,
            "statusCode": app_data.get("statusCode", "Pending_Appointment"),
            "createdDateTime": app_data.get("createdDateTime", "2024-01-01T00:00:00.000Z"),
            "modify_at_DemoPreview": True,
            "langCode": "eng",
            "dataCaptureLanguage": ["eng"],
            "demographicMetadata": {
                "fullName": identity.get("fullName", [{"language": "eng", "value": "User"}]),
                "dateOfBirth": identity.get("dateOfBirth", "1990/01/01"),
                "gender": identity.get("gender", [{"language": "eng", "value": "Male"}]),
                "phone": identity.get("phone", ""),
                "email": identity.get("email", ""),
                "postalCode": identity.get("postalCode", "")
            }
        })
    
    return {
        "response": {
            "basicDetails": basic_details,
            "totalRecords": len(basic_details)
        },
        "errors": None
    }

@app.post("/preregistration/v1/applications")
async def mosip_create_application(request: dict = None):
    """Mock create new application"""
    import uuid
    prid = str(uuid.uuid4())[:14].replace("-", "").upper()
    return {
        "response": {
            "preRegistrationId": prid,
            "createdDateTime": "2024-01-01T00:00:00.000Z",
            "statusCode": "Pending_Appointment"
        },
        "errors": None
    }

@app.delete("/preregistration/v1/applications/prereg/{prid}")
async def mosip_delete_application(prid: str):
    """Mock delete pre-registration application - actually removes from storage"""
    from datetime import datetime
    
    # Actually remove the application from our mock storage
    if prid in mosip_applications:
        del mosip_applications[prid]
        print(f"🗑️ Deleted application {prid}")
    else:
        print(f"⚠️ Application {prid} not found in storage, but returning success anyway")
    
    return {
        "response": {
            "preRegistrationId": prid,
            "deletedDateTime": datetime.now().isoformat() + "Z",
            "message": "Application deleted successfully"
        },
        "errors": None
    }

@app.put("/preregistration/v1/applications/prereg/{prid}")
async def mosip_update_application(prid: str, request: Request):
    """Mock update pre-registration application - stores the data"""
    try:
        body = await request.json()
        print(f"\n📥 Received PUT request for {prid}")
        print(f"📥 Full body: {body}")
        
        # Store the submitted data
        demo_details = body.get("request", {}).get("demographicDetails", body)
        print(f"📥 demographicDetails: {demo_details}")
        
        mosip_applications[prid] = {
            "preRegistrationId": prid,
            "demographicDetails": demo_details,
            "statusCode": "Pending_Appointment",
            "updatedDateTime": "2024-01-01T00:00:00.000Z"
        }
        print(f"✅ Stored application {prid}: {mosip_applications[prid]}")
    except Exception as e:
        print(f"Error storing application: {e}")
    
    return {
        "response": {
            "preRegistrationId": prid,
            "updatedDateTime": "2024-01-01T00:00:00.000Z",
            "statusCode": "Pending_Appointment",
            "message": "Application updated successfully"
        },
        "errors": None
    }

@app.post("/preregistration/v1/applications/prereg")
async def mosip_submit_prereg(request: dict = None):
    """Mock submit pre-registration"""
    import uuid  
    prid = str(uuid.uuid4())[:14].replace("-", "").upper()
    return {
        "response": {
            "preRegistrationId": prid,
            "createdDateTime": "2024-01-01T00:00:00.000Z",
            "statusCode": "Pending_Appointment"
        },
        "errors": None
    }

@app.get("/preregistration/v1/applications/prereg/status/{prid}")
async def mosip_get_app_status(prid: str):
    """Mock get application status"""
    return {
        "response": {
            "preRegistrationId": prid,
            "statusCode": "Pending_Appointment"
        },
        "errors": None
    }

@app.put("/preregistration/v1/applications/prereg/status/{prid}")
async def mosip_update_app_status(prid: str, request: dict = None):
    """Mock update application status"""
    return {
        "response": {
            "preRegistrationId": prid,
            "statusCode": "Pending_Appointment"
        },
        "errors": None
    }

@app.get("/preregistration/v1/applications/prereg/{prid}")
async def mosip_get_application(prid: str):
    """Mock get application by PRID - returns stored data if available"""
    # Check if we have stored data for this PRID
    if prid in mosip_applications:
        stored = mosip_applications[prid]
        print(f"📖 Returning stored application {prid}")
        print(f"📖 Stored data: {stored}")
        
        # Ensure the demographicDetails has proper structure
        demo_details = stored.get("demographicDetails", {})
        identity = demo_details.get("identity", demo_details)
        
        # Build proper identity structure with arrays for all multilingual fields
        proper_identity = {
            "fullName": identity.get("fullName") if isinstance(identity.get("fullName"), list) else [{"language": "eng", "value": str(identity.get("fullName", identity.get("fullName_eng", "User")))}],
            "fatherName": identity.get("fatherName") if isinstance(identity.get("fatherName"), list) else [{"language": "eng", "value": str(identity.get("fatherName", identity.get("fatherName_eng", "")))}] if identity.get("fatherName") or identity.get("fatherName_eng") else [{"language": "eng", "value": ""}],
            "motherName": identity.get("motherName") if isinstance(identity.get("motherName"), list) else [{"language": "eng", "value": str(identity.get("motherName", identity.get("motherName_eng", "")))}] if identity.get("motherName") or identity.get("motherName_eng") else [{"language": "eng", "value": ""}],
            "dateOfBirth": identity.get("dateOfBirth", "1990/01/01"),
            "gender": identity.get("gender") if isinstance(identity.get("gender"), list) else [{"language": "eng", "value": "Male"}],
            "residenceStatus": identity.get("residenceStatus") if isinstance(identity.get("residenceStatus"), list) else [{"language": "eng", "value": "Non-Foreigner"}],
            "addressLine1": identity.get("addressLine1") if isinstance(identity.get("addressLine1"), list) else [{"language": "eng", "value": str(identity.get("addressLine1", identity.get("addressLine1_eng", "")))}] if identity.get("addressLine1") or identity.get("addressLine1_eng") else [{"language": "eng", "value": ""}],
            "region": identity.get("region") if isinstance(identity.get("region"), list) else [{"language": "eng", "value": "Rabat-Salé-Kénitra"}],
            "province": identity.get("province") if isinstance(identity.get("province"), list) else [{"language": "eng", "value": "Rabat"}],
            "city": identity.get("city") if isinstance(identity.get("city"), list) else [{"language": "eng", "value": "Rabat City"}],
            "postalCode": identity.get("postalCode", "10000"),
            "phone": identity.get("phone", "0612345678"),
            "email": identity.get("email", "test@example.com"),
            "referenceIdentityNumber": identity.get("referenceIdentityNumber", "")
        }
        
        print(f"📖 Proper identity: {proper_identity}")
        
        return {
            "response": {
                "preRegistrationId": prid,
                "createdDateTime": "2024-01-01T00:00:00.000Z",
                "statusCode": stored.get("statusCode", "Pending_Appointment"),
                "modify_at_DemoPreview": True,
                "langCode": "eng",
                "demographicDetails": {"identity": proper_identity},
                "documents": []
            },
            "errors": None
        }
    
    # Default response for new applications
    return {
        "response": {
            "preRegistrationId": prid,
            "createdDateTime": "2024-01-01T00:00:00.000Z",
            "statusCode": "Pending_Appointment",
            "modify_at_DemoPreview": True,
            "langCode": "eng",
            "demographicDetails": {
                "identity": {
                    "fullName": [{"language": "eng", "value": "Test User"}],
                    "fatherName": [{"language": "eng", "value": ""}],
                    "motherName": [{"language": "eng", "value": ""}],
                    "dateOfBirth": "1990/01/01",
                    "gender": [{"language": "eng", "value": "Male"}],
                    "residenceStatus": [{"language": "eng", "value": "Non-Foreigner"}],
                    "addressLine1": [{"language": "eng", "value": ""}],
                    "region": [{"language": "eng", "value": "Rabat-Salé-Kénitra"}],
                    "province": [{"language": "eng", "value": "Rabat"}],
                    "city": [{"language": "eng", "value": "Rabat City"}],
                    "postalCode": "10000",
                    "phone": "0612345678",
                    "email": "test@example.com",
                    "referenceIdentityNumber": ""
                }
            },
            "documents": []
        },
        "errors": None
    }

@app.get("/preregistration/v1/documents/preregistration/{prid}")
async def mosip_get_documents(prid: str):
    """Mock get documents for application"""
    return {
        "response": {
            "documentsMetaData": []
        },
        "errors": None
    }

@app.post("/preregistration/v1/proxy/masterdata/getApplicantType")
async def mosip_get_applicant_type(request: dict = None):
    """Mock get applicant type"""
    return {
        "response": {
            "applicantType": {
                "applicantTypeCode": "001"
            }
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/applicanttype/{app_type}/languages")
async def mosip_applicant_type_docs(app_type: str, languages: str = None):
    """Mock get document categories for applicant type"""
    return {
        "response": {
            "documentCategories": [
                {
                    "code": "POI",
                    "description": "Proof of Identity",
                    "langCode": "eng",
                    "documentTypes": [
                        {"code": "PASSPORT", "description": "Passport", "langCode": "eng"},
                        {"code": "IDCARD", "description": "National ID Card", "langCode": "eng"}
                    ]
                },
                {
                    "code": "POA",
                    "description": "Proof of Address",
                    "langCode": "eng",
                    "documentTypes": [
                        {"code": "UTILITY", "description": "Utility Bill", "langCode": "eng"},
                        {"code": "BANK", "description": "Bank Statement", "langCode": "eng"}
                    ]
                }
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/validdocuments/{app_type}/languages")
async def mosip_valid_documents(app_type: str, langCode: str = None):
    """Mock valid documents for applicant type"""
    return {
        "response": {
            "documentCategories": [
                {
                    "code": "POI",
                    "description": "Proof of Identity",
                    "langCode": langCode or "eng",
                    "documentTypes": [
                        {"code": "PASSPORT", "description": "Passport", "langCode": langCode or "eng"},
                        {"code": "IDCARD", "description": "National ID Card", "langCode": langCode or "eng"}
                    ]
                },
                {
                    "code": "POA",
                    "description": "Proof of Address",
                    "langCode": langCode or "eng",
                    "documentTypes": [
                        {"code": "UTILITY", "description": "Utility Bill", "langCode": langCode or "eng"},
                        {"code": "BANK", "description": "Bank Statement", "langCode": langCode or "eng"}
                    ]
                }
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/dynamicfields")
async def mosip_dynamic_fields(langCode: str = None, pageNumber: str = None, pageSize: str = None):
    """Mock dynamic fields for dropdowns with proper format"""
    return {
        "response": {
            "data": [
                {
                    "name": "gender",
                    "langCode": "eng",
                    "dataType": "string",
                    "fieldVal": [
                        {"code": "MLE", "value": "Male"},
                        {"code": "FLE", "value": "Female"}
                    ]
                },
                {
                    "name": "gender",
                    "langCode": "ara",
                    "dataType": "string",
                    "fieldVal": [
                        {"code": "MLE", "value": "ذكر"},
                        {"code": "FLE", "value": "أنثى"}
                    ]
                },
                {
                    "name": "residenceStatus",
                    "langCode": "eng",
                    "dataType": "string",
                    "fieldVal": [
                        {"code": "FR", "value": "Foreigner"},
                        {"code": "NFR", "value": "Non-Foreigner"}
                    ]
                },
                {
                    "name": "residenceStatus",
                    "langCode": "ara",
                    "dataType": "string",
                    "fieldVal": [
                        {"code": "FR", "value": "أجنبي"},
                        {"code": "NFR", "value": "غير أجنبي"}
                    ]
                }
            ],
            "pageNo": 0,
            "totalPages": 1,
            "totalItems": 4
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/gendertypes")
async def mosip_gender_types():
    """Mock get gender types"""
    return {
        "response": {
            "genderType": [
                {"code": "MLE", "genderName": "Male", "langCode": "eng", "isActive": True},
                {"code": "FLE", "genderName": "Female", "langCode": "eng", "isActive": True}
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/individualtypes")
async def mosip_individual_types():
    """Mock get individual/resident types"""
    return {
        "response": {
            "individualTypes": [
                {"code": "FR", "name": "Foreigner", "langCode": "eng", "isActive": True},
                {"code": "NFR", "name": "Non-Foreigner", "langCode": "eng", "isActive": True}
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/locationHierarchyLevels/{lang_code}")
async def mosip_location_hierarchy_levels_by_lang(lang_code: str):
    """Mock get location hierarchy levels by language"""
    return {
        "response": {
            "locationHierarchyLevels": [
                {"hierarchyLevel": 0, "hierarchyLevelName": "Country", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 1, "hierarchyLevelName": "Region", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 2, "hierarchyLevelName": "Province", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 3, "hierarchyLevelName": "City", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 4, "hierarchyLevelName": "Zone", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 5, "hierarchyLevelName": "Postal Code", "langCode": lang_code, "isActive": True}
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/applications/appointment/slots/availability/{center_id}")
async def mosip_appointment_slots_availability_new(center_id: str):
    """Mock get appointment slots availability for a registration center"""
    from datetime import datetime, timedelta
    
    # Generate slots for next 14 days
    center_details = []
    today = datetime.now()
    for day in range(1, 15):
        date = today + timedelta(days=day)
        date_str = date.strftime("%Y-%m-%d")
        # Skip weekends
        if date.weekday() < 5:
            center_details.append({
                "date": date_str,
                "timeSlots": [
                    {"fromTime": "09:00:00", "toTime": "09:15:00", "availability": 5},
                    {"fromTime": "09:15:00", "toTime": "09:30:00", "availability": 5},
                    {"fromTime": "09:30:00", "toTime": "09:45:00", "availability": 3},
                    {"fromTime": "09:45:00", "toTime": "10:00:00", "availability": 4},
                    {"fromTime": "10:00:00", "toTime": "10:15:00", "availability": 5},
                    {"fromTime": "10:15:00", "toTime": "10:30:00", "availability": 5},
                    {"fromTime": "10:30:00", "toTime": "10:45:00", "availability": 4},
                    {"fromTime": "10:45:00", "toTime": "11:00:00", "availability": 5},
                    {"fromTime": "14:00:00", "toTime": "14:15:00", "availability": 5},
                    {"fromTime": "14:15:00", "toTime": "14:30:00", "availability": 4},
                    {"fromTime": "14:30:00", "toTime": "14:45:00", "availability": 5},
                    {"fromTime": "14:45:00", "toTime": "15:00:00", "availability": 3},
                    {"fromTime": "15:00:00", "toTime": "15:15:00", "availability": 5},
                    {"fromTime": "15:15:00", "toTime": "15:30:00", "availability": 4}
                ]
            })
    
    return {
        "response": {
            "regCenterId": center_id,
            "centerDetails": center_details
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/getcoordinatespecificregistrationcenters/{lang_code}/{longitude}/{latitude}/{distance}")
async def mosip_nearby_centers_by_coords(lang_code: str, longitude: str, latitude: str, distance: str = "2000"):
    """Mock get nearby registration centers by coordinates"""
    return {
        "response": {
            "registrationCenters": [
                {
                    "id": "10001",
                    "name": "MOSIP Registration Center - Nearby 1",
                    "centerTypeCode": "REG",
                    "addressLine1": "123 Main Street",
                    "addressLine2": "Downtown Area",
                    "latitude": latitude,
                    "longitude": longitude,
                    "locationCode": "RABAT_CITY",
                    "langCode": lang_code,
                    "numberOfKiosks": 5,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "lunchStartTime": "13:00:00",
                    "lunchEndTime": "14:00:00",
                    "isActive": True,
                    "contactPhone": "+212-537-123456",
                    "workingHours": "9:00 AM - 5:00 PM"
                },
                {
                    "id": "10002",
                    "name": "MOSIP Registration Center - Nearby 2",
                    "centerTypeCode": "REG",
                    "addressLine1": "456 Center Avenue",
                    "addressLine2": "City Center",
                    "latitude": str(float(latitude) + 0.01),
                    "longitude": str(float(longitude) + 0.01),
                    "locationCode": "RABAT_CITY",
                    "langCode": lang_code,
                    "numberOfKiosks": 8,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "08:00:00",
                    "centerEndTime": "16:00:00",
                    "lunchStartTime": "12:00:00",
                    "lunchEndTime": "13:00:00",
                    "isActive": True,
                    "contactPhone": "+212-537-654321",
                    "workingHours": "8:00 AM - 4:00 PM"
                }
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/locations/immediatechildren/{loc_code}/{lang_code}")
async def mosip_location_immediate_children(loc_code: str, lang_code: str):
    """Mock location hierarchy - returns immediate children of a location"""
    # Location hierarchy: MOR (country) -> regions -> provinces -> cities
    location_data = {
        "MOR": [  # Morocco regions
            {"code": "RSK", "name": "Rabat-Salé-Kénitra", "hierarchyLevel": 1, "hierarchyName": "Region", "parentLocCode": "MOR", "isActive": True, "langCode": lang_code},
            {"code": "CMK", "name": "Casablanca-Settat", "hierarchyLevel": 1, "hierarchyName": "Region", "parentLocCode": "MOR", "isActive": True, "langCode": lang_code},
            {"code": "FMK", "name": "Fès-Meknès", "hierarchyLevel": 1, "hierarchyName": "Region", "parentLocCode": "MOR", "isActive": True, "langCode": lang_code}
        ],
        "RSK": [  # Rabat-Salé-Kénitra provinces
            {"code": "RAB", "name": "Rabat", "hierarchyLevel": 2, "hierarchyName": "Province", "parentLocCode": "RSK", "isActive": True, "langCode": lang_code},
            {"code": "SAL", "name": "Salé", "hierarchyLevel": 2, "hierarchyName": "Province", "parentLocCode": "RSK", "isActive": True, "langCode": lang_code},
            {"code": "KEN", "name": "Kénitra", "hierarchyLevel": 2, "hierarchyName": "Province", "parentLocCode": "RSK", "isActive": True, "langCode": lang_code}
        ],
        "RAB": [  # Rabat cities
            {"code": "RABAT_CITY", "name": "Rabat City", "hierarchyLevel": 3, "hierarchyName": "City", "parentLocCode": "RAB", "isActive": True, "langCode": lang_code},
            {"code": "TEMARA", "name": "Témara", "hierarchyLevel": 3, "hierarchyName": "City", "parentLocCode": "RAB", "isActive": True, "langCode": lang_code}
        ],
        "CMK": [  # Casablanca provinces
            {"code": "CAS", "name": "Casablanca", "hierarchyLevel": 2, "hierarchyName": "Province", "parentLocCode": "CMK", "isActive": True, "langCode": lang_code},
            {"code": "SET", "name": "Settat", "hierarchyLevel": 2, "hierarchyName": "Province", "parentLocCode": "CMK", "isActive": True, "langCode": lang_code}
        ],
        "CAS": [  # Casablanca cities
            {"code": "CASA_CITY", "name": "Casablanca City", "hierarchyLevel": 3, "hierarchyName": "City", "parentLocCode": "CAS", "isActive": True, "langCode": lang_code},
            {"code": "MOHAMMEDIA", "name": "Mohammedia", "hierarchyLevel": 3, "hierarchyName": "City", "parentLocCode": "CAS", "isActive": True, "langCode": lang_code}
        ],
        "RABAT_CITY": [  # Postal codes for Rabat City
            {"code": "10000", "name": "10000", "hierarchyLevel": 4, "hierarchyName": "Postal Code", "parentLocCode": "RABAT_CITY", "isActive": True, "langCode": lang_code},
            {"code": "10001", "name": "10001", "hierarchyLevel": 4, "hierarchyName": "Postal Code", "parentLocCode": "RABAT_CITY", "isActive": True, "langCode": lang_code},
            {"code": "10002", "name": "10002", "hierarchyLevel": 4, "hierarchyName": "Postal Code", "parentLocCode": "RABAT_CITY", "isActive": True, "langCode": lang_code}
        ]
    }
    
    locations = location_data.get(loc_code, [])
    return {
        "response": {
            "locations": locations
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/locations/info/{loc_code}/{lang_code}")
async def mosip_location_info_by_code(loc_code: str, lang_code: str):
    """Mock get location info by code"""
    # Simple location name lookup
    location_names = {
        "MOR": "Morocco",
        "RSK": "Rabat-Salé-Kénitra",
        "CMK": "Casablanca-Settat",
        "FMK": "Fès-Meknès",
        "RAB": "Rabat",
        "SAL": "Salé",
        "KEN": "Kénitra",
        "CAS": "Casablanca",
        "SET": "Settat",
        "RABAT_CITY": "Rabat City",
        "TEMARA": "Témara",
        "CASA_CITY": "Casablanca City",
        "MOHAMMEDIA": "Mohammedia",
        "10000": "10000",
        "10001": "10001",
        "10002": "10002"
    }
    
    name = location_names.get(loc_code, loc_code)
    return {
        "response": {
            "code": loc_code,
            "name": name,
            "langCode": lang_code,
            "isActive": True
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/locations/{loc_code}/{lang_code}")
async def mosip_location_children(loc_code: str, lang_code: str):
    """Mock location hierarchy - returns children based on parent location"""
    # Location hierarchy: MOR (country) -> regions -> provinces -> cities
    location_data = {
        "MOR": [  # Morocco regions
            {"code": "RSK", "name": "Rabat-Salé-Kénitra", "hierarchyLevel": 1, "isActive": True, "langCode": lang_code},
            {"code": "CMK", "name": "Casablanca-Settat", "hierarchyLevel": 1, "isActive": True, "langCode": lang_code},
            {"code": "TTA", "name": "Tanger-Tetouan-Al Hoceima", "hierarchyLevel": 1, "isActive": True, "langCode": lang_code}
        ],
        "RSK": [  # Rabat-Salé-Kénitra provinces
            {"code": "RBT", "name": "Rabat", "hierarchyLevel": 2, "isActive": True, "langCode": lang_code},
            {"code": "SLE", "name": "Salé", "hierarchyLevel": 2, "isActive": True, "langCode": lang_code},
            {"code": "KNT", "name": "Kénitra", "hierarchyLevel": 2, "isActive": True, "langCode": lang_code}
        ],
        "CMK": [  # Casablanca provinces
            {"code": "CSB", "name": "Casablanca", "hierarchyLevel": 2, "isActive": True, "langCode": lang_code},
            {"code": "MDQ", "name": "Mohammedia", "hierarchyLevel": 2, "isActive": True, "langCode": lang_code}
        ],
        "RBT": [  # Rabat cities
            {"code": "RBT1", "name": "Rabat City", "hierarchyLevel": 3, "isActive": True, "langCode": lang_code},
            {"code": "AGD", "name": "Agdal", "hierarchyLevel": 3, "isActive": True, "langCode": lang_code}
        ],
        "SLE": [  # Salé cities
            {"code": "SLE1", "name": "Salé City", "hierarchyLevel": 3, "isActive": True, "langCode": lang_code}
        ],
        "CSB": [  # Casablanca cities
            {"code": "CSB1", "name": "Casablanca Center", "hierarchyLevel": 3, "isActive": True, "langCode": lang_code},
            {"code": "ANF", "name": "Anfa", "hierarchyLevel": 3, "isActive": True, "langCode": lang_code}
        ]
    }
    
    # Return locations for this parent, or default if not found
    locations = location_data.get(loc_code, location_data.get("MOR", []))
    
    return {
        "response": {
            "locations": locations
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/templates/templatetypecodes/{type_code}")
async def mosip_templates_by_type(type_code: str):
    """Mock templates by type code"""
    return {
        "response": {
            "templates": [
                {"langCode": "eng", "fileText": "I agree to the terms and conditions for pre-registration."},
                {"langCode": "ara", "fileText": "أوافق على الشروط والأحكام للتسجيل المسبق."},
                {"langCode": "fra", "fileText": "J'accepte les termes et conditions pour la pré-inscription."}
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/documenttypes/{category}/{lang_code}")
async def mosip_document_types(category: str, lang_code: str):
    """Mock document types"""
    return {
        "response": {
            "documenttypes": [
                {"code": "POI", "name": "Proof of Identity", "description": "Proof of Identity", "isActive": True},
                {"code": "POA", "name": "Proof of Address", "description": "Proof of Address", "isActive": True}
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/documentcategories/{lang_code}")
async def mosip_document_categories(lang_code: str):
    """Mock document categories"""
    return {
        "response": {
            "documentcategories": [
                {"code": "POI", "name": "Proof of Identity", "description": "Proof of Identity", "isActive": True},
                {"code": "POA", "name": "Proof of Address", "description": "Proof of Address", "isActive": True}
            ]
        },
        "errors": None
    }

@app.post("/preregistration/v1/logAudit")
async def mosip_log_audit(request: dict = None):
    """Mock audit logging - just accepts and returns success"""
    return {
        "response": {"status": "success"},
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/locations/info/{loc_code}/{lang_code}")
async def mosip_location_info(loc_code: str, lang_code: str):
    """Mock get location info by code - returns name for center selection"""
    # Map location codes to names
    location_names = {
        "RABAT_CITY": "Rabat City",
        "RSK": "Rabat-Salé-Kénitra",
        "RABAT": "Rabat",
        "AGDAL": "Agdal",
        "CASABLANCA": "Casablanca",
        "CK": "Casablanca-Settat"
    }
    name = location_names.get(loc_code, loc_code.replace("_", " ").title())
    
    return {
        "response": {
            "code": loc_code,
            "name": name,
            "hierarchyLevel": 3,
            "hierarchyName": "City",
            "parentLocCode": "RSK",
            "langCode": lang_code,
            "isActive": True
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/locationHierarchyLevels/{lang_code}")
async def mosip_location_hierarchy_levels(lang_code: str):
    """Mock get location hierarchy levels"""
    return {
        "response": {
            "locationHierarchyLevels": [
                {"hierarchyLevel": 0, "hierarchyLevelName": "Country", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 1, "hierarchyLevelName": "Region", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 2, "hierarchyLevelName": "Province", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 3, "hierarchyLevelName": "City", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 4, "hierarchyLevelName": "Zone", "langCode": lang_code, "isActive": True},
                {"hierarchyLevel": 5, "hierarchyLevelName": "Postal Code", "langCode": lang_code, "isActive": True}
            ]
        },
        "errors": None
    }

# ============== BOOKING APPOINTMENT ENDPOINTS ==============

@app.get("/preregistration/v1/booking/regcenters")
async def mosip_booking_regcenters():
    """Mock get registration centers for booking"""
    return {
        "response": {
            "registrationCenters": [
                {
                    "id": "10001",
                    "name": "MOSIP Registration Center 1",
                    "centerTypeCode": "REG",
                    "addressLine1": "123 Main Street",
                    "addressLine2": "Downtown",
                    "addressLine3": "",
                    "latitude": "33.9716",
                    "longitude": "-6.8498",
                    "locationCode": "RABAT_CITY",
                    "holidayLocationCode": "RABAT",
                    "contactPhone": "+212-537-123456",
                    "workingHours": "9:00 AM - 5:00 PM",
                    "langCode": "eng",
                    "numberOfKiosks": 5,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "lunchStartTime": "13:00:00",
                    "lunchEndTime": "14:00:00",
                    "timeZone": "Africa/Casablanca",
                    "isActive": True
                },
                {
                    "id": "10002",
                    "name": "MOSIP Registration Center 2",
                    "centerTypeCode": "REG",
                    "addressLine1": "456 Avenue Hassan II",
                    "addressLine2": "City Center",
                    "addressLine3": "",
                    "latitude": "33.5731",
                    "longitude": "-7.5898",
                    "locationCode": "CASABLANCA",
                    "holidayLocationCode": "CASABLANCA",
                    "contactPhone": "+212-522-654321",
                    "workingHours": "8:00 AM - 4:00 PM",
                    "langCode": "eng",
                    "numberOfKiosks": 8,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "08:00:00",
                    "centerEndTime": "16:00:00",
                    "lunchStartTime": "12:00:00",
                    "lunchEndTime": "13:00:00",
                    "timeZone": "Africa/Casablanca",
                    "isActive": True
                }
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/booking/availability/{regcenter_id}")
async def mosip_booking_availability(regcenter_id: str):
    """Mock get available slots for a registration center"""
    from datetime import datetime, timedelta
    
    # Generate slots for next 7 days
    slots = []
    today = datetime.now()
    for day in range(1, 8):
        date = today + timedelta(days=day)
        date_str = date.strftime("%Y-%m-%d")
        # Skip weekends
        if date.weekday() < 5:
            slots.append({
                "date": date_str,
                "timeslots": [
                    {"fromTime": "09:00:00", "toTime": "09:15:00", "availability": 5},
                    {"fromTime": "09:15:00", "toTime": "09:30:00", "availability": 5},
                    {"fromTime": "09:30:00", "toTime": "09:45:00", "availability": 3},
                    {"fromTime": "09:45:00", "toTime": "10:00:00", "availability": 4},
                    {"fromTime": "10:00:00", "toTime": "10:15:00", "availability": 5},
                    {"fromTime": "10:15:00", "toTime": "10:30:00", "availability": 5},
                    {"fromTime": "14:00:00", "toTime": "14:15:00", "availability": 5},
                    {"fromTime": "14:15:00", "toTime": "14:30:00", "availability": 4},
                    {"fromTime": "14:30:00", "toTime": "14:45:00", "availability": 5},
                    {"fromTime": "15:00:00", "toTime": "15:15:00", "availability": 3}
                ]
            })
    
    return {
        "response": {
            "regCenterId": regcenter_id,
            "centerDetails": slots
        },
        "errors": None
    }

@app.post("/preregistration/v1/booking/appointment")
async def mosip_book_appointment(request: Request):
    """Mock book appointment"""
    try:
        body = await request.json()
    except:
        body = {}
    
    return {
        "response": {
            "bookingMessage": "Appointment booked successfully",
            "preRegistrationId": body.get("request", {}).get("preRegistrationId", "MOCK123"),
            "registration_center_id": body.get("request", {}).get("registration_center_id", "10001"),
            "appointment_date": body.get("request", {}).get("appointment_date", "2024-01-15"),
            "time_slot_from": body.get("request", {}).get("time_slot_from", "09:00:00"),
            "time_slot_to": body.get("request", {}).get("time_slot_to", "09:15:00")
        },
        "errors": None
    }

@app.post("/preregistration/v1/applications/appointment")
async def mosip_applications_appointment(request: Request):
    """Mock book appointment via applications path"""
    try:
        body = await request.json()
    except:
        body = {}
    
    booking_request = body.get("request", {}).get("bookingRequest", [])
    
    return {
        "response": {
            "bookingStatusResponse": [
                {
                    "bookingMessage": "Appointment booked successfully",
                    "preRegistrationId": item.get("preRegistrationId", "MOCK123"),
                    "registration_center_id": item.get("registration_center_id", "10001"),
                    "appointment_date": item.get("appointment_date", "2024-01-15"),
                    "time_slot_from": item.get("time_slot_from", "09:00:00"),
                    "time_slot_to": item.get("time_slot_to", "09:15:00")
                } for item in (booking_request if booking_request else [body.get("request", {})])
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/applications/appointment/{prid}")
async def mosip_get_applications_appointment(prid: str):
    """Mock get appointment details for acknowledgement"""
    from datetime import datetime, timedelta
    
    # Generate a future appointment date
    appointment_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    return {
        "response": {
            "preRegistrationId": prid,
            "registration_center_id": "10001",
            "appointment_date": appointment_date,
            "time_slot_from": "09:00",
            "time_slot_to": "09:15",
            "statusCode": "Booked"
        },
        "errors": None
    }

@app.put("/preregistration/v1/applications/appointment/{prid}")
async def mosip_cancel_applications_appointment(prid: str, request: Request):
    """Mock cancel appointment - this is the endpoint used by the Angular UI to cancel appointments"""
    try:
        body = await request.json()
    except:
        body = {}
    
    # Update the application status in our mock storage
    if prid in mosip_applications:
        mosip_applications[prid]["statusCode"] = "Cancelled"
    
    return {
        "response": {
            "transactionId": f"txn_{prid}",
            "preRegistrationId": prid,
            "message": "Appointment cancelled successfully",
            "deletedDateTime": datetime.now().isoformat() + "Z"
        },
        "errors": None
    }

@app.put("/preregistration/v1/booking/appointment/{prid}")
async def mosip_update_appointment(prid: str, request: Request):
    """Mock update/reschedule appointment"""
    try:
        body = await request.json()
    except:
        body = {}
    
    return {
        "response": {
            "bookingMessage": "Appointment updated successfully",
            "preRegistrationId": prid
        },
        "errors": None
    }

@app.delete("/preregistration/v1/booking/appointment/{prid}")
async def mosip_cancel_appointment(prid: str):
    """Mock cancel appointment"""
    return {
        "response": {
            "message": "Appointment cancelled successfully",
            "preRegistrationId": prid
        },
        "errors": None
    }

@app.get("/preregistration/v1/booking/appointment/{prid}")
async def mosip_get_appointment(prid: str):
    """Mock get appointment details"""
    return {
        "response": {
            "preRegistrationId": prid,
            "registration_center_id": "10001",
            "registration_center_name": "MOSIP Registration Center 1",
            "appointment_date": "2024-01-15",
            "time_slot_from": "09:00:00",
            "time_slot_to": "09:15:00"
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/registrationcenters/{lang_code}/{hierarchy_level}/names")
async def mosip_regcenters_by_names(lang_code: str, hierarchy_level: str, name: str = None):
    """Mock get registration centers by location names (query param)"""
    return {
        "response": {
            "registrationCenters": [
                {
                    "id": "10001",
                    "name": "MOSIP Registration Center - Rabat",
                    "centerTypeCode": "REG",
                    "addressLine1": "123 Main Street, Downtown",
                    "addressLine2": "Near City Hall",
                    "latitude": "33.9716",
                    "longitude": "-6.8498",
                    "locationCode": "RABAT_CITY",
                    "langCode": lang_code,
                    "numberOfKiosks": 5,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "lunchStartTime": "13:00:00",
                    "lunchEndTime": "14:00:00",
                    "isActive": True
                },
                {
                    "id": "10002",
                    "name": "MOSIP Registration Center - Agdal",
                    "centerTypeCode": "REG",
                    "addressLine1": "456 Agdal Avenue",
                    "addressLine2": "Business District",
                    "latitude": "33.989523",
                    "longitude": "-6.849813",
                    "locationCode": "AGDAL",
                    "langCode": lang_code,
                    "numberOfKiosks": 3,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "lunchStartTime": "12:30:00",
                    "lunchEndTime": "13:30:00",
                    "isActive": True
                }
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/getcoordinatespecificregistrationcenters/{lang_code}/{longitude}/{latitude}/{distance}")
async def mosip_nearby_centers(lang_code: str, longitude: str, latitude: str, distance: str = None):
    """Mock get nearby registration centers by coordinates"""
    return {
        "response": {
            "registrationCenters": [
                {
                    "id": "10001",
                    "name": "MOSIP Registration Center - Nearby",
                    "centerTypeCode": "REG",
                    "addressLine1": "Nearest Location",
                    "addressLine2": "Near Your Location",
                    "latitude": latitude,
                    "longitude": longitude,
                    "locationCode": "NEARBY",
                    "langCode": lang_code,
                    "numberOfKiosks": 5,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "lunchStartTime": "13:00:00",
                    "lunchEndTime": "14:00:00",
                    "isActive": True
                },
                {
                    "id": "10002",
                    "name": "MOSIP Registration Center - City",
                    "centerTypeCode": "REG",
                    "addressLine1": "City Center Location",
                    "addressLine2": "Downtown Area",
                    "latitude": str(float(latitude) + 0.01),
                    "longitude": str(float(longitude) + 0.01),
                    "locationCode": "CITY_CENTER",
                    "langCode": lang_code,
                    "numberOfKiosks": 3,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "lunchStartTime": "12:30:00",
                    "lunchEndTime": "13:30:00",
                    "isActive": True
                }
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/registrationcenters/{lang_code}/{hierarchy_level}/{location_codes}")
async def mosip_registration_centers(lang_code: str, hierarchy_level: int, location_codes: str):
    """Mock get registration centers"""
    return {
        "response": {
            "registrationCenters": [
                {
                    "id": "10001",
                    "name": "Rabat Central Registration Center",
                    "centerTypeCode": "REG",
                    "addressLine1": "123 Main Street",
                    "addressLine2": "Building A",
                    "addressLine3": "",
                    "latitude": "34.020882",
                    "longitude": "-6.841650",
                    "locationCode": "RABAT_CITY",
                    "holidayLocationCode": "RABAT",
                    "contactPhone": "+212-537-123456",
                    "workingHours": "9:00 AM - 5:00 PM",
                    "langCode": lang_code,
                    "numberOfKiosks": 5,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "lunchStartTime": "13:00:00",
                    "lunchEndTime": "14:00:00",
                    "isActive": True
                },
                {
                    "id": "10002",
                    "name": "Agdal Registration Center",
                    "centerTypeCode": "REG",
                    "addressLine1": "456 Agdal Avenue",
                    "latitude": "33.989523",
                    "longitude": "-6.849813",
                    "locationCode": "AGDAL",
                    "langCode": lang_code,
                    "numberOfKiosks": 3,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "isActive": True
                }
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/workingdays/{center_id}/{lang_code}")
async def mosip_working_days(center_id: str, lang_code: str):
    """Mock get working days for a center"""
    return {
        "response": {
            "workingdays": [
                {"code": "101", "name": "MON", "dayCode": "1", "langCode": lang_code, "isActive": True, "isWorking": True},
                {"code": "102", "name": "TUE", "dayCode": "2", "langCode": lang_code, "isActive": True, "isWorking": True},
                {"code": "103", "name": "WED", "dayCode": "3", "langCode": lang_code, "isActive": True, "isWorking": True},
                {"code": "104", "name": "THU", "dayCode": "4", "langCode": lang_code, "isActive": True, "isWorking": True},
                {"code": "105", "name": "FRI", "dayCode": "5", "langCode": lang_code, "isActive": True, "isWorking": True},
                {"code": "106", "name": "SAT", "dayCode": "6", "langCode": lang_code, "isActive": True, "isWorking": False},
                {"code": "107", "name": "SUN", "dayCode": "7", "langCode": lang_code, "isActive": True, "isWorking": False}
            ]
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/exceptionalholidays/{center_id}/{lang_code}")
async def mosip_exceptional_holidays(center_id: str, lang_code: str):
    """Mock get exceptional holidays"""
    return {
        "response": {
            "exceptionalHolidayList": []
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/blocklistedwords/{lang_code}")
async def mosip_blocklisted_words(lang_code: str):
    """Mock get blocklisted words"""
    return {
        "response": {
            "blockListedWords": []
        },
        "errors": None
    }

@app.get("/preregistration/v1/appointment/availability/{center_id}")
async def mosip_appointment_availability(center_id: str):
    """Mock get appointment slots availability"""
    from datetime import datetime, timedelta
    
    # Generate available slots for next 30 days
    slots = []
    today = datetime.now()
    
    for i in range(30):
        date = today + timedelta(days=i)
        if date.weekday() < 5:  # Monday to Friday
            slots.append({
                "date": date.strftime("%Y-%m-%d"),
                "timeslots": [
                    {"fromTime": "09:00:00", "toTime": "09:15:00", "availability": 5},
                    {"fromTime": "09:15:00", "toTime": "09:30:00", "availability": 5},
                    {"fromTime": "09:30:00", "toTime": "09:45:00", "availability": 5},
                    {"fromTime": "09:45:00", "toTime": "10:00:00", "availability": 5},
                    {"fromTime": "10:00:00", "toTime": "10:15:00", "availability": 5},
                    {"fromTime": "10:15:00", "toTime": "10:30:00", "availability": 5},
                    {"fromTime": "10:30:00", "toTime": "10:45:00", "availability": 5},
                    {"fromTime": "10:45:00", "toTime": "11:00:00", "availability": 5},
                    {"fromTime": "11:00:00", "toTime": "11:15:00", "availability": 5},
                    {"fromTime": "11:15:00", "toTime": "11:30:00", "availability": 5},
                    {"fromTime": "14:00:00", "toTime": "14:15:00", "availability": 5},
                    {"fromTime": "14:15:00", "toTime": "14:30:00", "availability": 5},
                    {"fromTime": "14:30:00", "toTime": "14:45:00", "availability": 5},
                    {"fromTime": "14:45:00", "toTime": "15:00:00", "availability": 5},
                    {"fromTime": "15:00:00", "toTime": "15:15:00", "availability": 5},
                    {"fromTime": "15:15:00", "toTime": "15:30:00", "availability": 5},
                    {"fromTime": "16:00:00", "toTime": "16:15:00", "availability": 5},
                    {"fromTime": "16:15:00", "toTime": "16:30:00", "availability": 5}
                ],
                "holiday": False
            })
    
    return {
        "response": {
            "regCenterId": center_id,
            "centerDetails": slots
        },
        "errors": None
    }

@app.post("/preregistration/v1/appointment/{prid}")
async def mosip_book_appointment(prid: str, request: dict = None):
    """Mock book appointment"""
    return {
        "response": {
            "preRegistrationId": prid,
            "message": "Appointment booked successfully",
            "bookingDataPrimary": request.get("bookingRequest") if request else {}
        },
        "errors": None
    }

@app.delete("/preregistration/v1/appointment/{prid}")
async def mosip_cancel_appointment(prid: str):
    """Mock cancel appointment"""
    return {
        "response": {
            "preRegistrationId": prid,
            "message": "Appointment cancelled successfully"
        },
        "errors": None
    }

@app.get("/preregistration/v1/appointment/{prid}")
async def mosip_get_appointment(prid: str):
    """Mock get appointment details"""
    return {
        "response": {
            "preRegistrationId": prid,
            "registration_center_id": "10001",
            "appointment_date": "2024-12-20",
            "time_slot_from": "10:00:00",
            "time_slot_to": "10:15:00"
        },
        "errors": None
    }

# ============== APPOINTMENT SLOTS ENDPOINT ==============

@app.get("/preregistration/v1/applications/appointment/slots/availability/{center_id}")
async def mosip_appointment_slots_availability(center_id: str):
    """Mock get appointment slots availability for booking"""
    from datetime import datetime, timedelta
    
    slots = []
    today = datetime.now()
    
    for i in range(1, 15):  # Next 14 days
        date = today + timedelta(days=i)
        if date.weekday() < 5:  # Weekdays only
            slots.append({
                "date": date.strftime("%Y-%m-%d"),
                "timeSlots": [
                    {"fromTime": "09:00", "toTime": "09:15", "availability": 5},
                    {"fromTime": "09:15", "toTime": "09:30", "availability": 5},
                    {"fromTime": "09:30", "toTime": "09:45", "availability": 4},
                    {"fromTime": "10:00", "toTime": "10:15", "availability": 6},
                    {"fromTime": "10:15", "toTime": "10:30", "availability": 5},
                    {"fromTime": "11:00", "toTime": "11:15", "availability": 5},
                    {"fromTime": "14:00", "toTime": "14:15", "availability": 5},
                    {"fromTime": "14:15", "toTime": "14:30", "availability": 4},
                    {"fromTime": "15:00", "toTime": "15:15", "availability": 5},
                    {"fromTime": "15:15", "toTime": "15:30", "availability": 5}
                ]
            })
    
    return {
        "response": {
            "regCenterId": center_id,
            "centerDetails": slots
        },
        "errors": None
    }

# ============== QR CODE ENDPOINT ==============

@app.post("/preregistration/v1/qrCode/generate")
async def mosip_generate_qrcode(request: Request):
    """Mock generate QR code - returns simple valid base64 PNG"""
    # Simple 50x50 gray QR code placeholder
    return {
        "response": {
            "qrcode": "iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAIAAACRXR/mAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH5wEBCjMfL8lKVAAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAABTSURBVFjD7c4xAQAgDASxyn/oAh4wwZ0EHr5tbWbeAgAAANiG/gIAAACghv4CAAAAAOjXX15eXl5eXl5eXl5eXl5eXl5eXl5eXl4AAAAAAPhvPwA/QwGlJ2wKJAAAAABJRU5ErkJggg=="
        },
        "errors": None
    }

# ============== NOTIFICATION ENDPOINTS ==============

@app.post("/preregistration/v1/notification")
async def mosip_send_notification(request: Request):
    """Mock send notification"""
    return {
        "response": {
            "message": "Notification sent successfully",
            "status": "success"
        },
        "errors": None
    }

@app.post("/preregistration/v1/notification/notify")
async def mosip_notify(request: Request):
    """Mock notify endpoint"""
    return {
        "response": {
            "message": "Notification sent successfully",
            "status": "success"
        },
        "errors": None
    }

# ============== CAPTCHA ENDPOINT ==============

@app.post("/preregistration/v1/captcha/validatecaptcha")
async def mosip_validate_captcha(request: Request):
    """Mock validate captcha"""
    return {
        "response": {
            "success": True,
            "message": "Captcha validated"
        },
        "errors": None
    }

# ============== TRANSLITERATION ENDPOINT ==============

@app.post("/preregistration/v1/transliteration/transliterate")
async def mosip_transliterate(request: Request):
    """Mock transliteration"""
    try:
        body = await request.json()
        from_value = body.get("request", {}).get("fromFieldValue", "")
    except:
        from_value = ""
    
    return {
        "response": {
            "toFieldValue": from_value
        },
        "errors": None
    }

# ============== REGISTRATION CENTER BY ID ENDPOINT ==============

@app.get("/preregistration/v1/proxy/masterdata/registrationcenters/{center_id}/{lang_code}")
async def mosip_regcenter_by_id(center_id: str, lang_code: str):
    """Mock get registration center by ID"""
    return {
        "response": {
            "registrationCenters": [
                {
                    "id": center_id,
                    "name": f"MOSIP Registration Center {center_id}",
                    "centerTypeCode": "REG",
                    "addressLine1": "123 Main Street",
                    "addressLine2": "Downtown",
                    "latitude": "33.9716",
                    "longitude": "-6.8498",
                    "locationCode": "RABAT_CITY",
                    "langCode": lang_code,
                    "numberOfKiosks": 5,
                    "perKioskProcessTime": "00:15:00",
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "lunchStartTime": "13:00:00",
                    "lunchEndTime": "14:00:00",
                    "isActive": True
                }
            ]
        },
        "errors": None
    }

# ============== PAGED REGISTRATION CENTERS ==============

@app.get("/preregistration/v1/proxy/masterdata/registrationcenters/page/{lang_code}/{hierarchy_level}/{search_text}")
async def mosip_regcenters_paged(lang_code: str, hierarchy_level: str, search_text: str, pageNumber: int = 0, pageSize: int = 10):
    """Mock paged registration centers search"""
    return {
        "response": {
            "registrationCenters": [
                {
                    "id": "10001",
                    "name": f"MOSIP Center - {search_text}",
                    "centerTypeCode": "REG",
                    "addressLine1": "123 Main Street",
                    "latitude": "33.9716",
                    "longitude": "-6.8498",
                    "locationCode": "RABAT_CITY",
                    "langCode": lang_code,
                    "numberOfKiosks": 5,
                    "centerStartTime": "09:00:00",
                    "centerEndTime": "17:00:00",
                    "isActive": True
                }
            ],
            "totalItems": 1,
            "pageNo": pageNumber,
            "totalPages": 1
        },
        "errors": None
    }

# ============== LOG AUDIT ENDPOINT ==============

@app.post("/preregistration/v1/logAudit")
async def mosip_log_audit(request: Request):
    """Mock log audit"""
    return {
        "response": {
            "status": "success"
        },
        "errors": None
    }

# ============== APPLICATION STATUS ENDPOINTS ==============

@app.get("/preregistration/v1/applications/prereg/status/{prid}")
async def mosip_get_app_status(prid: str):
    """Mock get application status"""
    return {
        "response": {
            "preRegistrationId": prid,
            "statusCode": "Pending_Appointment"
        },
        "errors": None
    }

# ============== DOCUMENT ENDPOINTS ==============

@app.post("/preregistration/v1/documents/{prid}")
async def mosip_upload_document(prid: str, request: Request):
    """Mock upload document"""
    import uuid
    doc_id = str(uuid.uuid4())[:8].upper()
    return {
        "response": {
            "docId": doc_id,
            "docName": "document.pdf",
            "preRegistrationId": prid,
            "docCatCode": "POI",
            "docTypCode": "PASSPORT",
            "statusCode": "Pending_Appointment"
        },
        "errors": None
    }

@app.delete("/preregistration/v1/documents/{doc_id}")
async def mosip_delete_document(doc_id: str, preRegistrationId: str = None):
    """Mock delete document"""
    return {
        "response": {
            "message": "Document deleted successfully"
        },
        "errors": None
    }

@app.get("/preregistration/v1/documents/{doc_id}")
async def mosip_get_document(doc_id: str, preRegistrationId: str = None):
    """Mock get document"""
    return {
        "response": {
            "document": ""
        },
        "errors": None
    }

@app.put("/preregistration/v1/documents/document/{doc_id}")
async def mosip_update_document_ref(doc_id: str, preRegistrationId: str = None, refNumber: str = None):
    """Mock update document reference"""
    return {
        "response": {
            "message": "Document reference updated"
        },
        "errors": None
    }

# ============== HOLIDAYS ENDPOINT ==============

@app.get("/preregistration/v1/proxy/masterdata/holidays/{location_code}/{lang_code}")
async def mosip_holidays(location_code: str, lang_code: str):
    """Mock get holidays"""
    return {
        "response": {
            "holidays": []
        },
        "errors": None
    }

@app.get("/preregistration/v1/proxy/masterdata/templates/templatetypecodes/{template_type}")
async def mosip_templates_by_type(template_type: str):
    """Mock get templates by type code"""
    return {
        "response": {
            "templates": [
                {
                    "id": "1",
                    "langCode": "eng",
                    "templateTypeCode": template_type,
                    "fileText": "Please arrive 15 minutes before your appointment.\nBring your original documents.\nWear appropriate attire."
                }
            ]
        },
        "errors": None
    }

print("✅ Mock MOSIP endpoints added for local testing")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting OCR Text Extraction Server...")
    print("="*60)
    print(f"📡 Server running at: http://localhost:8001")
    print(f"📡 Alternative: http://127.0.0.1:8001")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)

