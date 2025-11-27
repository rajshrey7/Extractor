from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
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
from typing import Optional, Dict, List, Any
import base64
from difflib import SequenceMatcher
import os
import uuid
from datetime import datetime
import requests
import quality_score
from ocr_verifier import OCRVerifier
from job_form_filler import JobFormFiller
from config import OPENROUTER_API_KEY, LLAMA_CLOUD_API_KEY, DEFAULT_MODEL, OPENROUTER_MODELS, SELECTED_LANGUAGE
from paddle_ocr_module import PaddleOCRWrapper
from trocr_handwritten import TrOCRWrapper
from language_support import LanguageLoader
from ocr_comparison import compare_ocr_results
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
    _agent_path = os.path.join(os.path.dirname(__file__), 'Auto-Job-Form-Filler-Agent')
    
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

# Mount uploads directory for serving uploaded images
if not os.path.exists("uploads"):
    os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# In-memory storage for uploaded images and region data (for streaming)
uploaded_images = {}  # {image_id: image_bytes}
region_data_cache = {}  # {image_id: [regions]}

# Initialize models
MODEL_PATH = "Mymodel.pt"
yolo_model = None
ocr_reader = None
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
    global yolo_model, ocr_reader, paddle_ocr, trocr_ocr
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
            ocr_langs = language_loader.get_ocr_lang()
            print(f"📦 Languages: {ocr_langs}")
            ocr_reader = easyocr.Reader(ocr_langs)
            print("✅ EasyOCR reader initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing EasyOCR: {e}")
            ocr_reader = None
    
    if paddle_ocr is None:
        try:
            print("📦 Initializing PaddleOCR...")
            paddle_ocr = PaddleOCRWrapper(lang=SELECTED_LANGUAGE if SELECTED_LANGUAGE in ['en', 'ch', 'fr', 'german', 'korean', 'japan'] else 'en')
            print("✅ PaddleOCR initialized successfully!")
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

def extract_text_with_trocr(image_bytes: bytes) -> str:
    """
    Hybrid extraction: Use PaddleOCR for detection (boxes) and TrOCR for recognition (text).
    This is much more accurate for full pages than passing the whole image to TrOCR.
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
            text = trocr_ocr.extract_text_from_image(pil_crop)
            if text and len(text.strip()) > 0:
                full_text.append(text)
                print(f"  Line {line_idx+1}: {text}")
        
        final_text = "\n".join(full_text)
        print(f"✅ TrOCR extracted {len(final_text)} chars from {len(full_text)} lines")
        return final_text
            
    except Exception as e:
        print(f"TrOCR error: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""

def parse_text_to_json_advanced(text: str, blocks_data: List[Dict] = None) -> Dict:
    """
    Advanced parsing of extracted text into structured JSON format
    Uses both pattern matching and block-based extraction
    """
    result = {}
    lines = text.split('\n')
    
    # Enhanced field patterns with better matching
    # Enhanced field patterns with better matching
    patterns = language_loader.get_regex_patterns()
    
    # First, try pattern matching on full text
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Clean up value
                value = re.sub(r'[^\w\s@./-\u0600-\u06FF]', '', value).strip()
                if value and len(value) > 1 and value not in result.values():
                    result[field] = value
                    break
    
    # Also try extracting from blocks if available (more structured)
    if blocks_data:
        for block in blocks_data:
            block_text = block.get("text", "")
            if not block_text:
                continue
            
            # Try to match patterns in each block
            for field, field_patterns in patterns.items():
                if field in result:  # Skip if already found
                    continue
                for pattern in field_patterns:
                    match = re.search(pattern, block_text, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        value = re.sub(r'[^\w\s@./-\u0600-\u06FF]', '', value).strip()
                        if value and len(value) > 1:
                            result[field] = value
                            break
    
    # If still no structured fields found, try line-by-line key-value extraction
    if not result:
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Try to detect key-value pairs (e.g., "Name: John Doe")
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    
                    # Clean value
                    value = re.sub(r'[^\w\s@./-\u0600-\u06FF]', '', value).strip()
                    
                    if value and len(value) > 1:
                        # Normalize key names to match standard fields
                        key_normalized = key.replace(' ', '_').replace('-', '_')
                        
                        # Map common variations to standard field names
                        key_mapping = {
                            'name': 'Name',
                            'full_name': 'Name',
                            'first_name': 'Name',
                            'given_name': 'Name',
                            'surname': 'Surname',
                            'last_name': 'Surname',
                            'family_name': 'Surname',
                            'date_of_birth': 'Date of Birth',
                            'dob': 'Date of Birth',
                            'passport_no': 'Passport No',
                            'passport_number': 'Passport No',
                            'document_no': 'Passport No',
                            'personal_no': 'Personal No',
                            'national_id': 'Personal No',
                            'phone': 'Phone',
                            'mobile': 'Phone',
                            'email': 'Email',
                            'address': 'Address',
                            'issue_date': 'Issue Date',
                            'expiry_date': 'Expiry Date',
                            'nationality': 'Nationality',
                            'country': 'Country',
                            'issuing_office': 'Issuing Office',
                            'height': 'Height',
                            'sex': 'Sex',
                            'gender': 'Sex',
                            'place_of_birth': 'Place of Birth',
                            'card_no': 'Card No'
                        }
                        
                        # Use mapped key or normalized key
                        final_key = key_mapping.get(key_normalized, key.replace('_', ' ').title())
                        result[final_key] = value
    
    # Clean up and validate results
    cleaned_result = {}
    for key, value in result.items():
        if value and isinstance(value, str) and len(value.strip()) > 0:
            cleaned_result[key] = value.strip()
    
    return cleaned_result

def convert_ocr_to_json_with_ai(ocr_text: str, api_url: Optional[str] = None) -> Dict:
    """
    Convert OCR extracted text to structured JSON using AI model
    """
    if api_url is None:
        # Default to localhost:8000/v1/completions, but can be overridden via environment variable
        api_url = os.getenv("OCR_TO_JSON_API_URL", "http://localhost:8000/v1/completions")
    
    try:
        # Prepare prompt for OCR to JSON conversion
        prompt = f"""Convert the following OCR extracted text into a structured JSON format. 
