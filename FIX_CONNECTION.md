# 🔧 Fix: "This site can't be reached" Error

## The Problem
You're seeing `ERR_ADDRESS_INVALID` when trying to access `http://0.0.0.0:8000/`

## ✅ Solution Steps

### Step 1: Install Dependencies
Open your terminal/command prompt and run:

```bash
pip install -r requirements_web.txt
```

**OR** if that doesn't work, install individually:

```bash
pip install fastapi uvicorn opencv-python easyocr ultralytics pillow numpy python-multipart
```

### Step 2: Verify Setup
Run the test script to check everything:

```bash
python test_setup.py
```

You should see:
- ✅ Model file found
- ✅ app.py
- ✅ index.html
- ✅ All dependencies (after Step 1)

### Step 3: Start the Server
Run:

```bash
python app.py
```

**Important**: Wait for these messages:
```
✅ YOLOv8 model loaded successfully!
✅ EasyOCR reader initialized successfully!
📡 Server running at: http://localhost:8000
```

### Step 4: Open Browser
**DO NOT** use `http://0.0.0.0:8000/`

**USE** one of these instead:
- `http://localhost:8000` ✅
- `http://127.0.0.1:8000` ✅

## 🎯 Quick Test

1. **Check if server is running**: Open `http://localhost:8000/api/health` in browser
   - Should show: `{"status":"healthy","model_loaded":true,"ocr_loaded":true}`

2. **If that works**, then `http://localhost:8000` should show the web interface

## ⚠️ Common Mistakes

❌ **Wrong**: `http://0.0.0.0:8000` (this won't work in browser)
✅ **Correct**: `http://localhost:8000`

❌ **Wrong**: Starting server but closing terminal immediately
✅ **Correct**: Keep terminal open while server is running

❌ **Wrong**: Using wrong Python (Python 2 instead of Python 3)
✅ **Correct**: Use `python --version` to check (should be 3.8+)

## 🆘 Still Not Working?

1. **Check if server started**: Look at terminal output for errors
2. **Check port**: Make sure nothing else is using port 8000
3. **Check firewall**: Windows Firewall might be blocking
4. **Try different port**: Change `port=8000` to `port=8001` in `app.py` line 349

## 📝 What Should Happen

When you run `python app.py`, you should see:

```
============================================================
🚀 Starting OCR Text Extraction Server...
============================================================
📡 Server running at: http://localhost:8000
📡 Alternative: http://127.0.0.1:8000
============================================================

🔧 Initializing models on startup...
📦 Loading YOLOv8 model from Mymodel.pt...
✅ YOLOv8 model loaded successfully!
📦 Initializing EasyOCR reader...
✅ EasyOCR reader initialized successfully!
✅ Startup complete!

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Then open `http://localhost:8000` in your browser!

