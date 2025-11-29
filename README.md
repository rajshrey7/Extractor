# OCR Text Extraction & Verification System

A comprehensive, multilingual web application for extracting text from scanned documents (ID cards, forms, PDFs), intelligently auto-filling digital forms, and accurately verifying extracted data with advanced quality assessment and real-time camera capture capabilities.

## 🎯 Project Overview

This system provides an end-to-end OCR solution with advanced features:

- **Multi-Method OCR**: Extract text using YOLOv8 + EasyOCR, PaddleOCR, or combined methods with automatic best-result selection
- **Multi-Page Document Support**: Process complex PDF documents with multiple pages
- **Image Quality Assessment**: Real-time blur detection and lighting analysis with actionable feedback
- **Manual OCR Correction**: Interactive review and correction interface for extracted data
- **Camera Capture**: Built-in camera support for real-time document scanning
- **Multilingual Support**: Full English and Arabic language support for UI and OCR
- **Smart Form Auto-Fill**: AI-powered field matching and form filling for job applications
- **Advanced Data Verification**: Multi-layered validation with confidence scoring
- **Intelligent Comparison**: Automatic comparison between OCR methods to select the best result

## ✨ Key Features

### 1. **Advanced Document OCR & Text Extraction**

- **Three OCR Engines**:
  - YOLOv8 object detection + EasyOCR for structured field extraction
  - PaddleOCR for offline, full-text extraction
  - Automatic comparison and best-result selection
- **Multi-Page PDF Processing**: Extract and consolidate data from complex documents
- **Real-Time Camera Capture**: Scan documents directly using device camera
- **Language Support**: English and Arabic OCR with automatic language detection
- **Automatic Field Detection**: ID cards, passports, forms with 15+ field types
- **Structured JSON Output**: Clean, API-ready data format

### 2. **Image Quality Assessment**

- **Blur Detection**: Laplacian variance analysis with quality scoring
- **Lighting Analysis**: Automatic detection of over/underexposed images
- **Real-Time Feedback**: Instant suggestions for improving capture quality
- **Quality Thresholds**: GOOD, AVERAGE, POOR classifications with actionable recommendations

### 3. **Manual OCR Correction Interface**

- **Interactive Review**: Edit and correct OCR results before processing
- **Field Management**: Add, remove, or modify extracted fields
- **Smart Validation**: Real-time validation of corrected data
- **Skip Option**: Bypass correction if OCR results are acceptable

### 4. **Intelligent Form Auto-Fill**

- **Google Forms Integration**: Direct support for Google Forms auto-fill
- **Resume-Based Filling**: AI-powered extraction from PDF resumes
- **Smart Field Matching**: Fuzzy matching with confidence scoring
- **Multiple AI Models**: Support for various LLM providers (OpenRouter, Claude, GPT)
- **Job Application Optimization**: Specialized field matching for job forms

### 5. **Advanced Data Verification**

- **Multi-Layer Validation**: Format, content, and cross-reference verification
- **Confidence Scoring**: Field-by-field confidence metrics
- **Data Cleaning**: Automatic normalization and format correction
- **Comparison Reports**: Detailed mismatch detection and analysis
- **OCR Text Block Support**: Additional validation using raw OCR output

### 6. **Modern Multilingual Web Interface**

- **Responsive Design**: Mobile-friendly, adaptive layout
- **Drag-and-Drop Upload**: Intuitive file upload with preview
- **Real-Time Processing**: Live status updates and progress indicators
- **Language Switcher**: Seamless English ↔ Arabic switching
- **Export Capabilities**: JSON export for all extracted data
- **Interactive Tabs**: Extract, Verify, Job Form Filler, Auto-Fill

## 🚀 Quick Start

### Prerequisites

- **Python 3.8 or higher**
- **Pre-trained YOLOv8 model** (`Mymodel.pt`) - Place in the root directory
- **PaddleOCR** (optional, for offline OCR)
- Web browser (Chrome, Firefox, Edge, Safari)

### Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv

   # On Windows:
   venv\Scripts\activate

   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```
   
   > **Note**: This installs the lightweight version without AI dependencies (Llama Index). To enable AI features (Resume Parsing, AI Form Filling), install the additional packages:
   > ```bash
   > pip install llama-index llama-parse llama-index-llms-openrouter sentence-transformers faiss-cpu selenium
   > ```

4. **Configure API Keys** (optional - for advanced features):

   Edit `config.py` and add your API keys:
   ```python
   # Google Vision API Key (optional - for enhanced OCR)
   GOOGLE_VISION_API_KEY = "your-api-key-here"
   
   # OpenRouter API Key (optional - for AI-powered form filling)
   OPENROUTER_API_KEY = "your-openrouter-api-key"
   
   # Llama Cloud API Key (optional - for resume parsing)
   LLAMA_CLOUD_API_KEY = "your-llama-cloud-api-key"
   ```

5. **Configure Language** (optional):

   In `config.py`, set your preferred language:
   ```python
   SELECTED_LANGUAGE = "en"  # or "ar" for Arabic
   ```

6. **Ensure the YOLO model file is present**:
   - Download or train `Mymodel.pt` and place it in the root directory
   - The model enables YOLO-based structured field extraction

### Running the Application

**Start the server:**

```bash
python run_server.py
```

Or directly:

```bash
python app.py
```

The application will be available at: **http://localhost:8000**

## 📖 Usage Guide

### 1. Extract Text from Documents

#### Using File Upload:
1. Open `http://localhost:8000`
2. Navigate to the **"Extract Text"** tab
3. Upload an image or PDF:
   - Drag and drop the file, or
   - Click to browse and select
   - Supports: JPG, PNG, JPEG, PDF
4. (Optional) Check **"Use PaddleOCR"** for offline extraction
5. Click **"Process Image"**
6. Review the **Image Quality Report** (blur, lighting)
7. Review and correct extracted data in the **OCR Correction Modal**
8. Save or skip corrections
9. View extracted fields and full JSON output

#### Using Camera Capture:
1. Click **"📷 Use Camera"** button
2. Allow camera permissions in your browser
3. Position the document in the camera frame
4. Click **"Capture"** to take a photo
5. Review the captured image
6. Click **"Use Image"** to process, or **"Retake"** to try again

### 2. Verify Extracted Data

1. Navigate to the **"Verify Data"** tab
2. Paste extracted data (JSON format) in the first text area
   - Auto-populated if you used the Extract tab
3. (Optional) Paste original/reference data in the second text area
4. (Optional) Add OCR text block for additional validation
5. Click **"🔍 Verify & Validate Data"**
6. Review the verification report:
   - Overall verification status
   - Cleaned and normalized data
   - Field-by-field comparison with confidence scores
   - Summary statistics

### 3. Auto-Fill Job Application Forms

#### Using OCR Data:
1. Navigate to the **"Job Form Filler"** tab
2. Enter the Google Form URL
3. Click **"🔍 Analyze Form"** to detect form fields
4. Click **"✨ Fill Form with OCR Data"** to use extracted data

#### Using Resume (AI-Powered):
1. Upload a PDF resume using **"Upload Resume"**
2. Click **"Process Resume with AI"**
3. Enter the Google Form URL
4. Click **"🔍 Analyze Form"**
5. Select your preferred AI model (if needed)
6. Click **"🤖 Fill Form with AI"**
7. Review the filled form data
8. Submit the form manually

### 4. Match Fields to Custom Forms

1. Navigate to the **"Auto-Fill Form"** tab
2. Enter form field names (JSON array or line-separated)
   - Example: `["Full Name", "Email", "Phone Number"]`
3. Paste extracted data (JSON format)
   - Auto-populated if you used the Extract tab
4. Click **"🎯 Match Fields"**
5. Review matched fields with confidence scores
6. Use the matched data to fill your custom forms

## 🔌 API Endpoints

### POST `/api/upload`

Upload and process an image or PDF for OCR extraction.

