# MOSIP Pre-Registration OCR System

<div align="center">

![MOSIP](https://img.shields.io/badge/MOSIP-Integrated-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python)
![Angular](https://img.shields.io/badge/Angular-8-red?style=for-the-badge&logo=angular)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=for-the-badge&logo=fastapi)

**A complete document processing and identity pre-registration system combining OCR extraction, MOSIP Pre-Registration UI, and backend mock services.**

</div>

---

## 🎯 Overview

This project provides a **complete MOSIP Pre-Registration solution** with:

| Component | Description |
|-----------|-------------|
| **OCR Extraction** | Multi-lingual document processing with PaddleOCR & TrOCR |
| **MOSIP Pre-Reg UI** | Full Angular-based Pre-Registration portal (forked from MOSIP) |
| **Mock Backend** | Complete FastAPI backend simulating all MOSIP APIs |
| **Data Verification** | Field validation and confidence scoring |

---

## ⚡ Quick Start

### Prerequisites

- **Python 3.10+** (required)
- **Node.js 14+** (for Angular UI)
- **4GB RAM** minimum (8GB recommended for TrOCR)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd extractor

# Create Python virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Angular dependencies
cd mosip-prereg
npm install
cd ..
```

### Running the System

**Terminal 1 - Python Backend (Port 8001):**
```bash
python run_server.py
```

**Terminal 2 - Angular Frontend (Port 4200):**
```bash
cd mosip-prereg
npm start
```

### Access Points

| Application | URL |
|------------|-----|
| **OCR Extraction UI** | http://localhost:8001 |
| **MOSIP Pre-Registration** | http://localhost:4200 |
| **API Documentation** | http://localhost:8001/docs |

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                        │
├─────────────────────────────┬──────────────────────────────────────┤
│    OCR Extraction UI        │      MOSIP Pre-Registration UI       │
│    (index.html:8001)        │      (Angular:4200)                  │
├─────────────────────────────┴──────────────────────────────────────┤
│                         FastAPI Backend                            │
│                         (app.py:8001)                              │
├────────────────────────────────────────────────────────────────────┤
│  OCR Services  │  MOSIP Mock APIs  │  Data Verification  │ Packets │
│  - PaddleOCR   │  - Login/Auth     │  - Field Validation │ - Create│
│  - TrOCR       │  - Applications   │  - Confidence Score │ - Store │
│  - EasyOCR     │  - Booking        │  - Data Cleaning    │ - Upload│
│                │  - Documents      │                     │         │
└────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 📄 OCR Document Processing

| Feature | Description |
|---------|-------------|
| **PaddleOCR** | High-accuracy offline printed text recognition |
| **TrOCR** | Microsoft's transformer for handwritten text |
| **EasyOCR** | Multi-language fallback engine |
| **Multi-page PDF** | Automatic page extraction |
| **Camera Capture** | Real-time document scanning |

### 🌐 Multi-Language Support

| Language | Direction | Script |
|----------|-----------|--------|
| English | LTR | Latin |
| Arabic (العربية) | RTL | Arabic |
| Hindi (हिन्दी) | LTR | Devanagari |

### 🆔 MOSIP Pre-Registration

The system includes a **complete MOSIP Pre-Registration portal** with:

- **OTP-based Login** (mock mode - any OTP works)
- **Demographic Data Entry** with UI specification support
- **Document Upload** (POI, POA categories)
- **Appointment Booking** with calendar selection
- **Application Management** (create, edit, delete, cancel)
- **Multi-language UI** (English, Arabic, French)

### 📊 Data Quality & Verification

| Feature | Description |
|---------|-------------|
| **Image Quality Score** | Blur, brightness, contrast analysis |
| **Field Confidence** | Per-field accuracy (0-100%) |
| **Data Verification** | Multi-layer validation |
| **Manual Correction** | Edit extracted fields |

---

## 📁 Project Structure

```
extractor/
├── app.py                      # Main FastAPI backend + MOSIP mock APIs
├── run_server.py               # Server startup script
├── index.html                  # OCR Extraction web interface
├── requirements.txt            # Python dependencies
├── config.py                   # Configuration settings
│
├── mosip-prereg/               # Angular MOSIP Pre-Registration UI
│   ├── src/app/                # Angular components
│   ├── src/assets/i18n/        # Translations (eng, ara, fra, hin, kan)
│   └── package.json            # Node dependencies
│
├── language_support.py         # Multi-lingual OCR patterns
├── ocr_verifier.py             # Data verification logic
├── quality_score.py            # Image quality detection
├── ocr_confidence.py           # Confidence visualization
│
├── paddle_ocr_module.py        # PaddleOCR wrapper
├── trocr_handwritten.py        # TrOCR handwritten recognition
│
├── mosip_client.py             # MOSIP API client
├── mosip_field_mapper.py       # Field → MOSIP schema mapping
├── packet_handler.py           # Packet management
│
├── mock_packets/               # Local packet storage
├── static/                     # CSS/JS assets
├── tests/                      # Test files
└── Deliverables/               # Documentation & presentations
```

---

## 🔌 API Endpoints

### OCR Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload document for OCR |
| POST | `/api/verify` | Verify extracted data |
| GET | `/api/config` | Get language translations |
| POST | `/api/set-language` | Change UI language |

### MOSIP Mock Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/preregistration/v1/login/sendOtp` | Send OTP (mock) |
| POST | `/preregistration/v1/login/validateOtp` | Validate OTP (auto-approve) |
| POST | `/preregistration/v1/login/invalidateToken` | Logout |
| GET | `/preregistration/v1/applications/prereg` | List applications |
| POST | `/preregistration/v1/applications` | Create application |
| PUT | `/preregistration/v1/applications/prereg/{prid}` | Update application |
| DELETE | `/preregistration/v1/applications/prereg/{prid}` | Delete application |
| GET | `/preregistration/v1/uispec/latest` | Get UI specification |
| POST | `/preregistration/v1/applications/appointment` | Book appointment |
| PUT | `/preregistration/v1/applications/appointment/{prid}` | Cancel appointment |

### Packet Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/mosip/send` | Create MOSIP packet from OCR |
| GET | `/api/mosip/packets` | List all packets |
| GET | `/api/mosip/packet/{id}` | Get packet details |
| POST | `/api/mosip/upload/{id}` | Upload to MOSIP server |

---

## 🎮 Usage Guide

### 1. OCR Extraction (localhost:8001)

1. Open http://localhost:8001
2. Go to **"Extract Text"** tab
3. Upload document (JPG, PNG, PDF) or use camera
4. Select OCR options:
   - ☑ **PaddleOCR** for printed text
   - ☑ **TrOCR** for handwritten text
5. Click **"Process Docs"**
6. Review quality score and extracted fields
7. Make corrections if needed
8. Click **"Send to MOSIP"** to create packet

### 2. MOSIP Pre-Registration (localhost:4200)

1. Open http://localhost:4200
2. Enter phone/email and click **"Get OTP"**
3. Enter any 6 digits (mock accepts all)
4. Complete workflow:
   - **Demographic Details** → Fill form
   - **Document Upload** → Upload POI/POA
   - **Book Appointment** → Select center & time
   - **Preview & Submit** → Confirm details
5. Manage applications from dashboard:
   - Edit, delete, or cancel appointments

### 3. Verify & Clean Data

1. Go to **"Verify Data"** tab
2. Paste extracted JSON
3. Optionally add reference data
4. Click **"Verify & Validate"**
5. Review field-by-field validation

---

## ⚙️ Configuration

### config.py

```python
# Language
SELECTED_LANGUAGE = "en"  # en, ar, hi

# MOSIP Integration
MOSIP_ENABLED = False     # True for real MOSIP server
MOSIP_BASE_URL = "https://collab.mosip.net"
MOSIP_CLIENT_ID = "mosip-prereg-client"
MOSIP_CLIENT_SECRET = "your-secret"
```

### Angular Environment (mosip-prereg)

Edit `src/assets/configs/default.properties`:
```
mosip.preregistration.api.url=http://localhost:8001
```

---

## 🛠️ Troubleshooting

### Server Issues

**Port 8001 in use:**
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8001 | xargs kill -9
```

**Angular won't start:**
```bash
cd mosip-prereg
rm -rf node_modules package-lock.json
npm install
npm start
```

### OCR Issues

| Problem | Solution |
|---------|----------|
| Poor accuracy | Check image quality score (>85) |
| Missing handwritten text | Enable TrOCR checkbox |
| Slow processing | First run downloads models (~1GB) |

### MOSIP UI Issues

| Problem | Solution |
|---------|----------|
| Login fails | Restart Python backend |
| Delete not working | Server restart required after code changes |
| Cancel appointment disabled | Only works for "Booked" status applications |

---

## 📦 Dependencies

### Python (requirements.txt)

```
fastapi>=0.104.1
uvicorn>=0.24.0
paddlepaddle>=2.5.0
paddleocr>=2.7.0
opencv-python>=4.8.0
pillow>=10.0.0
torch>=2.1.0
transformers>=4.35.0
aiofiles>=23.2.0
python-multipart>=0.0.6
pymupdf>=1.23.0
```

### Angular (mosip-prereg)

- Angular 8
- Angular Material
- RxJS
- ngx-translate

---

## 🧪 Testing

```bash
# Run Python tests
python -m pytest tests/

# Run Angular tests
cd mosip-prereg
npm test
```

---

## 📊 Supported Document Fields

### Identity
- Full Name, First/Last Name
- Date of Birth, Place of Birth
- Nationality, Gender
- National ID, Personal Number

### Document
- Passport Number, Card Number
- Issue Date, Expiry Date
- Issuing Authority
- PAN, Aadhaar

### Contact
- Phone, Email
- Address Lines
- City, State, Pin Code

### Family
- Father Name, Mother Name
- Spouse Name
- Marital Status

---

## 📄 License

This project is provided for educational and development purposes.

---

## 🙏 Acknowledgments

- **MOSIP** - Open-source identity platform
- **Microsoft TrOCR** - Transformer OCR
- **PaddlePaddle** - High-accuracy OCR
- **FastAPI** - Modern Python framework
- **Angular** - Frontend framework

---

<div align="center">

**Version:** 2.0.0 | **Python:** 3.10+ | **Angular:** 8 | **Status:** Production Ready 🚀

Built with ❤️ for MOSIP Pre-Registration and document processing

</div>
