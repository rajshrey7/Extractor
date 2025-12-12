# Installation & Integration Guide
## MOSIP Pre-Registration OCR System

**Version:** 2.0.0  
**Last Updated:** December 12, 2024

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Start](#quick-start)
3. [Detailed Installation](#detailed-installation)
   - [Windows](#windows-installation)
   - [Linux/Ubuntu](#linux-installation)
   - [macOS](#macos-installation)
4. [Running the Application](#running-the-application)
5. [Configuration](#configuration)
6. [OCR to Form Integration](#ocr-to-form-integration)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

| Component | Specification |
|-----------|--------------|
| **OS** | Windows 10+, Ubuntu 20.04+, macOS 11+ |
| **Python** | 3.10 or higher |
| **Node.js** | 14.x or higher |
| **RAM** | 4GB (8GB recommended for TrOCR) |
| **Disk Space** | 5GB (includes OCR models) |

### Verify Prerequisites

```bash
# Check Python version
python --version
# Should output: Python 3.10.x or higher

# Check Node.js version
node --version
# Should output: v14.x.x or higher

# Check npm version
npm --version
```

---

## Quick Start

### 5-Minute Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd extractor

# 2. Create and activate Python virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\Activate.ps1

# Linux/macOS:
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Angular dependencies
cd mosip-prereg
npm install
cd ..

# 5. Start Backend (Terminal 1)
python run_server.py

# 6. Start Frontend (Terminal 2)
cd mosip-prereg
npm start
```

### Access the Application

| Application | URL |
|------------|-----|
| **MOSIP Pre-Registration** | http://localhost:4200 |
| **OCR Extraction Tool** | http://localhost:8001 |
| **API Documentation** | http://localhost:8001/docs |

---

## Detailed Installation

### Windows Installation

#### Step 1: Install Python 3.10+

1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. **✅ Check "Add Python to PATH"**
4. Click "Install Now"

#### Step 2: Install Node.js 14+

1. Download from [nodejs.org](https://nodejs.org/)
2. Run installer with default options
3. Restart terminal after installation

#### Step 3: Clone Repository

```powershell
git clone <repository-url>
cd extractor
```

#### Step 4: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

**Verification:** Your prompt should show `(venv)` prefix.

#### Step 5: Install Python Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** First installation downloads ~2GB of OCR models. This may take 10-15 minutes.

#### Step 6: Install Angular Dependencies

```powershell
cd mosip-prereg
npm install
cd ..
```

#### Step 7: Verify Installation

```powershell
# Test Python imports
python -c "import paddle; import transformers; print('✅ Python dependencies OK')"

# Test Node modules
cd mosip-prereg
npm list @angular/core
cd ..
```

---

### Linux Installation

#### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### Step 2: Install Python 3.10+

```bash
sudo apt install python3.10 python3.10-venv python3-pip -y
python3.10 --version
```

#### Step 3: Install Node.js 14+

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
node --version
npm --version
```

#### Step 4: Clone and Setup

```bash
git clone <repository-url>
cd extractor

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Angular
cd mosip-prereg
npm install
cd ..
```

---

### macOS Installation

#### Step 1: Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Step 2: Install Python and Node.js

```bash
brew install python@3.10 node
python3.10 --version
node --version
```

#### Step 3: Clone and Setup

```bash
git clone <repository-url>
cd extractor

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Angular
cd mosip-prereg
npm install
cd ..
```

---

## Running the Application

### Start Both Servers

You need **two terminal windows** running simultaneously.

#### Terminal 1: Python Backend (Port 8001)

```bash
# Navigate to project root
cd extractor

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Start server
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

#### Terminal 2: Angular Frontend (Port 4200)

```bash
# Navigate to Angular project
cd extractor/mosip-prereg

# Start development server
npm start
```

**Expected Output:**
```
** Angular Live Development Server is listening on localhost:4200 **
: Compiled successfully.
```

### Verify Both Servers

1. Open http://localhost:4200 → MOSIP Login page
2. Open http://localhost:8001 → OCR Extraction tool
3. Open http://localhost:8001/docs → API documentation

---

## Configuration

### Backend Configuration (`config.py`)

```python
# Language Settings
SELECTED_LANGUAGE = "en"  # en, ar, hi

# MOSIP Integration
MOSIP_ENABLED = False     # True to connect to real MOSIP server
MOSIP_BASE_URL = "https://collab.mosip.net"
MOSIP_CLIENT_ID = "mosip-prereg-client"
MOSIP_CLIENT_SECRET = "your-secret"
```

### Frontend Configuration

#### API URL (`mosip-prereg/src/assets/configs/default.properties`)

```properties
mosip.preregistration.api.url=http://localhost:8001
```

#### Supported Languages

The system supports:
- **English (eng)** — Default
- **Arabic (ara)** — RTL support
- **French (fra)**

---

## OCR to Form Integration

### How It Works

1. **User opens OCR tool** (http://localhost:8001)
2. **Uploads document** and processes with OCR
3. **Extracted data sent via `postMessage`** to Angular app
4. **OcrDataService receives** and stores data
5. **DemographicComponent auto-fills** form fields

### Field Mapping

| OCR Extracted Field | MOSIP Form Field |
|---------------------|------------------|
| Name, Full Name | fullName |
| Father Name, Father's Name | fatherName |
| Mother Name, Mother's Name | motherName |
| Date of Birth, DOB | dateOfBirth |
| Gender, Sex | gender |
| Phone, Mobile | phone |
| Email | email |
| Address | addressLine1 |
| City | city |
| Pin Code, Postal Code | postalCode |

### Testing the Integration

1. Open http://localhost:4200
2. Login with any email and OTP (e.g., `123456`)
3. Create new application
4. Click "Scan Document" in demographic form
5. Upload a document with name, DOB, etc.
6. Fields should auto-fill in the form

---

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/ocr-backend.service`:

```ini
[Unit]
Description=OCR Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/extractor
Environment="PATH=/opt/extractor/venv/bin"
ExecStart=/opt/extractor/venv/bin/python run_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable ocr-backend
sudo systemctl start ocr-backend
```

### Angular Production Build

```bash
cd mosip-prereg
npm run build --prod
```

Deploy `dist/` folder to web server (Nginx, Apache).

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name prereg.example.com;

    # Angular frontend
    location / {
        root /var/www/mosip-prereg;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /preregistration/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
    }
}
```

---

## Troubleshooting

### Installation Issues

#### Python: ModuleNotFoundError

```bash
# Ensure virtual environment is activated
# Then reinstall:
pip install --upgrade -r requirements.txt
```

#### Node: npm install fails

```bash
cd mosip-prereg
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### Windows: venv won't activate

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### Runtime Issues

#### Port 8001 in use

```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8001 | xargs kill -9
```

#### Port 4200 in use

```bash
# Windows
netstat -ano | findstr :4200
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:4200 | xargs kill -9
```

#### Angular compilation errors

```bash
cd mosip-prereg
npm start -- --source-map=false
```

#### OCR models downloading slowly

First startup downloads ~1GB of models. On slow connections:
- Wait patiently (can take 10-20 minutes)
- Models are cached after first download

### MOSIP UI Issues

| Problem | Solution |
|---------|----------|
| Login fails | Restart Python backend |
| Form fields missing | Clear browser cache (Ctrl+Shift+R) |
| Preview not showing fields | Check console for errors |
| Appointment booking fails | Ensure backend is running |

### OCR Issues

| Problem | Solution |
|---------|----------|
| Poor accuracy | Check image quality (>85% recommended) |
| Handwritten text missing | Enable TrOCR checkbox |
| Processing timeout | Reduce image size or PDF pages |

---

## Health Checks

### Backend Health

```bash
curl http://localhost:8001/
# Should return HTML of OCR tool
```

### Frontend Health

```bash
curl http://localhost:4200/
# Should return Angular app HTML
```

### API Health

```bash
curl http://localhost:8001/preregistration/v1/config
# Should return JSON configuration
```

---

## Quick Reference Commands

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/macOS

# Start backend
python run_server.py

# Start frontend
cd mosip-prereg && npm start

# Stop all Python processes (Windows)
Get-Process -Name python | Stop-Process -Force

# Stop all Node processes (Windows)
Get-Process -Name node | Stop-Process -Force
```

---

**Document Version:** 2.0  
**Last Updated:** December 12, 2024
