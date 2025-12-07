# OCR Text Extraction & Verification System

**A production-ready OCR system with multi-lingual support, handwritten text recognition, real-time confidence scoring, and MOSIP integration.**

## 🎯 Overview

Enterprise-grade document processing solution featuring:
- ✅ **100% Requirements Coverage** - All 20 mandatory, good-to-have, and bonus features
- 🌐 **Multi-lingual** - English, Arabic (RTL), Hindi (Devanagari)
- ✍️ **Handwritten Text** - TrOCR transformer-based recognition
- 🆔 **MOSIP Integration** - Pre-Registration API with full packet management
- 📊 **Quality Detection** - Real-time image quality analysis
- 💯 **Confidence Scoring** - Field-level accuracy metrics

---

## ⚡ Quick Start

### Prerequisites

- Python 3.10 or higher
- 4GB RAM minimum (8GB recommended for TrOCR)
- Modern web browser

### Installation

```bash
# Clone repository
git clone <repository-url>
cd extractor

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
python run_server.py
```

**Access the application:** http://localhost:8001

---

## ✨ Key Features

### 🌍 Multi-Lingual Support (100% Complete)
- **English** - Full UI + OCR
- **Arabic (العربية)** - RTL support + OCR  
- **Hindi (हिन्दी)** - Devanagari script + OCR
- Dynamic language switching without reload
- Localized field patterns and translations

### 📝 Advanced OCR Extraction
- **PaddleOCR** - Offline, high-accuracy printed text
- **TrOCR** - Microsoft's transformer-based handwritten text recognition
- **EasyOCR** - Multi-language fallback
- **Automatic best-method selection** with comparison scoring
- **Multi-page PDF support**
- **Field-specific confidence scores** (0-100%)

### 🎯 TrOCR Confidence Scoring
- **Real-time confidence badges** for each extracted field
- **Color-coded indicators**: 🟢 High (≥85%) | 🟡 Medium (60-84%) | 🔴 Low (<60%)
- **Works with both printed and handwritten text**
- **Displayed in UI and included in MOSIP packets**

### 📸 Image Quality Detection
- **Blur detection** (Laplacian variance)
- **Brightness analysis** (histogram-based)
- **Contrast measurement**
- **Noise estimation**
- **Resolution check**
- **Overall quality score** (0-100) with actionable feedback

### ✍️ Manual Correction Interface
- **Interactive review modal** after OCR extraction
- **Edit field values** before saving
- **Add/remove fields dynamically**
- **Skip option** if OCR is acceptable
- **Preserved confidence scores** after manual edits

### 🏥 Data Verification API
- **Multi-layer validation** (format, content, cross-reference)
- **Field-by-field comparison** with match percentages
- **Confidence scoring** for each verified field
- **Automatic data cleaning** and normalization
- **Detailed verification reports**

### 🆔 MOSIP Integration (Full End-to-End)
- **Packet creation** with OCR data
- **Pre-Registration API** upload
- **Quality score inclusion** (blur, brightness)
- **Schema mapping** to MOSIP ID Schema v1.2.0+
- **Mock mode** for testing without credentials
- **Packet management UI** with JSON viewer

### 📄 Document Support
- **40+ Field types** (ID cards, Passports, Licenses)
- **Multi-page PDFs** (automatic page extraction)
- **Image formats**: JPG, PNG, JPEG
- **Camera capture** (real-time scanning)

---

## 🚀 Usage Guide

### 1. Extract Text

**Upload File:**
1. Open http://localhost:8001
2. Go to "Extract Text" tab
3. Drag & drop or select file (JPG, PNG, PDF)
4. Check options:
   - ☑ **PaddleOCR (Offline)** - for printed text
   - ☑ **Handwritten Document (TrOCR)** - for handwritten text
5. Click **"Process Docs"**
6. Review quality report
7. Correct OCR errors in popup modal (optional)
8. Save or skip corrections

**Use Camera:**
1. Click **"📷 Use Camera"**
2. Allow camera permissions
3. Position document in frame
4. Click **"Capture"**
5. Click **"Use Image"** to process

### 2. Verify Data

