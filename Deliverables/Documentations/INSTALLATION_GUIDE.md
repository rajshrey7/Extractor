# Installation & Setup Guide
## MOSIP Pre-Registration OCR System

**Version:** 2.0.0  
**Last Updated:** December 13, 2025

---

## 📖 What is This?

This guide will help you install and run the **MOSIP Pre-Registration OCR System** on your computer. Don't worry if you're not technical - just follow each step carefully!

The application has **two parts**:
1. **OCR Tool** (localhost:8001) - Extracts text from documents
2. **MOSIP Pre-Registration** (localhost:4200) - Identity registration form

---

## Table of Contents

1. [Before You Start](#-before-you-start)
2. [Installing Requirements](#-installing-requirements)
3. [Setting Up the Project](#-setting-up-the-project)
4. [Running the Application](#-running-the-application)
5. [Using the Application](#-using-the-application)
6. [Common Problems & Solutions](#-common-problems--solutions)
7. [Quick Reference](#-quick-reference)

---

## ✅ Before You Start

### What You Need

| Item | Requirement | Why? |
|------|-------------|------|
| **Computer** | Windows 10/11, macOS, or Linux | Operating system |
| **RAM** | 4GB minimum (8GB better) | For OCR models |
| **Storage** | 5GB free space | For models and dependencies |
| **Internet** | Required for first setup | Downloads ~1-2GB of data |

### Time Required

| Step | Time (first time) |
|------|-------------------|
| Installing software | 15-20 minutes |
| Downloading models | 10-15 minutes |
| Total | ~30-40 minutes |

> 💡 **Good to know:** After the first setup, starting the app takes only 1-2 minutes!

---

## 📥 Installing Requirements

You need to install **TWO programs** before starting:
1. **Python** (the backend programming language)
2. **Node.js v12** (for the web interface)

---

### Step 1: Install Python 3.10+

#### Windows

1. Go to: https://www.python.org/downloads/
2. Click the big **"Download Python"** button
3. Run the downloaded file
4. ⚠️ **IMPORTANT:** Check the box that says **"Add Python to PATH"** at the bottom!
   
   ![Add to PATH checkbox](https://docs.python.org/3/_images/win_installer.png)
   
5. Click **"Install Now"**
6. Wait for installation to complete
7. Click **"Close"**

#### macOS

1. Go to: https://www.python.org/downloads/
2. Download the macOS installer
3. Double-click to install
4. Follow the prompts

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip -y
```

#### 🔍 Verify Python Installation

Open **PowerShell** (Windows) or **Terminal** (Mac/Linux) and type:

```bash
python --version
```

You should see something like: `Python 3.10.x` or higher.

> ❌ If you see an error or a version below 3.10, reinstall Python.

---

### Step 2: Install Node.js v12 (VERY IMPORTANT!)

⚠️ **CRITICAL:** This project requires **Node.js version 12.x ONLY**. Newer versions (14, 16, 18, 20) will NOT work!

We'll use **nvm** (Node Version Manager) to install the correct version.

---

#### Windows - Installing Node.js v12

**Part A: Install nvm-windows**

1. Download nvm-windows from this link:
   https://github.com/coreybutler/nvm-windows/releases/download/1.1.12/nvm-setup.exe

2. Run the installer (`nvm-setup.exe`)
3. Click **Next** → **Next** → **Install** → **Finish**
4. **CLOSE all PowerShell/Command Prompt windows** (Important!)

**Part B: Install Node.js 12**

1. Open **NEW PowerShell as Administrator**:
   - Click Start menu
   - Type "PowerShell"
   - Right-click **Windows PowerShell**
   - Click **"Run as administrator"**
   - Click **Yes** if prompted

2. Type these commands one by one (press Enter after each):

```powershell
nvm install 12.22.12
```

Wait for download to complete (about 1 minute).

```powershell
nvm use 12.22.12
```

3. Verify it worked:

```powershell
node --version
```

You should see: `v12.22.12`

```powershell
npm --version
```

You should see: `6.x.x` (like 6.14.16)

> ✅ If you see these versions, you're ready to continue!

---

#### macOS/Linux - Installing Node.js v12

1. Open Terminal and run:

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
```

2. Close and reopen Terminal, then run:

```bash
# Verify nvm installed
source ~/.bashrc   # or ~/.zshrc if using zsh

# Install Node 12
nvm install 12.22.12
nvm use 12.22.12

# Verify
node --version   # Should show v12.22.12
npm --version    # Should show 6.x.x
```

---

## 🔧 Setting Up the Project

Now let's set up the actual application.

### Step 3: Get the Project Files

If you have a ZIP file, extract it to a folder like `C:\extractor` (Windows) or `~/extractor` (Mac/Linux).

If using Git:
```bash
git clone <repository-url>
cd extractor
```

### Step 4: Set Up Python Environment

Open **PowerShell** (Windows) or **Terminal** (Mac/Linux) and navigate to the project:

#### Windows:

```powershell
# Navigate to project folder (change path if different)
cd C:\extractor

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

> ⚠️ **If you get a "execution policy" error**, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then try the activation again.

After activation, your prompt should show `(venv)` at the beginning like this:
```
(venv) PS C:\extractor>
```

#### macOS/Linux:

```bash
# Navigate to project folder
cd ~/extractor

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

Your prompt should show `(venv)` at the beginning.

---

### Step 5: Install Python Dependencies

With the virtual environment activated (you should see `(venv)` in your prompt):

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> ⏳ **This will take 5-10 minutes** and download about 1-2GB of data (OCR models). Be patient!

You'll see many packages being installed. Wait until you see your prompt again.

---

### Step 6: Install Frontend Dependencies

Open a **NEW terminal/PowerShell window** (keeping the first one open), then:

```bash
# Navigate to Angular project
cd C:\extractor\mosip-prereg   # Windows
# OR
cd ~/extractor/mosip-prereg    # Mac/Linux

# Install dependencies
npm install
```

> ⏳ **This will take 5-10 minutes**. You'll see warnings - that's normal, ignore them.

Wait until you see your prompt again and no more text is appearing.

---

## 🚀 Running the Application

You need **TWO terminal windows** running at the same time - one for each server.

### Terminal 1: Start the Backend (Python Server)

```powershell
# Navigate to project root
cd C:\extractor

# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# OR
source venv/bin/activate      # Mac/Linux

# Start the server
python run_server.py
```

**What you should see:**
```
====================
Starting OCR Server...
====================
✅ PaddleOCR initialized successfully
✅ Startup complete!
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

> 📍 **Keep this terminal open!** Don't close it.

> ⏳ **First time only:** The first startup downloads OCR models (~1GB). This can take 5-10 minutes. Let it run!

---

### Terminal 2: Start the Frontend (Angular Server)

Open a **NEW** PowerShell/Terminal window:

```powershell
# Navigate to Angular project
cd C:\extractor\mosip-prereg   # Windows
# OR
cd ~/extractor/mosip-prereg    # Mac/Linux

# Start the Angular server
npm start
```

**What you should see (after 1-2 minutes):**
```
** Angular Live Development Server is listening on localhost:4200 **
: Compiled successfully.
```

> 📍 **Keep this terminal open too!**

---

### ✅ Verify Everything is Running

Open your web browser and go to these addresses:

| URL | What You Should See |
|-----|---------------------|
| http://localhost:4200 | MOSIP Login page (with phone/email input) |
| http://localhost:8001 | OCR Extraction tool (upload documents) |
| http://localhost:8001/docs | API Documentation (Swagger UI) |

🎉 **Congratulations!** If you see all three pages, the application is working!

---

## 🎮 Using the Application

### OCR Tool (localhost:8001)

1. Open http://localhost:8001
2. Click **"Extract Text"** tab
3. Upload a document (JPG, PNG, or PDF)
4. Click **"Process Docs"**
5. View extracted text fields
6. Click **"Send to MOSIP"** to save as packet

### MOSIP Pre-Registration (localhost:4200)

1. Open http://localhost:4200
2. Enter any email (e.g., `test@example.com`)
3. Click **"Send OTP"**
4. Enter any 6 digits (e.g., `123456`) - the system accepts any code
5. Fill in the registration form
6. Upload documents (optional in demo mode)
7. Book appointment and submit

---

## 🔧 Common Problems & Solutions

### Problem: "npm install" or "npm start" fails with RxJS errors

**Error looks like:**
```
ERROR in node_modules/@angular-devkit/build-angular/node_modules/rxjs/internal/...
```

**Cause:** You're using the wrong Node.js version (probably 14, 16, or newer)

**Solution:**
```powershell
# Check your Node version
node --version

# If it's NOT v12.x.x, fix it:
nvm use 12.22.12

# Verify
node --version   # Should show v12.22.12

# Clean reinstall (in the mosip-prereg folder)
cd mosip-prereg
Remove-Item -Recurse -Force node_modules   # Windows
# OR: rm -rf node_modules                  # Mac/Linux
Remove-Item package-lock.json              # Windows
# OR: rm package-lock.json                 # Mac/Linux
npm cache clean --force
npm install
npm start
```

---

### Problem: PowerShell won't activate virtual environment

**Error:** "execution of scripts is disabled on this system"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then try activating again:
```powershell
.\venv\Scripts\Activate.ps1
```

---

### Problem: Port 8001 already in use

**Solution (Windows):**
```powershell
netstat -ano | findstr :8001
# Note the PID number shown
taskkill /PID <PID> /F
```

**Solution (Mac/Linux):**
```bash
lsof -ti:8001 | xargs kill -9
```

---

### Problem: Port 4200 already in use

**Solution (Windows):**
```powershell
netstat -ano | findstr :4200
taskkill /PID <PID> /F
```

**Solution (Mac/Linux):**
```bash
lsof -ti:4200 | xargs kill -9
```

---

### Problem: Python module not found

**Solution:**
Make sure your virtual environment is activated (you see `(venv)` in prompt), then:
```bash
pip install -r requirements.txt
```

---

### Problem: Blank page at localhost:4200

**Causes & Solutions:**
1. **Angular still compiling** - Wait 1-2 minutes, check terminal for "Compiled successfully"
2. **Cache issue** - Press `Ctrl+Shift+R` to hard refresh
3. **Server not running** - Check Terminal 2 is still running

---

### Problem: Login fails at localhost:4200

**Solution:**
- Check Terminal 1 (Python backend) is still running
- If it crashed, restart it with `python run_server.py`

---

### Problem: OCR models downloading slowly / taking forever

**This is normal for first run!**

- Models are ~1GB total
- On slow internet, this can take 15-30 minutes
- Once downloaded, they're cached forever
- Just wait patiently

---

## 📋 Quick Reference

### Starting the App (After First Setup)

**Terminal 1:**
```powershell
cd C:\extractor
.\venv\Scripts\Activate.ps1
python run_server.py
```

**Terminal 2:**
```powershell
cd C:\extractor\mosip-prereg
npm start
```

### Stopping the App

- Press `Ctrl+C` in each terminal window

### URLs

| Service | URL |
|---------|-----|
| MOSIP Pre-Registration | http://localhost:4200 |
| OCR Tool | http://localhost:8001 |
| API Docs | http://localhost:8001/docs |

### Demo Login

| Field | Value |
|-------|-------|
| Email/Phone | Any email (e.g., `test@example.com`) |
| OTP | Any 6 digits (e.g., `123456`) |

---

## 🆘 Still Need Help?

If you're still having issues:

1. **Screenshot the error** from your terminal
2. **Note which step** you were on
3. **Check Node version** with `node --version` (must be v12.x.x)
4. **Check Python version** with `python --version` (must be 3.10+)

---

## ⚙️ Advanced Configuration (Optional)

### Python Backend Settings (`config.py`)

```python
SELECTED_LANGUAGE = "en"  # Options: en, ar, hi
MOSIP_ENABLED = False     # Set True for real MOSIP server
```

### Frontend API URL

Edit `mosip-prereg/src/assets/configs/default.properties`:
```properties
mosip.preregistration.api.url=http://localhost:8001
```

---

**Document Version:** 2.0.0  
**Last Updated:** December 13, 2025  
**Compatible With:** Python 3.10+ | Node.js 12.x | Angular 7

---

<div align="center">

**Made for MOSIP Pre-Registration and Document Processing**

🚀 You're all set! Happy registering!

</div>
