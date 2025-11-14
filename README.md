# OCR Text Extraction & Verification System

A comprehensive web application for extracting text from scanned documents (ID cards, forms), intelligently auto-filling digital forms, and accurately verifying extracted data against original sources for enhanced reliability and efficiency.

## 🎯 Project Overview

This system provides an end-to-end OCR solution that:

- **Extracts text** from scanned documents (ID cards, forms, PDFs) using advanced OCR technology
- **Auto-fills digital forms** by intelligently matching extracted data to form fields
- **Verifies extracted data** against original sources to ensure accuracy and reliability

## ✨ Key Features

### 1. **Document OCR & Text Extraction**

- Extract text from scanned documents using **YOLOv8** object detection and **EasyOCR**
- Support for **Google Vision API** for enhanced accuracy
- Process both **images** (JPG, PNG) and **PDF documents**
- Automatic field detection for ID cards (Name, Date of Birth, Passport No, etc.)
- Structured JSON output for easy integration

### 2. **Intelligent Form Auto-Fill**

- Automatically match extracted data to form fields
- Confidence scoring for field matches
- Support for Google Forms integration
- Smart field name matching with alias support
- Batch form filling capabilities

### 3. **Data Verification**

- Compare extracted data with original/reference sources
- Field-by-field verification with confidence scores
- Data cleaning and normalization
- Verification reports with detailed match analysis
- Overall confidence metrics

### 4. **Modern Web Interface**

- Beautiful, responsive UI with drag-and-drop file upload
- Real-time processing feedback
- Interactive data visualization
- Export results in JSON format
- Mobile-friendly design

## 🚀 Quick Start

### Prerequisites

- **Python 3.8 or higher**
- **Pre-trained YOLOv8 model** (`Mymodel.pt`) - Place in the root directory
- **Google Vision API Key** (optional, for enhanced OCR accuracy)
- Web browser (Chrome, Firefox, Edge, etc.)

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
   pip install -r requirements_web.txt
   ```

4. **Configure API Keys** (optional):

   - Edit `config.py` and add your Google Vision API key:
     ```python
     GOOGLE_VISION_API_KEY = "your-api-key-here"
     ```

5. **Ensure the model file is present**:
   - Download `Mymodel.pt` and place it in the root directory
   - The model file is required for YOLO-based OCR processing

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

1. Open the web interface at `http://localhost:8000`
2. Navigate to the **"Extract Text"** tab
3. Upload an image or PDF file:
   - Drag and drop the file, or
   - Click to browse and select
4. (Optional) Check **"Use Google Vision API"** for enhanced accuracy
5. Click **"Process Image"** or **"Process PDF"**
6. View extracted fields and general text in JSON format

### 2. Verify Extracted Data

1. Navigate to the **"Verify Data"** tab
2. Paste your extracted data (JSON format) in the first text area
3. Paste the original/reference data (JSON format) in the second text area
4. (Optional) Add OCR text block for additional context
5. Click **"Verify Data"**
6. Review the verification report with confidence scores

### 3. Auto-Fill Forms

1. Navigate to the **"Auto-Fill Form"** tab
2. Enter form field names (one per line or JSON array)
3. Paste extracted data (JSON format)
4. Click **"Match Fields"**
5. Review matched fields with confidence scores
6. Use the matched data to fill your forms

## 🔌 API Endpoints

### POST `/api/upload`

Upload and process an image or PDF for OCR extraction.

**Request:**

- `file`: Image or PDF file (multipart/form-data)
- `use_openai`: "true" to use Google Vision API (optional)

**Response:**

```json
{
  "success": true,
  "filename": "document.pdf",
  "extracted_fields": {
    "Name": "John Doe",
    "Date of Birth": "01/01/1990",
    "Passport No": "AB123456",
    ...
  },
  "general_text": ["Additional text lines..."],
  "found_idcard": true,
  "file_type": "pdf",
  "method": "google_vision",
  "total_pages": 1
}
```

### POST `/api/verify`