1. Go to "Verify Data" tab
2. Paste extracted JSON
3. (Optional) Paste reference data
4. Click **"🔍 Verify & Validate Data"**
5. Review:
   - Overall verification status
   - Field-by-field match percentages
   - Cleaned & normalized data

### 3. Send to MOSIP

1. Extract text from ID document
2. Review extracted fields
3. Click **"Send to MOSIP"**
4. View packet in "MOSIP Packets" tab
5. Click **"Upload to MOSIP"** to send to Pre-Registration

### 4. Change Language

Use the dropdown in the header:
- **English**
- **العربية** (Arabic)
- **हिन्दी** (Hindi)

---

## 🔌 API Endpoints

### POST `/api/upload`
Upload and process document with OCR.

**Request:**
```bash
curl -X POST http://localhost:8001/api/upload \
  -F "file=@document.jpg" \
  -F "use_openai=true" \
  -F "use_trocr=false"
```

**Response:**
```json
{
  "success": true,
  "extracted_fields": {
    "Name": "John Smith",
    "Date of Birth": "01/01/1990"
  },
  "trocr_confidence": {
    "Name": 0.976,
    "Date of Birth": 0.883
  },
  "quality": {
    "overall": 95.2,
    "blur": 3.5,
    "brightness": 89.1
  },
  "method": "paddle_trocr_combined"
}
```

### POST `/api/verify`
Verify extracted data.

**Request:**
```bash
curl -X POST http://localhost:8001/api/verify \
  -F "extracted_data={\"Name\": \"John\"}" \
  -F "original_data={\"Name\": \"John\"}"
```

**Response:**
```json
{
  "overall_verification_status": "PASS",
  "verification_report": [
    {
      "field": "Name",
      "status": "PASS",
      "confidence": 100,
      "match_percentage": 100
    }
  ]
}
```

### POST `/api/mosip/send`
Create MOSIP packet.

**Request:**
```json
{
  "extracted_fields": {"Name": "John"},
  "extracted_metadata": {
    "trocr_confidence": {"Name": 0.95}
  }
}
```

**Response:**
```json
{
  "success": true,
  "packet_id": "PKT_20241130_001",
  "message": "Packet created successfully"
}
```

### GET `/api/mosip/packets`
List all MOSIP packets.

### POST `/api/set-language`
Change language dynamically.

**Request:** `language=hi` (or `en`, `ar`)

---

## 📁 Project Structure

```
extractor/
├── app.py                      # Main FastAPI backend
├── index.html                  # Frontend web interface
├── setup.py                    # Python packaging config
├── requirements.txt            # Dependencies
├── .python-version             # Python version (3.10)
├── config.py                   # Configuration
│
├── language_support.py         # Multi-lingual (EN/AR/HI)
├── ocr_verifier.py             # Data verification
├── quality_score.py            # Image quality detection
├── ocr_confidence.py           # Confidence visualization
│
├── paddle_ocr_module.py        # PaddleOCR wrapper
├── trocr_handwritten.py        # TrOCR wrapper
│
├── mosip_client.py             # MOSIP API client
├── mosip_field_mapper.py       # Field → MOSIP schema
├── packet_handler.py           # Packet management
│
├── mock_packets/               # Local packet storage
├── static/                     # Static assets
└── tests/                      # Test files
```

---

## 🌐 Supported Fields

### Identity
- Name, Surname, Full Name
- Date of Birth, Place of Birth
- Nationality, Country
- Gender/Sex
- Personal No, National ID

### Document Info
- Passport Number
- Card Number, License Number
- PAN, Aadhaar, SSN
- Issue Date, Expiry Date
- Issuing Office/Authority

### Contact
- Phone, Mobile
- Email
- Address (Line 1, Line 2)
- City, State, Pin Code

### Physical
- Height, Weight
- Eye Color, Hair Color
- Blood Group

### Family
- Father Name, Mother Name
- Spouse Name
- Marital Status, Religion, Occupation

---

## 🛠️ Configuration

### Language Selection

Edit `config.py`:
```python
SELECTED_LANGUAGE = "en"  # or "ar", "hi"
```

Or switch via UI dropdown (top-right header).

### MOSIP Integration