**Request:**
- `file`: Image or PDF file (multipart/form-data)
- `use_openai`: `"true"` to use PaddleOCR and enable comparison (optional)

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "extracted_fields": {
    "Name": "John Doe",
    "Date of Birth": "01/01/1990",
    "Passport No": "AB123456"
  },
  "general_text": ["Additional text lines..."],
  "paddle_text": "Full raw text from PaddleOCR...",
  "found_idcard": true,
  "file_type": "pdf",
  "method": "combined_auto_best",
  "best_method": "paddle",
  "comparison": {
    "yolo_score": 85.2,
    "paddle_score": 92.1,
    "winner": "paddle"
  },
  "quality": {
    "blur_score": 158.32,
    "lighting_score": 125.45,
    "overall": "GOOD",
    "message": "Image quality is good."
  },
  "total_pages": 3
}
```

### POST `/api/verify`

Verify extracted data against original source with advanced validation.

**Request:**
- `extracted_data`: JSON string of extracted fields
- `original_data`: JSON string of original/reference fields (optional)
- `ocr_text_block`: Raw OCR text for context (optional)

**Response:**
```json
{
  "success": true,
  "cleaned_data": {
    "Name": "John Doe",
    "Email": "john.doe@example.com"
  },
  "verification_report": {
    "Name": {
      "extracted": "John Doe",
      "original": "John Doe",
      "match": true,
      "confidence": 100.0
    }
  },
  "overall_verification_status": "verified",
  "summary": {
    "total_fields": 5,
    "verified_fields": 5,
    "overall_confidence": 95.5
  }
}
```

### POST `/api/autofill`

Match extracted data to form fields with intelligent fuzzy matching.

**Request:**
- `form_fields`: JSON array of form field names
- `extracted_data`: JSON string of extracted fields

**Response:**
```json
{
  "success": true,
  "matches": {
    "Full Name": {
      "matched_field": "Name",
      "value": "John Doe",
      "confidence": 95.5
    }
  },
  "fields_matched": 8
}
```

### POST `/api/set-language`

Set the application language dynamically.

**Request:**
- `language`: Language code (`"en"` or `"ar"`)

**Response:**
```json
{
  "success": true,
  "language": "ar",
  "translations": { ... }
}
```

### GET `/api/config`

Get current configuration and translations.

**Response:**
```json
{
  "language": "en",
  "translations": { ... },
  "supported_languages": ["en", "ar"]
}
```

### GET `/api/health`

Health check endpoint to verify server and model status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "ocr_loaded": true
}
```

## 📁 Project Structure

```
extractor/
├── app.py                          # Main FastAPI backend application
├── index.html                      # Frontend web interface
├── config.py                       # Configuration (API keys, language)
├── ocr_verifier.py                 # Advanced data verification module
├── job_form_filler.py              # Form auto-fill module
├── language_support.py             # Multilingual support (EN/AR)
├── quality_score.py                # Image quality assessment
├── ocr_comparison.py               # OCR method comparison
├── paddle_ocr_module.py          # PaddleOCR wrapper
├── run_server.py                   # Server startup script
├── requirements.txt                # Project dependencies
├── Mymodel.pt                      # YOLOv8 pre-trained model (required)
├── README.md                       # This file
├── static/                         # Static assets
├── tests/                          # Test files
└── Auto-Job-Form-Filler-Agent/     # Form filling agent module
    ├── google_form_handler.py      # Google Forms integration
    ├── rag_workflow_with_human_feedback.py
    ├── resume_processor.py         # Resume parsing
    └── assets/
```

## 🎯 Supported Document Fields

The system can extract and process the following fields from ID cards and documents:

**Identity Fields:**
- Name, Surname, Full Name
- Date of Birth, Place of Birth
- Nationality, Country
- Sex/Gender
- Personal No, National ID

**Document Fields:**
- Passport No, Document No
- Card No
- Issue Date, Expiry Date
- Issuing Office, Issuing Authority

**Contact Fields:**
- Phone Number, Mobile
- Email Address
- Address, Street, City, State

**Additional Fields:**
- Height, Type
- Custom fields detected in documents

## 🌍 Multilingual Support

### Supported Languages
- **English** (`en`): Full UI and OCR support
- **Arabic** (`ar`): Full UI and OCR support with RTL layout

### Features
- Dynamic language switching without page reload
- Localized UI elements and field names
- Language-specific regex patterns for field extraction
- Bidirectional text support (LTR/RTL)
- Multilingual OCR with EasyOCR and PaddleOCR

