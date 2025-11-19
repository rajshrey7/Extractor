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
from typing import Optional, Dict, List, Any
import base64
from difflib import SequenceMatcher
import os
import uuid
import requests
from ocr_verifier import OCRVerifier
from job_form_filler import JobFormFiller
from config import OPENROUTER_API_KEY, LLAMA_CLOUD_API_KEY, DEFAULT_MODEL, OPENROUTER_MODELS, GOOGLE_VISION_API_KEY, SELECTED_LANGUAGE
from language_support import LanguageLoader

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

# Initialize models
MODEL_PATH = "Mymodel.pt"
yolo_model = None
ocr_reader = None
language_loader = LanguageLoader(SELECTED_LANGUAGE)
verifier = OCRVerifier(SELECTED_LANGUAGE)

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
            ocr_langs = language_loader.get_ocr_lang()
            print(f"📦 Languages: {ocr_langs}")
            ocr_reader = easyocr.Reader(ocr_langs)
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

def convert_image_to_json_with_google_vision(image_bytes: bytes) -> Dict:
    """
    Convert image directly to JSON using Google Vision API with proper structured extraction
    """
    try:
        import base64
        import re
        import io
        
        # Encode image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Prepare the request to Google Vision API
        url = f"https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_API_KEY}"
        
        payload = {
            "requests": [
                {
                    "image": {
                        "content": image_base64
                    },
                    "features": [
                        {
                            "type": "DOCUMENT_TEXT_DETECTION",  # Better for structured documents
                            "maxResults": 1
                        }
                    ],
                    "imageContext": {
                        "languageHints": language_loader.get_google_vision_lang()
                    }
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract text and structured data from Google Vision response
            extracted_text = ""
            blocks_data = []
            
            if "responses" in result and len(result["responses"]) > 0:
                response_data = result["responses"][0]
                
                # Check for errors
                if "error" in response_data:
                    error_msg = response_data["error"].get("message", "Unknown error")
                    print(f"Google Vision API error: {error_msg}")
                    return {}
                
                # Get full text annotation (document text detection) - provides structured layout
                if "fullTextAnnotation" in response_data:
                    full_text_annotation = response_data["fullTextAnnotation"]
                    extracted_text = full_text_annotation.get("text", "")
                    
                    # Extract structured blocks with bounding boxes and confidence
                    if "pages" in full_text_annotation:
                        for page in full_text_annotation["pages"]:
                            if "blocks" in page:
                                for block in page["blocks"]:
                                    block_text = ""
                                    if "paragraphs" in block:
                                        for paragraph in block["paragraphs"]:
                                            para_text = ""
                                            if "words" in paragraph:
                                                for word in paragraph["words"]:
                                                    word_text = ""
                                                    if "symbols" in word:
                                                        word_text = "".join([symbol.get("text", "") for symbol in word["symbols"]])
                                                    para_text += word_text + " "
                                            block_text += para_text.strip() + " "
                                    
                                    if block_text.strip():
                                        blocks_data.append({
                                            "text": block_text.strip(),
                                            "confidence": block.get("confidence", 0.0),
                                            "block_type": block.get("blockType", "UNKNOWN")
                                        })
                
                # Fallback to text annotations if fullTextAnnotation not available
                elif "textAnnotations" in response_data and len(response_data["textAnnotations"]) > 0:
                    extracted_text = response_data["textAnnotations"][0].get("description", "")
            
            if not extracted_text:
                print("No text detected in image")
                return {}
            
            # Parse extracted text into structured JSON using both raw text and blocks
            structured_data = parse_text_to_json_advanced(extracted_text, blocks_data)
            return structured_data
        else:
            error_text = response.text[:500] if hasattr(response, 'text') else str(response.status_code)
            print(f"Google Vision API error {response.status_code}: {error_text}")
            print(f"Full response: {response.text[:1000]}")
            return {}
            
    except requests.exceptions.RequestException as e:
        print(f"Google Vision API request error: {str(e)}")
        return {}
    except Exception as e:
        print(f"Google Vision image conversion error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

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
            # For Google Vision API, we need RGB format, not BGR
            if use_openai:
                # Convert BGR to RGB for Google Vision API
                if len(img_array.shape) == 3:
                    img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                else:
                    img_rgb = img_array
                
                # Encode as PNG for Google Vision API
                img_pil = Image.fromarray(img_rgb)
                img_buffer = io.BytesIO()
                img_pil.save(img_buffer, format='PNG')
                img_bytes = img_buffer.getvalue()
                
                # Use Google Vision API for this page
                page_result = convert_image_to_json_with_google_vision(img_bytes)
                if page_result:
                    all_extracted_fields.update(page_result)
                    found_idcard = True
                else:
                    print(f"Warning: Google Vision API returned no results for page {page_num + 1}")
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
            "method": "google_vision" if use_openai else "yolo_easyocr"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    use_openai: Optional[str] = Form(None)
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
        
        print(f"File: {filename}, Size: {len(contents)} bytes")
        sys.stdout.flush()
        
        # Check if it's a PDF
        is_pdf = filename.lower().endswith('.pdf')
        use_openai_flag = use_openai and use_openai.lower() == 'true'
        
        print(f"Is PDF: {is_pdf}, Use OpenAI: {use_openai_flag}")
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
        
        # Process image
        if use_openai_flag:
            print("Using Google Vision API...")
            sys.stdout.flush()
            try:
                google_vision_result = convert_image_to_json_with_google_vision(contents)
                if google_vision_result:
                    print("Google Vision processing successful")
                    print(f"Extracted {len(google_vision_result)} fields")
                    sys.stdout.flush()
                    return JSONResponse(content={
                        "success": True,
                        "filename": filename,
                        "extracted_fields": google_vision_result,
                        "general_text": [],
                        "found_idcard": True,
                        "google_vision_converted": True,
                        "method": "google_vision",
                        "file_type": "image"
                    })
                else:
                    print("Google Vision returned empty result, falling back to YOLO...")
                    sys.stdout.flush()
            except Exception as gv_err:
                print(f"Google Vision API error: {str(gv_err)}")
                print("Falling back to YOLO...")
                sys.stdout.flush()
                import traceback
                traceback.print_exc()
        
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
        from rag_workflow_with_human_feedback import RAGWorkflowWithHumanFeedback
        from llama_index.core.workflow import StartEvent, StopEvent, InputRequiredEvent
        
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
        from rag_workflow_with_human_feedback import RAGWorkflowWithHumanFeedback
        from llama_index.core.workflow import StopEvent
        
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

