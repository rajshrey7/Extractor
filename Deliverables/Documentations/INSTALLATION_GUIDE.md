# Installation & Integration Guide
## OCR Text Extraction & Verification System

**Version:** 1.0.0  
**Last Updated:** November 30, 2024

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
   - [Windows](#windows-installation)
   - [Linux/Ubuntu](#linux-installation)
   - [macOS](#macos-installation)
   - [Docker](#docker-deployment)
3. [Configuration](#configuration)
4. [MOSIP Integration](#mosip-integration)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)
7. [Upgrade Guide](#upgrade-guide)

---

## System Requirements

### Minimum Requirements

| Component | Specification |
|-----------|--------------|
| **OS** | Windows 10+, Ubuntu 20.04+, macOS 11+ |
| **Python** | 3.10 - 3.14 |
| **RAM** | 4GB (8GB recommended for TrOCR) |
| **Disk Space** | 5GB (includes models) |
| **CPU** | Dual-core 2.0GHz+ |
| **GPU** | Optional (CUDA for TrOCR acceleration) |

### Recommended Requirements

| Component | Specification |
|-----------|--------------|
| **RAM** | 16GB |
| **Disk Space** | 10GB SSD |
| **CPU** | Quad-core 3.0GHz+ |
| **GPU** | NVIDIA with CUDA 11.8+ |

### Software Dependencies

- Python 3.10+
- pip (Python package manager)
- Git (for cloning repository)
- Web browser (Chrome, Firefox, Edge, Safari)

---

## Installation

### Windows Installation

#### Step 1: Install Python

1. Download Python 3.10+ from [python.org](https://www.python.org/downloads/)
2. Run installer and **check "Add Python to PATH"**
3. Verify installation:

```cmd
python --version
pip --version
```

#### Step 2: Clone Repository

```cmd
git clone https://github.com/your-org/ocr-extractor.git
cd ocr-extractor
```

#### Step 3: Create Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

**Verification:** Command prompt should show `(venv)` prefix

#### Step 4: Install Dependencies

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** First install downloads ~2GB of models (PaddleOCR, TrOCR)

#### Step 5: Verify Installation

```cmd
python -c "import paddle; import transformers; print('✓ Dependencies OK')"
```

#### Step 6: Start Server

```cmd
python run_server.py
```

**Success:** Server running at http://localhost:8001

---

### Linux Installation

#### Step 1: Update System

```bash
sudo apt update
sudo apt upgrade -y
```

#### Step 2: Install Python 3.10+

```bash
sudo apt install python3.10 python3.10-venv python3-pip -y
python3.10 --version
```

#### Step 3: Clone Repository

```bash
git clone https://github.com/your-org/ocr-extractor.git
cd ocr-extractor
```

#### Step 4: Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
```

#### Step 5: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**For GPU support (optional):**

```bash
pip install torch==2.6.0+cu118 --index-url https://download.pytorch.org/whl/cu118
```

#### Step 6: Start Server

```bash
python run_server.py
```

**Run as Background Service:**

```bash
nohup python run_server.py > server.log 2>&1 &
```

---

### macOS Installation

#### Step 1: Install Homebrew (if not installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Step 2: Install Python 3.10+

```bash
brew install python@3.10
python3.10 --version
```

#### Step 3: Clone Repository

```bash
git clone https://github.com/your-org/ocr-extractor.git
cd ocr-extractor
```

#### Step 4: Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
```

#### Step 5: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 6: Start Server

```bash
python run_server.py
```

---

### Docker Deployment

#### Option 1: Using Docker Compose (Recommended)

**Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  ocr-extractor:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - ./uploads:/app/uploads
      - ./mock_packets:/app/mock_packets
    environment:
      - SELECTED_LANGUAGE=en
      - MOSIP_ENABLED=false
    restart: unless-stopped
```

**Create `Dockerfile`:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p uploads mock_packets

# Expose port
EXPOSE 8001

# Run server
CMD ["python", "run_server.py"]
```

**Deploy:**

```bash
docker-compose up -d
```

**Access:** http://localhost:8001

#### Option 2: Docker Run

```bash
docker build -t ocr-extractor .
docker run -d -p 8001:8001 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/mock_packets:/app/mock_packets \
  --name ocr-server \
  ocr-extractor
```

---

## Configuration

### 1. Basic Configuration

Edit `config.py`:

```python
# Default Language (en, ar, hi)
SELECTED_LANGUAGE = "en"

# Server Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 8001       # Default port

# File Upload Settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
```

### 2. MOSIP Configuration

```python
# MOSIP Integration
MOSIP_ENABLED = True  # Enable MOSIP features
MOSIP_API_URL = "https://mosip-server.example.com"
MOSIP_API_KEY = "your-api-key-here"
MOSIP_API_VERSION = "v1"

# Packet Storage
PACKETS_DIR = "mock_packets"
```

### 3. OCR Engine Configuration

```python
# PaddleOCR Settings
PADDLE_LANG = "en"
PADDLE_USE_GPU = False  # Set True if GPU available

# TrOCR Settings
TROCR_MODEL = "microsoft/trocr-large-handwritten"
TROCR_DEVICE = "cpu"  # or "cuda" for GPU
```

### 4. Quality Thresholds

```python
# Image Quality Thresholds
BLUR_THRESHOLD = 100.0      # Laplacian variance
BRIGHTNESS_MIN = 50         # Minimum brightness
BRIGHTNESS_MAX = 200        # Maximum brightness
OVERALL_QUALITY_MIN = 70    # Minimum overall score
```

---

## MOSIP Integration

### Prerequisites

1. Access to MOSIP Pre-Registration server
2. Valid API credentials
3. Network connectivity to MOSIP endpoint

### Step 1: Configure MOSIP Connection

Edit `config.py`:

```python
MOSIP_ENABLED = True
MOSIP_API_URL = "https://your-mosip-server.com/preregistration/v1"
MOSIP_API_KEY = "your-api-key"
```

### Step 2: Test Connection

```python
from mosip_client import MosipClient

client = MosipClient()
status = client.test_connection()
print(f"MOSIP Connection: {status}")
```

### Step 3: Field Mapping Configuration

Edit `mosip_field_mapper.py` to customize field mappings:

```python
FIELD_MAPPING = {
    # OCR Field → MOSIP Schema Field
    "Name": "fullName",
    "Date of Birth": "dateOfBirth",
    "Gender": "gender",
    "Address": "addressLine1",
    ...
}
```

### Step 4: Create Test Packet

```bash
curl -X POST http://localhost:8001/api/mosip/send \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

### Step 5: Upload to MOSIP

```bash
curl -X POST http://localhost:8001/api/mosip/upload/{packet_id}
```

**Expected Response:**

```json
{
  "success": true,
  "mosip_prid": "1234567890123456"
}
```

---

## Production Deployment

### 1. Using Systemd (Linux)

**Create service file:** `/etc/systemd/system/ocr-extractor.service`

```ini
[Unit]
Description=OCR Extraction Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ocr-extractor
Environment="PATH=/opt/ocr-extractor/venv/bin"
ExecStart=/opt/ocr-extractor/venv/bin/python run_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable ocr-extractor
sudo systemctl start ocr-extractor
sudo systemctl status ocr-extractor
```

### 2. Using Nginx Reverse Proxy

**Install Nginx:**

```bash
sudo apt install nginx -y
```

**Configure:** `/etc/nginx/sites-available/ocr-extractor`

```nginx
server {
    listen 80;
    server_name ocr.example.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Increase timeout for large file uploads
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        
        # Increase max body size
        client_max_body_size 20M;
    }
}
```

**Enable site:**

```bash
sudo ln -s /etc/nginx/sites-available/ocr-extractor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. SSL/HTTPS Setup (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d ocr.example.com
```

### 4. Performance Tuning

**Increase worker processes in `run_server.py`:**

```python
if __name__ == "__main__":
    import multiprocessing
    
    workers = multiprocessing.cpu_count()
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        workers=workers,
        log_level="info"
    )
```

---

## Troubleshooting

### Installation Issues

#### Issue: `ModuleNotFoundError`

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

#### Issue: `torch` installation fails

**Solution:**
```bash
# CPU version
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu

# GPU version (CUDA 11.8)
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu118
```

#### Issue: `venv` not activating

**Windows:**
```cmd
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\activate
```

**Linux/Mac:**
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

### Runtime Issues

#### Issue: Server won't start (port in use)

**Check port:**
```bash
# Windows
netstat -ano | findstr :8001

# Linux/Mac
lsof -ti:8001
```

**Kill process:**
```bash
# Windows
taskkill /PID <PID> /F

# Linux/Mac
kill -9 <PID>
```

#### Issue: Out of memory

**Solution:** Reduce model size or increase RAM

```python
# In config.py
TROCR_MODEL = "microsoft/trocr-base-handwritten"  # Smaller model
```

#### Issue: MOSIP connection fails

**Debug:**
```bash
curl -X GET https://your-mosip-server.com/health
```

**Check firewall:**
```bash
sudo ufw allow 8001
```

---

## Upgrade Guide

### From v0.x to v1.0

#### Step 1: Backup Data

```bash
cp -r mock_packets mock_packets.backup
cp -r uploads uploads.backup
```

#### Step 2: Pull Latest Code

```bash
git pull origin main
```

#### Step 3: Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

#### Step 4: Migrate Configuration

**Old `config.py` → New `config.py`**

```python
# Update language codes
SELECTED_LANGUAGE = "en"  # was "english"

# Add new fields
MOSIP_ENABLED = False
```

#### Step 5: Restart Server

```bash
sudo systemctl restart ocr-extractor
```

---

## Health Checks

### Manual Check

```bash
curl http://localhost:8001/api/health
```

**Expected:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "ocr_loaded": true
}
```

### Automated Monitoring

**Create `monitor.sh`:**

```bash
#!/bin/bash
ENDPOINT="http://localhost:8001/api/health"
RESPONSE=$(curl -s $ENDPOINT)

if echo $RESPONSE | grep -q "healthy"; then
    echo "✓ Service healthy"
    exit 0
else
    echo "✗ Service unhealthy"
    systemctl restart ocr-extractor
    exit 1
fi
```

**Add to cron:**
```bash
*/5 * * * * /opt/ocr-extractor/monitor.sh
```

---

## Security Hardening

### 1. Firewall Configuration

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. File Permissions

```bash
chmod 750 /opt/ocr-extractor
chmod 640 /opt/ocr-extractor/config.py
chown -R www-data:www-data /opt/ocr-extractor
```

### 3. Environment Variables

**Use `.env` file instead of hardcoding secrets:**

```bash
# .env
MOSIP_API_KEY=your-secret-key
MOSIP_API_URL=https://mosip-server.com
```

**Load in `config.py`:**

```python
from dotenv import load_dotenv
import os

load_dotenv()
MOSIP_API_KEY = os.getenv("MOSIP_API_KEY")
```

---

**Document Version:** 1.0  
**Support:** support@your-org.com  
**Last Reviewed:** November 30, 2024