Edit `config.py`:
```python
MOSIP_ENABLED = True  # Set to False for mock mode
MOSIP_BASE_URL = "https://collab.mosip.net"
MOSIP_CLIENT_ID = "mosip-prereg-client"
MOSIP_CLIENT_SECRET = "mosip"
```


---

## 📦 Dependencies

### Core (Python 3.10+)
- **FastAPI** - Modern API framework
- **Uvicorn** - ASGI server
- **OpenCV** - Image processing
- **Pillow** - Image manipulation
- **NumPy** - Numerical operations
- **PyMuPDF** - PDF processing

### OCR Engines
- **PaddlePaddle + PaddleOCR** - Offline printed text
- **Transformers + PyTorch** - TrOCR handwritten text
- **aiofiles** - Async file operations

### Python Version Support
- ✅ Python 3.10.x (tested)
- ✅ Python 3.11.x (compatible)
- ✅ Python 3.12.x (compatible)
- ✅ Python 3.13.x (compatible)

---

## 🐛 Troubleshooting

### Server Won't Start

**Issue:** Port 8001 already in use

**Solution:**
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8001 | xargs kill -9
```

### Poor OCR Accuracy

**Solutions:**
1. Check image quality score (should be >85)
2. Use **Manual Correction** modal to fix errors
3. Enable **TrOCR** for handwritten documents
4. Try both PaddleOCR + TrOCR for best results
5. Use camera capture for controlled quality

### TrOCR Not Working

**Solutions:**
1. Ensure PyTorch is installed: `pip install torch==2.6.0`
2. Check internet on first run (downloads model ~1GB)
3. Verify checkbox **"Handwritten Document (TrOCR)"** is checked

### Confidence Scores Missing

**Solutions:**
1. Restart server after code changes
2. Check terminal for debug logs
3. Verify TrOCR is enabled for handwritten text
4. For printed text, enable PaddleOCR checkbox

---

## ✅ Requirements Compliance

| Category | Status | Count |
|----------|--------|-------|
| **Mandatory** | ✅ Complete | 2/2 |
| **Good-to-Have** | ✅ Complete | 6/6 |
| **Bonus** | ✅ Complete | 12/12 |
| **TOTAL** | ✅ **100%** | **20/20** |

### Mandatory ✅
1. ✅ API 1: OCR Extraction (English support)
2. ✅ API 2: Data Verification (format + confidence)

### Good-to-Have ✅
1. ✅ Multi-lingual: Arabic + Hindi (non-Latin)
2. ✅ Interface/Demo Form
3. ✅ Handwritten Text (TrOCR)
4. ✅ Partial Data Mapping
5. ✅ Manual Correction
6. ✅ Multi-lingual UI

### Bonus ✅
1. ✅ MOSIP Integration (Pre-Reg + Client)
2. ✅ Capture Quality Score (blur, brightness)
3. ✅ Quality-Based Retake Prompt
4. ✅ Multi-Page Documents
5. ✅ Real-Time Confidence Feedback
6. ✅ Confidence Zone Display
7. ✅ End-to-End MOSIP Flow
8. ✅ Enhanced UX Features

---

## 🚀 Performance Tips

1. **Enable both OCR methods** for automatic best-result selection
2. **Use TrOCR** specifically for handwritten documents
3. **Check quality scores** before processing (>85 recommended)
4. **Use camera capture** for controlled, high-quality scans
5. **Manual correction** for critical data accuracy
6. **Process single PDF pages** when possible (faster)

---

## 📄 License

This project is provided as-is for educational and development purposes.

---

## 🙏 Acknowledgments

- **Microsoft TrOCR** - Transformer-based handwritten OCR
- **PaddlePaddle** - High-accuracy offline OCR
- **FastAPI** - Modern Python web framework
- **PyTorch** - Deep learning framework
- **MOSIP** - Open-source identity platform

---

## 📞 Support

**For issues:**
1. Check **Troubleshooting** section
2. Review terminal logs for errors
3. Test image quality with quality assessment
4. Use manual correction for OCR errors
5. Verify Python version: `python --version` (≥3.10)

---

**Built with ❤️ for multilingual document processing, handwritten text recognition, and MOSIP identity integration**

**Version:** 1.0.0 | **Python:** 3.10+ | **Status:** Production Ready 🚀