### Switching Languages
1. Use the language dropdown in the header
2. Or set via API: `POST /api/set-language` with `language=ar` or `language=en`
3. Or configure default in `config.py`: `SELECTED_LANGUAGE = "ar"`

## 🔧 Configuration

### API Keys

Edit `config.py` to configure API keys:

```python
# Google Vision API Key for enhanced OCR (optional)
GOOGLE_VISION_API_KEY = "your-google-vision-api-key"

# OpenRouter API Key for AI models (optional)
OPENROUTER_API_KEY = "your-openrouter-api-key"

# Llama Cloud API Key for resume parsing (optional)
LLAMA_CLOUD_API_KEY = "your-llama-cloud-api-key"

# Default AI model for form filling
DEFAULT_MODEL = "gryphe/mythomax-l2-13b"

# Application language (en or ar)
SELECTED_LANGUAGE = "en"
```

### Model Configuration

- Place `Mymodel.pt` in the root directory
- The model is automatically loaded on server startup
- If the model is not found, YOLO-based OCR will be unavailable

### OCR Method Selection

**YOLO + EasyOCR (Default)**:
- Structured field extraction using trained YOLO model
- Best for ID cards, passports, and structured forms
- Requires `Mymodel.pt`

**PaddleOCR**:
- Full-text extraction, works offline
- Best for unstructured documents and dense text
- Automatically installed with requirements

**Combined Method** (Recommended):
- Runs both YOLO+EasyOCR and PaddleOCR
- Automatically selects best result based on quality scoring
- Provides comparison metrics
- Enable by checking "Use PaddleOCR" in the UI

## 🐛 Troubleshooting

### Model Not Found Error

**Issue**: `YOLO model not loaded. Check if Mymodel.pt exists.`

**Solutions**:
- Ensure `Mymodel.pt` is in the root directory
- Check the file name matches exactly (case-sensitive)
- Verify file permissions and integrity

### OCR Not Working

**Issue**: No text extracted or empty results

**Solutions**:
- Ensure EasyOCR models are downloaded (first run downloads automatically)
- Check internet connection for initial model download
- Verify image quality using the quality assessment feature
- Try enabling PaddleOCR for comparison
- Ensure the image is not rotated or heavily distorted

### Server Won't Start

**Issue**: Port 8000 already in use or other startup errors

**Solutions**:
- Check if port 8000 is available: `netstat -ano | findstr :8000` (Windows)
- Kill the blocking process or change the port in `run_server.py`
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (3.8+ required)

### Poor Extraction Accuracy

**Issue**: Incorrect or missing field values

**Solutions**:
- Review the Image Quality Report after upload
- Ensure image quality is good (high resolution, clear text, good lighting)
- Try using the Manual OCR Correction feature to fix errors
- Enable both OCR methods and let the system auto-select the best
- Use the camera capture feature for better-controlled captures
- Preprocess images (adjust brightness/contrast) if needed

### Camera Not Working

**Issue**: Camera doesn't start or permission denied

**Solutions**:
- Ensure you're using HTTPS or localhost
- Grant camera permissions in your browser
- Check browser console for specific errors
- Try a different browser (Chrome recommended)
- Ensure no other application is using the camera

### Language Switching Issues

**Issue**: UI doesn't update or OCR language incorrect

**Solutions**:
- Ensure you save changes after switching language
- OCR models redownload for the new language (may take time)
- Check browser console for API errors
- Clear browser cache and reload

### Manual Correction Modal Not Saving

**Issue**: Corrections are lost or not applied

**Solutions**:
- Click "✓ Save Corrections" (not just close)
- Verify JSON is valid before saving
- Check if browser console shows validation errors

## 🛠️ Development

### Adding New Field Types

To add support for new document fields:

1. Edit `language_support.py` and update the `REGEX_PATTERNS` dictionary
2. Add patterns for both English and Arabic (if applicable)
3. Update `TRANSLATIONS` dictionary with field display names
4. Restart the server to load new patterns

### Extending Form Auto-Fill

To add support for new form types:

1. Edit `job_form_filler.py` to add new form handlers
2. Update field matching logic in `language_support.py` `JOB_FIELD_ALIASES`
3. Add form-specific field aliases and validation rules
4. Test with sample forms

### Customizing Verification

To customize verification logic:

1. Edit `ocr_verifier.py` to modify verification algorithms
2. Adjust confidence thresholds in the verification functions
3. Add custom validation rules for specific field types
4. Update scoring weights as needed

### Adding New OCR Methods

To integrate additional OCR providers:

1. Create a new module (e.g., `new_ocr_provider.py`)
2. Implement a standardized interface similar to `tesseract_ocr.py`
3. Update `ocr_comparison.py` to include the new method
4. Add UI option in `index.html` for method selection

## 📝 Dependencies

### Core Dependencies

- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: Lightning-fast ASGI server
- **OpenCV (cv2)**: Image processing and computer vision
- **EasyOCR**: Multi-language text recognition
- **Ultralytics YOLOv8**: Object detection for structured fields
- **Pillow (PIL)**: Image manipulation and format conversion
- **NumPy**: Numerical operations and array processing
- **PyMuPDF (fitz)**: PDF processing and page extraction

### Optional Dependencies

- **PaddleOCR**: Offline OCR engine (highly recommended)
- **pdf2image**: Alternative PDF processing
- **Requests**: HTTP library for API calls

### AI Dependencies (Optional)


- **Selenium**: Browser automation for form filling
- **Sentence Transformers**: Embeddings for semantic search
- **FAISS**: Vector storage for similarity search

## 🚀 Performance Tips

1. **Use Combined OCR Method**: Let the system auto-select the best OCR result
2. **Image Quality**: Ensure high-quality scans (good lighting, no blur)
3. **Camera Capture**: Use built-in camera for controlled, high-quality captures
4. **Manual Correction**: Review and correct OCR results for critical data
5. **Cache Models**: First run downloads models; subsequent runs are faster
6. **PDF Processing**: Multi-page PDFs take longer; process single pages if possible
7. **Language Settings**: Set the correct language before processing for better results

## 🆔 MOSIP Integration

The system includes a complete integration layer for the MOSIP ID Lifecycle ecosystem, supporting Pre-Registration, Registration Client, and Android RC.

### Key Features
- **Packet Management**: Create and manage MOSIP-compliant registration packets locally
- **Pre-Registration API**: Direct upload to MOSIP Pre-Registration server
- **Quality Scores**: Include image quality assessment (blur, lighting) in packets
- **Schema Mapping**: Automatic mapping of OCR fields to MOSIP ID Schema (v1.2.0+)
- **Mock Mode**: Built-in mock server for testing without live MOSIP credentials

### Usage
1. **Create Packet**: After OCR extraction, click "Create MOSIP Packet" in the UI
2. **View Packets**: Manage created packets in the "MOSIP Packets" tab
3. **Upload**: Click "Upload to MOSIP" to send data to the Pre-Registration server
4. **Configuration**: Set `MOSIP_ENABLED = True` in `config.py` to switch from mock to real mode

### Project Structure
- `mosip_client.py`: Handles communication with MOSIP APIs
- `mosip_field_mapper.py`: Maps OCR fields to MOSIP schema
- `packet_handler.py`: Manages local packet storage and metadata
- `mock_packets/`: Directory for locally created packets

## 📄 License

This project is provided as-is for educational and development purposes.

## 🙏 Acknowledgments

- **YOLOv8** from Ultralytics for object detection
- **EasyOCR** by JaidedAI for multi-language text recognition
- **PaddleOCR** by PaddlePaddle for offline OCR capabilities
- **FastAPI** for the modern, high-performance web framework
- **PyMuPDF** for efficient PDF processing
- **OpenCV** community for computer vision tools

## 📞 Support

For issues, questions, or contributions:

1. Check the **Troubleshooting** section above
2. Review the **API documentation** for endpoint details
3. Verify all dependencies are installed correctly
4. Check image quality using the built-in quality assessment
5. Use the Manual OCR Correction feature for data accuracy
6. Enable debug mode in `app.py` for detailed error logs

---

**Built with ❤️ for efficient multilingual document processing, intelligent form automation, and data accuracy**
