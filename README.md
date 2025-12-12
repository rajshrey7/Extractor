# MOSIP Pre-Registration OCR System

<div align="center">

![MOSIP](https://img.shields.io/badge/MOSIP-Integrated-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python)
![Angular](https://img.shields.io/badge/Angular-8-red?style=for-the-badge&logo=angular)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=for-the-badge&logo=fastapi)

**A complete document processing and identity pre-registration system combining OCR extraction, MOSIP Pre-Registration UI, and backend mock services.**

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)
- [Access Points](#-access-points)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Usage Guide](#-usage-guide)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Supported Fields](#-supported-fields)
- [Testing](#-testing)

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

## 💻 System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+) |
| **Python** | 3.10 or higher |
| **Node.js** | 14.x or higher (includes npm) |
| **RAM** | 4GB minimum (8GB recommended for TrOCR models) |
| **Storage** | 3GB free space (for OCR models) |

### Verify Prerequisites

```bash
# Check Python version (should be 3.10+)
python --version

# Check Node.js version (should be 14+)
node --version

# Check npm version
npm --version
```

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd extractor
```

### Step 2: Set Up Python Environment

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install Python dependencies
pip install -r requirements.txt
```

**Windows (Command Prompt):**
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat

# Install Python dependencies
pip install -r requirements.txt
```

**Linux/macOS:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Set Up Angular Frontend

```bash
# Navigate to Angular project
cd mosip-prereg

# Install Node dependencies
npm install

# Return to root directory
cd ..
```

> **Note:** First-time `npm install` may take 5-10 minutes. Ignore deprecation warnings.

---

## 🚀 Running the Application

The application requires **two servers running simultaneously**. Open **two separate terminal windows**.

### Terminal 1: Start Python Backend (Port 8001)

```bash
# Navigate to project root
cd extractor

# Activate virtual environment (if not already active)
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Start the backend server
python run_server.py
```

**Expected Output:**
```
====================
Starting OCR Server...
====================
✅ PaddleOCR initialized successfully
✅ Startup complete!
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

> **First Run:** The first startup will download OCR models (~1GB). This may take 5-10 minutes.

### Terminal 2: Start Angular Frontend (Port 4200)

```bash
# Navigate to Angular project
cd extractor/mosip-prereg

# Start Angular development server
npm start
```

**Expected Output:**
```
** Angular Live Development Server is listening on localhost:4200 **
: Compiled successfully.
```

> **Note:** Angular compilation takes 1-2 minutes. Wait for "Compiled successfully" before accessing the UI.

---

## 🌐 Access Points

Once both servers are running, access the application at:

| Application | URL | Description |
|------------|-----|-------------|
| **MOSIP Pre-Registration UI** | http://localhost:4200 | Main Pre-Registration portal |
| **OCR Extraction Tool** | http://localhost:8001 | Document OCR interface |
| **API Documentation** | http://localhost:8001/docs | Interactive Swagger UI |
| **API Docs (Alternative)** | http://localhost:8001/redoc | ReDoc API documentation |

### Quick Verification

1. Open http://localhost:4200 — You should see the MOSIP login page
2. Open http://localhost:8001 — You should see the OCR extraction interface
3. Open http://localhost:8001/docs — You should see the Swagger API docs

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                        │
├─────────────────────────────┬──────────────────────────────────────┤
│    OCR Extraction UI        │      MOSIP Pre-Registration UI       │
│    (localhost:8001)         │      (localhost:4200)                │
│    [index.html]             │      [Angular 8]                     │
├─────────────────────────────┴──────────────────────────────────────┤
│                         FastAPI Backend                            │
│                         (localhost:8001)                           │
├────────────────────────────────────────────────────────────────────┤
│  OCR Services       │  MOSIP Mock APIs    │  Data Processing       │
│  ├─ PaddleOCR       │  ├─ Login/Auth      │  ├─ Verification       │
│  ├─ TrOCR           │  ├─ Applications    │  ├─ Confidence Score   │
│  └─ EasyOCR         │  ├─ Booking         │  └─ Data Cleaning      │
│                     │  └─ Documents       │                        │
└────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 📄 OCR Document Processing

- **PaddleOCR** — High-accuracy offline printed text recognition
- **TrOCR** — Microsoft's transformer for handwritten text
- **Multi-page PDF** — Automatic page extraction
- **Camera Capture** — Real-time document scanning
- **Quality Analysis** — Blur, brightness, contrast detection

### 🌐 Multi-Language Support

| Language | Direction | Auto-Detection |
|----------|-----------|----------------|
| English | LTR | ✅ |
| Arabic (العربية) | RTL | ✅ |
| Hindi (हिन्दी) | LTR | ✅ |

### 🆔 MOSIP Pre-Registration

- **OTP-based Login** — Mock mode accepts any 6-digit OTP
- **Demographic Data Entry** — Dynamic form with UI specification
- **Document Upload** — POI, POA categories
- **Appointment Booking** — Calendar-based center selection
- **Application Management** — Create, edit, delete, cancel

### 📊 Data Quality & Verification

- **Image Quality Score** — 0-100% rating
- **Field Confidence** — Per-field accuracy metrics
- **Data Validation** — Format and pattern checking
- **Manual Correction** — Inline field editing

---

## 🎮 Usage Guide

### 1. MOSIP Pre-Registration (localhost:4200)

1. Open http://localhost:4200
2. Enter phone number or email (e.g., `test@example.com`)
3. Click **"Send OTP"**
4. Enter any 6 digits (e.g., `123456`) — mock accepts all
5. Complete the workflow:
   - **Demographic Details** → Fill personal information
   - **Document Upload** → Upload ID proofs (optional in mock mode)
   - **Book Appointment** → Select center and time slot
   - **Preview & Submit** → Review and confirm

### 2. OCR Extraction (localhost:8001)

1. Open http://localhost:8001
2. Go to **"Extract Text"** tab
3. Upload document (JPG, PNG, PDF) or use camera
4. Configure OCR options:
   - ☑ **Use PaddleOCR** — Best for printed text
   - ☑ **Include Handwriting (TrOCR)** — For handwritten content
5. Click **"Process Docs"**
6. Review extracted fields and confidence scores
7. Make corrections if needed
8. Click **"Send to MOSIP"** to create registration packet

### 3. OCR to Pre-Registration Integration

The OCR tool can automatically fill the Pre-Registration form:

1. Extract data from document using OCR (localhost:8001)
2. In the Pre-Registration form (localhost:4200), OCR data is auto-filled
3. Fields like Name, DOB, Address are mapped automatically
4. Review and submit the application

---

## 🔌 API Reference

### OCR Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload document for OCR processing |
| `POST` | `/api/verify` | Verify and validate extracted data |
| `GET` | `/api/config` | Get language translations |
| `POST` | `/api/set-language` | Change UI language |

### MOSIP Mock Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/preregistration/v1/login/sendOtp` | Send OTP (mock) |
| `POST` | `/preregistration/v1/login/validateOtp` | Validate OTP (auto-approve) |
| `POST` | `/preregistration/v1/login/invalidateToken` | Logout |
| `GET` | `/preregistration/v1/applications/prereg` | List applications |
| `POST` | `/preregistration/v1/applications` | Create application |
| `PUT` | `/preregistration/v1/applications/prereg/{prid}` | Update application |
| `DELETE` | `/preregistration/v1/applications/prereg/{prid}` | Delete application |
| `GET` | `/preregistration/v1/uispec/latest` | Get UI specification |

### Packet Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/mosip/send` | Create MOSIP packet from OCR data |
| `GET` | `/api/mosip/packets` | List all created packets |
| `GET` | `/api/mosip/packet/{id}` | Get packet details |

Full API documentation available at http://localhost:8001/docs

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
│   │   ├── feature/            # Feature modules (demographic, booking, etc.)
│   │   └── core/services/      # API services
│   ├── src/assets/             # Static assets and translations
│   └── package.json            # Node dependencies
│
├── language_support.py         # Multi-lingual OCR patterns
├── ocr_verifier.py             # Data verification logic
├── quality_score.py            # Image quality detection
├── data_cleaner.py             # OCR data cleaning
│
├── paddle_ocr_module.py        # PaddleOCR wrapper
├── trocr_handwritten.py        # TrOCR handwritten recognition
│
├── mosip_client.py             # MOSIP API client
├── mosip_field_mapper.py       # Field → MOSIP schema mapping
├── packet_handler.py           # Packet management
│
├── mock_packets/               # Local packet storage
├── uploads/                    # Uploaded images
└── Deliverables/               # Documentation & presentations
```

---

## ⚙️ Configuration

### Python Backend (config.py)

```python
# Language Settings
SELECTED_LANGUAGE = "en"  # Options: en, ar, hi

# MOSIP Integration (Mock Mode)
MOSIP_ENABLED = False     # Set True to connect to real MOSIP server
MOSIP_BASE_URL = "https://collab.mosip.net"
MOSIP_CLIENT_ID = "mosip-prereg-client"
MOSIP_CLIENT_SECRET = "your-secret"
```

### Angular Frontend

Edit `mosip-prereg/src/assets/configs/default.properties`:
```properties
mosip.preregistration.api.url=http://localhost:8001
```

---

## 🛠️ Troubleshooting

### Server Won't Start

**Problem:** Port 8001 already in use
```powershell
# Windows - Find and kill process
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8001 | xargs kill -9
```

**Problem:** Python module not found
```bash
# Ensure virtual environment is activated
# Windows:
.\venv\Scripts\Activate.ps1
# Then reinstall:
pip install -r requirements.txt
```

### Angular Issues

**Problem:** `npm start` fails
```bash
cd mosip-prereg
rm -rf node_modules package-lock.json
npm install
npm start
```

**Problem:** Blank page at localhost:4200
- Wait for compilation to complete (check terminal for "Compiled successfully")
- Try hard refresh: Ctrl+Shift+R

### OCR Issues

| Problem | Solution |
|---------|----------|
| Poor accuracy | Check image quality (aim for score > 85%) |
| Missing handwritten text | Enable TrOCR checkbox |
| Slow first run | Normal — models downloading (~1GB) |
| CUDA errors | Ignore — CPU mode is used automatically |

### MOSIP UI Issues

| Problem | Solution |
|---------|----------|
| Login fails | Restart Python backend server |
| Form fields missing | Check browser console for errors |
| Cancel disabled | Only works for "Booked" status |

---

## 📊 Supported Document Fields

### Identity Information
- Full Name, First Name, Last Name
- Date of Birth, Place of Birth
- Father's Name, Mother's Name
- Gender, Nationality

### Document Details
- Passport Number, Card Number
- Aadhaar, PAN, Voter ID
- Issue Date, Expiry Date
- Issuing Authority

### Contact Information
- Phone, Mobile
- Email
- Address Line 1, Line 2
- City, State, District
- Postal Code / PIN Code

---

## 🧪 Testing

### Test Python Backend

```bash
# Activate virtual environment first
python -m pytest tests/ -v
```

### Test Angular Frontend

```bash
cd mosip-prereg
npm test
```

### Manual API Testing

```bash
# Test if backend is running
curl http://localhost:8001/

# Test UI spec endpoint
curl http://localhost:8001/preregistration/v1/uispec/latest
```

---

## 🔄 Quick Commands Reference

```bash
# Start Backend (Terminal 1)
cd extractor
.\venv\Scripts\Activate.ps1  # Windows
python run_server.py

# Start Frontend (Terminal 2)
cd extractor/mosip-prereg
npm start

# Stop Servers
# Press Ctrl+C in each terminal

# Restart Backend Only
# In backend terminal: Ctrl+C, then:
python run_server.py

# Full Reset (if issues occur)
# Terminal 1:
Get-Process -Name python | Stop-Process -Force
python run_server.py

# Terminal 2:
cd mosip-prereg
npm start
```

---

## 📄 License

This project is provided for educational and development purposes.

---

## 🙏 Acknowledgments

- **MOSIP** — Open-source digital identity platform
- **Microsoft TrOCR** — Transformer-based OCR
- **PaddlePaddle** — High-accuracy OCR engine
- **FastAPI** — Modern Python web framework
- **Angular** — Frontend framework

---

<div align="center">

**Version:** 2.0.0 | **Python:** 3.10+ | **Angular:** 8 | **Status:** Production Ready 🚀

Made for MOSIP Pre-Registration and Document Processing

</div>