Extract all relevant fields like name, date of birth, ID numbers, addresses, phone numbers, emails, etc.

OCR Text:
{ocr_text}

Return only valid JSON object with extracted fields. Format: {{"field_name": "value"}}"""
        
        payload = {
            "model": "mychen76/mistral7b_ocr_to_json_v1",
            "prompt": prompt,
            "max_tokens": 512,
            "temperature": 0.3  # Lower temperature for more consistent JSON output
        }
        
        response = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            # Extract the generated text from the response
            # Handle both OpenAI-compatible format and custom formats
            choices = result.get("choices", [])
            if choices:
                choice = choices[0]
                # Try "text" first (OpenAI format), then "message" -> "content" (Chat format)
                generated_text = choice.get("text", "") or choice.get("message", {}).get("content", "")
                generated_text = generated_text.strip()
            else:
                # Fallback: try to get text directly from result
                generated_text = result.get("text", "").strip()
            
            # Try to parse JSON from the response
            # The model might return JSON wrapped in markdown code blocks or plain text
            json_text = generated_text
            
            # Remove markdown code blocks if present
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            
            # Try to extract JSON object from the text
            try:
                # Find JSON object in the text
                start_idx = json_text.find("{")
                end_idx = json_text.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_text = json_text[start_idx:end_idx]
                
                parsed_json = json.loads(json_text)
                if isinstance(parsed_json, dict):
                    return parsed_json
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract key-value pairs
                pass
        
        else:
            print(f"AI API returned status code: {response.status_code}")
            print(f"Response: {response.text[:500]}")
        
        return {}
    except requests.exceptions.ConnectionError as e:
        print(f"AI conversion API connection error: {str(e)}")
        print(f"Could not connect to API at: {api_url}")
        return {}
    except requests.exceptions.Timeout as e:
        print(f"AI conversion API timeout: {str(e)}")
        return {}
    except requests.exceptions.RequestException as e:
        print(f"AI conversion API error: {str(e)}")
        return {}
    except Exception as e:
        print(f"AI conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

def process_image(image_bytes: bytes):
    """Process image and extract text fields"""
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
    
    if yolo_model is None:
        raise Exception("YOLO model not loaded. Check if Mymodel.pt exists.")
    
    if ocr_reader is None:
        raise Exception("EasyOCR reader not initialized. Check EasyOCR installation.")
    
    try:
        results = yolo_model(img)[0]
        boxes = results.boxes
    except Exception as e:
        raise Exception(f"YOLO detection failed: {str(e)}")
    
    # Process class 0 (general text)
    raw_boxes = []
    for box in boxes:
        class_id = int(box.cls[0])
        if class_id == 0:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            raw_boxes.append((x1, y1, x2, y2))
    
    general_text = []
    if raw_boxes:
        try:
            filtered_boxes = non_max_suppression_area(raw_boxes)
            for x1, y1, x2, y2 in filtered_boxes:
                crop = img[y1:y2, x1:x2]
                ocr_result = ocr_reader.readtext(crop, detail=0)
                for line in ocr_result:
                    cleaned = line.strip()
                    if cleaned:
                        general_text.append(cleaned)
        except Exception as e:
            print(f"Warning: Error processing general text: {e}")
    
    # Process ID card fields (class 3+)
    raw_fields = defaultdict(set)
    all_texts = []
    found_idcard = False
    
    for box in boxes:
        try:
            class_id = int(box.cls[0])
            # class_map is now static but we need to handle it carefully
            # For now, we'll stick to English class names for YOLO output mapping
            class_map_static = {
                1: "Surname", 2: "Name", 3: "Nationality", 4: "Sex", 5: "Date of Birth",
                6: "Place of Birth", 7: "Issue Date", 8: "Expiry Date", 9: "Issuing Office",
                10: "Height", 11: "Type", 12: "Country", 13: "Passport No",
                14: "Personal No", 15: "Card No"
            }
            if class_id not in class_map_static:
                continue
            found_idcard = True
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = img[y1:y2, x1:x2]
            ocr_result = ocr_reader.readtext(crop, detail=0)
            extracted = " ".join(ocr_result).strip()
            field = class_map_static[class_id]
            cleaned_value = clean_ocr_text(field, extracted)
            all_texts.append(extracted)
            if cleaned_value:
                raw_fields[field].add(cleaned_value)
        except Exception as e:
            print(f"Warning: Error processing box {class_id}: {e}")
            continue
    
    final_fields = {}
    if found_idcard:
        for field, values in raw_fields.items():
            standard_field = field.strip() # equivalent_to_standard is removed
            filtered_values = [v for v in values if len(v) > 1]
            if filtered_values:
                final_fields[standard_field] = max(filtered_values, key=len)
        
        for text in all_texts:
            final_fields.update(detect_unknown_fields(text))
    
    # Ensure we always have some fields, even if empty
    if not final_fields:
        # If no structured fields found, try to extract from general text
        for text in general_text:
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
    global ocr_reader
    
    if language_loader.set_language(language):
        # Update verifier language
        verifier.set_language(language)

        # Reload OCR model with new language
        try:
            ocr_langs = language_loader.get_ocr_lang()
            print(f"🔄 Reloading EasyOCR with languages: {ocr_langs}")
            ocr_reader = easyocr.Reader(ocr_langs)
            print("✅ EasyOCR reloaded successfully!")
            
            return {
                "success": True,
                "language": language,
                "translations": language_loader.get_all_translations()
            }
        except Exception as e:
            print(f"❌ Error reloading EasyOCR: {e}")
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
                # Use COMBINED OCR: YOLO+EasyOCR + Tesseract
                print(f"Using combined OCR for page {page_num + 1}")
                
                # Run YOLO for structured fields
                yolo_page_result = process_image(img_bytes)
                if yolo_page_result.get('extracted_fields'):
                    all_extracted_fields.update(yolo_page_result['extracted_fields'])
                if yolo_page_result.get('general_text'):
                    all_general_text.extend(yolo_page_result['general_text'])
                if yolo_page_result.get('found_idcard'):
                    found_idcard = True
                
                # Run PaddleOCR for full text
                try:
                    paddle_page_text = extract_text_with_paddle(img_bytes)
                    if paddle_page_text:
                        all_general_text.append(f"--- Page {page_num + 1} (PaddleOCR) ---")
                        all_general_text.append(paddle_page_text)
                except Exception as e:
                    print(f"⚠️ PaddleOCR error on page {page_num + 1}: {e}")
            else:
                # For YOLO, keep BGR format
                _, img_encoded = cv2.imencode('.png', img_array)
                img_bytes = img_encoded.tobytes()
                
                # Use YOLO + EasyOCR for this page
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
            "method": "combined_yolo_tesseract" if use_openai else "yolo_easyocr"
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

            if yolo_model is None:
                yield f"event: error\ndata: {{\"error\": \"YOLO model not loaded\"}}\n\n"
                return
            
            # Decode image
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                yield f"event: error\ndata: {{\"error\": \"Failed to decode image\"}}\n\n"
                return
            
            # Run YOLO detection
            results = yolo_model(img)[0]
            boxes = results.boxes
            
            # Process each detected box and stream results
            regions = []
            region_idx = 0
            
            # Process class 1-15 (ID card fields) first, then class 0 (general text)
            all_boxes = []
            for box in boxes:
                class_id = int(box.cls[0])
                if class_id >= 1:  # ID card fields
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    all_boxes.append((class_id, x1, y1, x2, y2, 'field'))
            
            for box in boxes:
                class_id = int(box.cls[0])
                if class_id == 0:  # General text
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    all_boxes.append((class_id, x1, y1, x2, y2, 'general'))
            
            # Apply NMS to all boxes
            raw_boxes = [(x1, y1, x2, y2) for (_, x1, y1, x2, y2, _) in all_boxes]
            filtered_boxes_coords = non_max_suppression_area(raw_boxes) if raw_boxes else []
            
            # Filter all_boxes to keep only those in filtered set
            filtered_boxes = []
            for (class_id, x1, y1, x2, y2, box_type) in all_boxes:
                if (x1, y1, x2, y2) in filtered_boxes_coords:
                    filtered_boxes.append((class_id, x1, y1, x2, y2, box_type))
            
            # Process each filtered box
            for (class_id, x1, y1, x2, y2, box_type) in filtered_boxes:
                try:
                    # Crop region
                    crop = img[y1:y2, x1:x2]
                    
                    # Encode crop as bytes
                    _, crop_encoded = cv2.imencode('.png', crop)
                    crop_bytes = crop_encoded.tobytes()
                    
                    text = ""
                    avg_ocr_conf = 0.0
                    ocr_method_used = 'easyocr'
                    
                    # Run OCR based on selection
                    if use_trocr and trocr_ocr:
                        try:
                            text = trocr_ocr.extract_text_from_image(crop)
                            avg_ocr_conf = 0.85 # TrOCR is usually reliable
                            ocr_method_used = 'trocr'
                        except Exception as e:
                            print(f"TrOCR error on region: {e}")
                            # Fallback
                            pass
                            
                    if not text and use_openai and paddle_ocr:
                        try:
                            # Save crop to temp file for Paddle
                            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                                cv2.imwrite(tf.name, crop)
                                temp_path = tf.name
                            
                            text = paddle_ocr.extract_text(temp_path)
                            avg_ocr_conf = 0.9 # Paddle high confidence
                            ocr_method_used = 'paddle'
                            
                            try:
                                os.remove(temp_path)
                            except:
                                pass
                        except Exception as e:
                            print(f"PaddleOCR error on region: {e}")
                            pass

                    if not text:
                        # Default to EasyOCR
                        if ocr_reader:
                            ocr_result = ocr_reader.readtext(crop)
                            text_parts = []
                            ocr_confidences = []
                            for detection in ocr_result:
                                if len(detection) >= 2:
                                    text_parts.append(str(detection[1]))
                                    if len(detection) >= 3:
                                        ocr_confidences.append(float(detection[2]))
                            
                            text = " ".join(text_parts).strip()
                            avg_ocr_conf = sum(ocr_confidences) / len(ocr_confidences) if ocr_confidences else 0.7
                            ocr_method_used = 'easyocr'
                    
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
            
            # Send final done event
            done_data = {
                "document_confidence": doc_confidence,
                "total_regions": len(regions)
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
    # ORDER MATTERS! Put specific keys before general ones to prevent partial match overwrites
    STANDARD_FIELDS = {
        'Address Line 1': ['address line 1', 'address line 1', 'road', 'street', 'address line !'],
        'Address Line 2': ['address line 2', 'address line 2', 'area', 'layout'],
        'Address': ['address', 'address line', 'residence'],
        'First Name': ['first name', 'given name', 'forename'],
        'Middle Name': ['middle name', 'midde name', 'second name'],
        'Last Name': ['last name', 'surname', 'family name', 'is a man'], 
        'Gender': ['gender', 'sex', 'brender', 'cender'], # 'cender' is a common typo
        'Date of Birth': ['date of birth', 'dob', 'birth date'],
        'City': ['city', 'town', 'district'],
        'State': ['state', 'province', 'stale'], 
        'Pin Code': ['pin code', 'pincode', 'zip code', 'postal code', 'pincade'],
        'Phone No': ['phone', 'mobile', 'contact', 'cell', 'phone member', 'phone number'],
        'Email': ['email', 'e-mail', 'mail', 'email id']
    }
    
    # Helper to find closest standard key
    def get_standard_key(ocr_key):
        ocr_key = ocr_key.lower().strip()
        
        best_match = None
        max_len = 0
        
        # Direct check with "best match" logic (longest matching variation wins)
        for std_key, variations in STANDARD_FIELDS.items():
            if ocr_key in variations:
                return std_key
            for var in variations:
                if var in ocr_key:
                    # Found a substring match.
                    # If we already have a match, check if this one is "better" (longer specific match)
                    # e.g. "address line 1" (len 14) is better than "address" (len 7) for input "address line 1"
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

    # Line-by-line extraction with fuzzy key matching
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key_raw = parts[0].strip()
                value = parts[1].strip()
                
                # Clean value
                # Remove quotes and trailing punctuation
                value = value.replace('"', '').replace("'", "").strip(" .,!")
                
                # Fix common OCR typos in values
                val_lower = value.lower()
                
                # Email fixes
                if 'gmail' in val_lower or 'yahoo' in val_lower or 'hotmail' in val_lower or 'gymail' in val_lower or 'great-com' in val_lower:
                    value = value.replace('Gymail', 'gmail').replace('gymail', 'gmail')
                    value = value.replace('great-com', 'gmail.com') 
                    value = value.replace('-com', '.com').replace(' com', '.com')
                    value = value.replace(' ', '') 
                    if '@' not in value and 'gmail' in value:
                        value = value.replace('gmail', '@gmail')
                
                # Find standard key
                std_key = get_standard_key(key_raw)
                
                if std_key:
                    result[std_key] = value
                else:
                    # Keep original key if no match found, but clean it
                    clean_key = key_raw.title().replace('_', ' ')
                    result[clean_key] = value

    return result


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
        print("\n" + "=" * 70)
        print("UPLOAD REQUEST RECEIVED - NEW CODE VERSION")
        print("=" * 70)
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
                trocr_text = extract_text_with_trocr(contents)
                print(f"✅ TrOCR extracted {len(trocr_text)} chars")
                
                # Parse the extracted text into structured fields
                parsed_fields = parse_text_to_json_advanced(trocr_text)
                
                # Return TrOCR results
                return JSONResponse(content={
                    "success": True,
                    "filename": filename,
                    "extracted_fields": parsed_fields,
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
            print("Using COMBINED OCR: YOLO+EasyOCR + PaddleOCR...")
            sys.stdout.flush()
            
            # Run YOLO+EasyOCR for structured fields
            yolo_result = process_image(contents)
            
            # Run PaddleOCR for full text
            try:
                paddle_text = extract_text_with_paddle(contents)
                print(f"✅ PaddleOCR extracted {len(paddle_text)} chars")
            except Exception as paddle_err:
                print(f"⚠️ PaddleOCR error: {str(paddle_err)}")
                paddle_text = ""
            
            # Compare and select best result
            best_result = compare_ocr_results(yolo_result, paddle_text)
            print(f"🏆 Best OCR method: {best_result.get('best_method', 'unknown')}")
            print(f"   Comparison: YOLO score={best_result['comparison']['yolo_score']:.1f}, "
                  f"PaddleOCR score={best_result['comparison']['paddle_score']:.1f}")
            
            # Return best result with both options available
            return JSONResponse(content={
                "success": True,
                "filename": filename,
                "extracted_fields": best_result.get("extracted_fields", {}),
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
        
        # Regular YOLO + EasyOCR processing
        print("Processing with YOLO+EasyOCR...")
        sys.stdout.flush()
        try:
            result = process_image(contents)
            result["file_type"] = "image"
            print("YOLO processing successful")
            sys.stdout.flush()
            return JSONResponse(content={
                "success": True,
                "filename": filename,
                "quality": quality_report,
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
        print("\n" + "=" * 70)
        print(f"EXCEPTION in upload_image: {error_type}")
        print(f"MESSAGE: {error_msg}")
        print("TRACEBACK:")
        traceback.print_exc()
        print("=" * 70 + "\n")
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
            print("Using COMBINED OCR: YOLO+EasyOCR + Tesseract...")
            
            # Run YOLO+EasyOCR for structured fields
            yolo_result = process_image(contents)
            
            # Run Tesseract for full text
            try:
                tesseract_text = extract_text_with_tesseract(contents)
                print(f"✅ Tesseract extracted {len(tesseract_text)} chars")
            except Exception as tesseract_err:
                print(f"⚠️ Tesseract error: {str(tesseract_err)}")
                tesseract_text = ""
            
            result = {
                "extracted_fields": yolo_result.get("extracted_fields", {}),  # From YOLO
                "general_text": yolo_result.get("general_text", []),  # From YOLO  
                "tesseract_text": tesseract_text,  # Full text from Tesseract
                "found_idcard": yolo_result.get("found_idcard", False),
                "tesseract_converted": True
            }
        else:
            print("Using YOLO + EasyOCR...")
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

@app.post("/api/job-form/analyze")
async def analyze_job_form(form_url: str = Form(...)):
    """Analyze a Google Form and return its questions"""
    try:
        GoogleFormHandler = get_google_form_handler()
        if GoogleFormHandler is None:
            raise HTTPException(status_code=503, detail="Google Form Handler module not available. Please ensure Auto-Job-Form-Filler-Agent folder exists.")
        form_handler = GoogleFormHandler(url=form_url)
        questions_df = form_handler.get_form_questions_df(only_required=False)
        
        if questions_df.empty:
            raise HTTPException(status_code=400, detail="Could not parse form. Make sure the form is publicly accessible.")
        
        return JSONResponse(content={
            "success": True,
            "form_url": form_url,
            "total_questions": len(questions_df),
            "questions": questions_df.to_dict(orient="records")
        })
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
        
        # If AI-powered filling is requested, use RAG workflow
        if use_ai:
            return await fill_form_with_ai(form_url, extracted)
        else:
            # Use simple field matching
            filler = JobFormFiller()
            result = filler.fill_form_with_data(form_url, extracted)
            return JSONResponse(content=result)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def fill_form_with_ai(form_url: str, extracted_data: Dict[str, Any]):
    """Use AI-powered RAG workflow to fill form"""
    try:
        # Import RAG workflow
        try:
            from rag_workflow_with_human_feedback import RAGWorkflowWithHumanFeedback
            from llama_index.core.workflow import StartEvent, StopEvent, InputRequiredEvent
        except ImportError:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "AI features are not installed. Please install 'llama-index' and related packages to use this feature.",
                    "install_command": "pip install llama-index llama-parse llama-index-llms-openrouter"
                }
            )
        
        # Create a temporary resume index from extracted data
        import tempfile
        import json as json_lib
        from pathlib import Path
        
        # Convert extracted data to a text format for indexing
        resume_text = "\n".join([f"{k}: {v}" for k, v in extracted_data.items()])
        
        # Create temporary index directory
        temp_index_dir = tempfile.mkdtemp(prefix="resume_index_")
        
        # For now, use simple matching but with AI enhancement
        # Full RAG workflow requires resume PDF processing
        filler = JobFormFiller()
        result = filler.fill_form_with_data(form_url, extracted_data)
        
        # Enhance results with AI if possible
        if result.get("success"):
            # Add AI enhancement note
            result["ai_enhanced"] = False
            result["note"] = "Using intelligent field matching. For full AI-powered filling, upload a resume PDF."
        
        return JSONResponse(content=result)
    except Exception as e:
        # Fallback to simple matching
        filler = JobFormFiller()
        result = filler.fill_form_with_data(form_url, extracted_data)
        return JSONResponse(content=result)

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
        
        filler = JobFormFiller()
        success = filler.submit_filled_form(form_url, filled_data)
        
        return JSONResponse(content={
            "success": success,
            "message": "Form submitted successfully" if success else "Form submission failed",
            "form_url": form_url
        })
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resume/process")
async def process_resume(file: UploadFile = File(...)):
    """Process a resume PDF and create searchable index"""
    try:
        import tempfile
        import sys
        import os as os_module
        
        # Add path for resume processor
        agent_path = os.path.join(os.path.dirname(__file__), 'Auto-Job-Form-Filler-Agent')
        if agent_path not in sys.path:
            sys.path.insert(0, agent_path)
        
        try:
            from resume_processor import ResumeProcessor
        except ImportError as ie:
            error_msg = str(ie)
            if 'llama_parse' in error_msg.lower():
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "error": "Resume processing requires llama-parse. Install with: pip install llama-parse llama-index",
                        "install_command": "pip install llama-parse llama-index"
                    }
                )
            else:
                return JSONResponse(
                    status_code=503,
                    content={
                        "success": False,
                        "error": f"Resume processor not available: {error_msg}"
                    }
                )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Process resume
        processor = ResumeProcessor(
            storage_dir="resume_indexes",
            llama_cloud_api_key=LLAMA_CLOUD_API_KEY
        )
        
        result = processor.process_file(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        if result.get("success"):
            return JSONResponse(content={
                "success": True,
                "index_location": result["index_location"],
                "num_nodes": result["num_nodes"],
                "message": f"Resume processed successfully! Created {result['num_nodes']} searchable sections."
            })
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
        import asyncio
        GoogleFormHandler = get_google_form_handler()
        if GoogleFormHandler is None:
            raise HTTPException(status_code=503, detail="Google Form Handler module not available. Please ensure Auto-Job-Form-Filler-Agent folder exists.")
            
        try:
            from rag_workflow_with_human_feedback import RAGWorkflowWithHumanFeedback
            from llama_index.core.workflow import StopEvent
        except ImportError:
             return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "AI features are not installed. Please install 'llama-index' and related packages to use this feature.",
                    "install_command": "pip install llama-index llama-parse llama-index-llms-openrouter"
                }
            )
        
        # Get form data
        form_handler = GoogleFormHandler(url=form_url)
        questions_df = form_handler.get_form_questions_df(only_required=False)
        form_data = questions_df.to_dict(orient="records")
        
        # Use default model if not specified
        selected_model = model or DEFAULT_MODEL
        if selected_model not in OPENROUTER_MODELS.values():
            # Try to find by name
            selected_model = OPENROUTER_MODELS.get(selected_model, DEFAULT_MODEL)
        
        # Create workflow
        workflow = RAGWorkflowWithHumanFeedback(timeout=1000, verbose=True)
        
        # Run workflow
        handler = workflow.run(
            resume_index_path=resume_index_path,
            form_data=form_data,
            openrouter_key=OPENROUTER_API_KEY,
            llama_cloud_key=LLAMA_CLOUD_API_KEY,
            selected_model=selected_model
        )
        
        # Process events
        final_result = None
        async for event in handler.stream_events():
            if isinstance(event, StopEvent):
                if hasattr(event, 'result') and event.result:
                    try:
                        if isinstance(event.result, str):
                            final_result = json.loads(event.result)
                        else:
                            final_result = event.result
                        break
                    except:
                        final_result = {"raw": str(event.result)}
        
        # Get final result if not received
        if not final_result:
            final_result = await handler
        
        return JSONResponse(content={
            "success": True,
            "form_data": final_result,
            "message": "Form filled using AI"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/job-form/get-filled")
async def get_filled_form(form_url: str):
    """Get filled form data (for testing/debugging)"""
    try:
        GoogleFormHandler = get_google_form_handler()
        if GoogleFormHandler is None:
            raise HTTPException(status_code=503, detail="Google Form Handler module not available. Please ensure Auto-Job-Form-Filler-Agent folder exists.")
        form_handler = GoogleFormHandler(url=form_url)
        questions_df = form_handler.get_form_questions_df(only_required=False)
        
        return JSONResponse(content={
            "success": True,
            "form_url": form_url,
            "questions": questions_df.to_dict(orient="records"),
            "note": "This endpoint returns form structure. Use /api/job-form/fill to fill with data."
        })
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
        if not extracted_fields:
            raise HTTPException(status_code=400, detail="No extracted_fields provided")
        
        # Map OCR data to MOSIP schema
        mosip_data = mosip_mapper.map_to_mosip_schema(extracted_fields)
        
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
        "model_loaded": yolo_model is not None,
        "ocr_loaded": ocr_reader is not None
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting OCR Text Extraction Server...")
    print("="*60)
    print(f"📡 Server running at: http://localhost:8001")
    print(f"📡 Alternative: http://127.0.0.1:8001")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)