Verify extracted data against original source.

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
    ...
  },
  "verification_report": {
    "Name": {
      "extracted": "John Doe",
      "original": "John Doe",
      "match": true,
      "confidence": 100.0
    },
    ...
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

Match extracted data to form fields.

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
      "confidence": 85.5
    },
    ...
  },
  "fields_matched": 3
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
├── config.py                       # Configuration file (API keys)
├── ocr_verifier.py                 # Data verification module
├── job_form_filler.py              # Form auto-fill module
├── run_server.py                   # Server startup script
├── requirements_web.txt            # Web app dependencies
├── requirements.txt                # Full dependencies (optional)
├── Mymodel.pt                      # YOLOv8 pre-trained model (required)
├── README.md                       # This file
└── Auto-Job-Form-Filler-Agent/    # Form filling agent module
    ├── google_form_handler.py
    ├── rag_workflow_with_human_feedback.py
    ├── resume_processor.py
    └── assets/
```

## 🎯 Supported Document Fields

The system can extract the following ID card and document fields:

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

- Height
- Type
- Any custom fields detected in documents

## 🔧 Configuration

### API Keys

Edit `config.py` to configure API keys:

```python
# Google Vision API Key for document parsing and OCR
GOOGLE_VISION_API_KEY = "your-google-vision-api-key"

# OpenRouter API Key for AI models (optional)
OPENROUTER_API_KEY = "your-openrouter-api-key"

# Llama Cloud API Key for resume parsing (optional)
LLAMA_CLOUD_API_KEY = "your-llama-cloud-api-key"
```

### Model Configuration

- Place `Mymodel.pt` in the root directory
- The model is automatically loaded on server startup
- If the model is not found, the server will still start but YOLO-based OCR will be unavailable

## 🐛 Troubleshooting

### Model Not Found Error

- Ensure `Mymodel.pt` is in the root directory
- Check the file name matches exactly (case-sensitive)
- Verify file permissions

### OCR Not Working

- Ensure EasyOCR models are downloaded (first run will download automatically)
- Check internet connection for initial model download
- Verify image quality (high resolution, clear text)

### Server Won't Start

- Check if port 8000 is available
- Verify all dependencies are installed: `pip install -r requirements_web.txt`
- Check Python version (3.8 or higher required)

### Poor Extraction Accuracy

- Ensure image quality is good (high resolution, clear text)
- Try using Google Vision API for better accuracy
- Check if document type matches training data
- Preprocess images (adjust brightness/contrast) if needed

### Google Vision API Errors

- Verify API key is correct in `config.py`
- Check API quota and billing status
- Ensure API is enabled in Google Cloud Console

## 🛠️ Development

### Adding New Field Types

To add support for new document fields:

1. Edit `app.py` and update the `class_map` dictionary
2. Add field patterns to `parse_text_to_json_advanced()` function
3. Update field equivalents in `field_equivalents` dictionary

### Extending Form Auto-Fill

To add support for new form types:

1. Edit `job_form_filler.py` to add new form handlers
2. Update field matching logic in `app.py` `/api/autofill` endpoint
3. Add form-specific field aliases

### Customizing Verification

To customize verification logic:

1. Edit `ocr_verifier.py` to modify verification algorithms
2. Adjust confidence thresholds
3. Add custom validation rules

## 📝 Dependencies

### Core Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **OpenCV**: Image processing
- **EasyOCR**: Text recognition
- **Ultralytics YOLOv8**: Object detection
- **Pillow**: Image manipulation
- **NumPy**: Numerical operations

### Optional Dependencies

- **Google Vision API**: Enhanced OCR accuracy
- **PyMuPDF / pdf2image**: PDF processing
- **Selenium**: Form automation
- **Llama Index**: AI-powered form filling

## 📄 License

This project is provided as-is for educational and development purposes.

## 🙏 Acknowledgments

- **YOLOv8** from Ultralytics for object detection
- **EasyOCR** for text recognition
- **FastAPI** for the backend framework
- **Google Vision API** for enhanced OCR capabilities

## 📞 Support

For issues, questions, or contributions:

1. Check the troubleshooting section above
2. Review the API documentation
3. Verify all dependencies are installed correctly

---

**Built with ❤️ for efficient document processing and form automation**
