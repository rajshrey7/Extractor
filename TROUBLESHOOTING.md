# Troubleshooting Guide

## 🚨 Common Issues and Solutions

### Issue 1: "This site can't be reached" or "ERR_ADDRESS_INVALID"

**Problem**: You're trying to access `http://0.0.0.0:8000/` in your browser.

**Solution**: 
- Use `http://localhost:8000` or `http://127.0.0.1:8000` instead
- `0.0.0.0` is a server binding address, not a browser address

**Steps**:
1. Make sure the server is running (check terminal/command prompt)
2. Open your browser
3. Navigate to: `http://localhost:8000`

---

### Issue 2: Server Won't Start

**Problem**: Error when running `python app.py`

**Solutions**:

1. **Check Python version**:
   ```bash
   python --version
   ```
   Should be Python 3.8 or higher

2. **Install dependencies**:
   ```bash
   pip install -r requirements_web.txt
   ```

3. **Check if port 8000 is in use**:
   - Windows: `netstat -ano | findstr :8000`
   - Linux/Mac: `lsof -i :8000`
   - If port is busy, change port in `app.py` (line 349)

4. **Run test script**:
   ```bash
   python test_setup.py
   ```
   This will check all dependencies and files

---

### Issue 3: Model Not Loading

**Problem**: Warning message about `Mymodel.pt` not found

**Solutions**:

1. **Check file name** (case-sensitive):
   - Correct: `Mymodel.pt`
   - Wrong: `mymodel.pt` or `MYMODEL.PT`

2. **Check file location**:
   - File should be in the root directory (same folder as `app.py`)
   - Not in a subfolder

3. **Download the model**:
   - Check `mymodel.md` for download link
   - Download and place in root directory

4. **Verify file size**:
   - Model files are usually large (several MB)
   - If file is very small (< 1MB), it might be corrupted

---

### Issue 4: "Module not found" Errors

**Problem**: Import errors when starting server

**Solutions**:

1. **Install missing packages**:
   ```bash
   pip install fastapi uvicorn opencv-python easyocr ultralytics pillow numpy
   ```

2. **Use virtual environment** (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   pip install -r requirements_web.txt
   ```

3. **Check Python path**:
   - Make sure you're using the correct Python installation
   - Try `python3` instead of `python` on Linux/Mac

---

### Issue 5: EasyOCR Download Issues

**Problem**: EasyOCR takes a long time on first run or fails

**Solutions**:

1. **First run downloads models**:
   - This is normal and can take several minutes
   - Requires internet connection
   - Models are cached after first download

2. **Check internet connection**:
   - EasyOCR needs internet for initial model download

3. **Manual download** (if needed):
   - EasyOCR models are downloaded automatically
   - If stuck, check firewall/antivirus settings

---

### Issue 6: Poor OCR Accuracy

**Problem**: Extracted text is incorrect or missing

**Solutions**:

1. **Image quality**:
   - Use high-resolution images (at least 300 DPI)
   - Ensure good lighting and contrast
   - Avoid blurry or skewed images

2. **Image preprocessing**:
   - Rotate images to be straight
   - Crop to focus on document area
   - Adjust brightness/contrast if needed

3. **Document type**:
   - Model is trained for ID cards
   - Other documents may have lower accuracy

---

### Issue 7: Server Starts But Page Doesn't Load

**Problem**: Server running but browser shows error

**Solutions**:

1. **Check server output**:
   - Look for error messages in terminal
   - Check if models loaded successfully

2. **Verify index.html exists**:
   - File should be in same directory as `app.py`

3. **Try API endpoint directly**:
   - `http://localhost:8000/api/health`
   - Should return JSON with status

4. **Clear browser cache**:
   - Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

---

### Issue 8: "CORS" Errors

**Problem**: CORS policy errors in browser console

**Solution**: 
- Already handled in code, but if issues persist:
- Check `app.py` line 22-28 for CORS settings
- Ensure `allow_origins=["*"]` is set

---

## 🔍 Diagnostic Steps

### Step 1: Run Test Script
```bash
python test_setup.py
```
This checks:
- ✅ All dependencies installed
- ✅ Model file exists
- ✅ Required files present

### Step 2: Check Server Status
```bash
python app.py
```
Look for:
- ✅ "Server running at: http://localhost:8000"
- ✅ "YOLOv8 model loaded successfully!"
- ✅ "EasyOCR reader initialized successfully!"

### Step 3: Test API Endpoint
Open browser to: `http://localhost:8000/api/health`

Should return:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "ocr_loaded": true
}
```

### Step 4: Check Browser Console
- Press F12 in browser
- Look for errors in Console tab
- Check Network tab for failed requests

---

## 📞 Still Having Issues?

1. **Check all error messages** - They usually point to the problem
2. **Verify Python version** - Must be 3.8+
3. **Check file paths** - All files should be in root directory
4. **Review server output** - Error messages appear in terminal
5. **Test with simple image** - Try a clear, high-quality ID card image

---

## ✅ Quick Checklist

Before reporting issues, verify:

- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements_web.txt`)
- [ ] `Mymodel.pt` exists in root directory
- [ ] `app.py` and `index.html` in root directory
- [ ] Server started successfully (no errors in terminal)
- [ ] Using `http://localhost:8000` (not `0.0.0.0`)
- [ ] Port 8000 not in use by another application
- [ ] Internet connection available (for EasyOCR first run)

