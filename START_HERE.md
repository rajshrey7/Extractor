# 🚀 START HERE - Get Your Server Running

## The Problem
You're seeing "ERR_CONNECTION_REFUSED" because the server isn't running.

## ✅ Solution: Start the Server

### Option 1: Simple Way (Recommended)
1. **Open a NEW Command Prompt or PowerShell window**
2. **Navigate to your project folder**:
   ```bash
   cd C:\Users\rshre\OneDrive\Desktop\extractor
   ```
3. **Run the server**:
   ```bash
   python app.py
   ```
4. **Wait for this message**:
   ```
   ✅ YOLOv8 model loaded successfully!
   ✅ EasyOCR reader initialized successfully!
   📡 Server running at: http://localhost:8000
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```
5. **Keep this window open** (don't close it!)
6. **Open your browser** and go to: `http://localhost:8000`

### Option 2: Using the Startup Script
```bash
python run_server.py
```

### Option 3: Double-Click (Windows)
Double-click `start_server.bat` in Windows Explorer

## ⚠️ Important Notes

1. **Keep the terminal window open** - Closing it stops the server
2. **Use `http://localhost:8000`** - Not `0.0.0.0` or `127.0.0.1:8000` (though 127.0.0.1 also works)
3. **First time EasyOCR runs** - It will download models (takes 2-5 minutes, needs internet)
4. **Model loading** - First startup loads the YOLOv8 model (takes 10-30 seconds)

## 🔍 How to Know It's Working

When the server starts successfully, you'll see:
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

INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## 🐛 If It Still Doesn't Work

1. **Check for errors** in the terminal output
2. **Verify dependencies**:
   ```bash
   python test_setup.py
   ```
3. **Check if port 8000 is free**:
   ```bash
   netstat -ano | findstr :8000
   ```
   If something is using it, change port in `app.py` line 349

## 📝 Quick Test

Once server is running:
1. Open browser: `http://localhost:8000`
2. You should see the OCR web interface
3. Or test API: `http://localhost:8000/api/health`
   - Should return: `{"status":"healthy","model_loaded":true,"ocr_loaded":true}`

## 🎯 Next Steps After Server Starts

1. Go to "Extract Text" tab
2. Upload an image (ID card, document, etc.)
3. Click "Process Image"
4. See extracted text!

---

**Remember**: The server must be running in a terminal window for the website to work!

