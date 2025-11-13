# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements_web.txt
```

### Step 2: Ensure Model File is Present
- Make sure `Mymodel.pt` is in the root directory
- If not, download it from the link in `mymodel.md`

### Step 3: Start the Server

**Windows:**
```bash
start_server.bat
```

**Linux/Mac:**
```bash
chmod +x start_server.sh
./start_server.sh
```

**Or manually:**
```bash
python app.py
```

### Step 4: Open Your Browser
Navigate to: **http://localhost:8000**

## 📖 Usage Examples

### Example 1: Extract Text from ID Card
1. Go to "Extract Text" tab
2. Upload an image of an ID card
3. Click "Process Image"
4. View extracted fields

### Example 2: Verify Extracted Data
1. Extract text first (or paste JSON manually)
2. Go to "Verify Data" tab
3. Paste extracted data:
   ```json
   {"Name": "John Doe", "Date of Birth": "01/01/1990"}
   ```
4. Paste original data:
   ```json
   {"Name": "John Doe", "Date of Birth": "01/01/1990"}
   ```
5. Click "Verify Data"
6. View confidence scores

### Example 3: Auto-Fill Form Fields
1. Go to "Auto-Fill Form" tab
2. Enter form fields (one per line):
   ```
   Full Name
   Date of Birth
   Passport Number
   ```
3. Paste extracted data (JSON)
4. Click "Match Fields"
5. See which fields matched with confidence scores

## 🔧 Troubleshooting

**Port already in use?**
- Change port in `app.py`: `uvicorn.run(app, host="0.0.0.0", port=8001)`

**Model not loading?**
- Check file name: `Mymodel.pt` (case-sensitive)
- Ensure file is in root directory

**Dependencies error?**
- Use Python 3.8+
- Try: `pip install --upgrade pip`
- Then: `pip install -r requirements_web.txt`

## 📝 API Usage (cURL Examples)

### Upload Image
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@your_image.jpg"
```

### Verify Data
```bash
curl -X POST "http://localhost:8000/api/verify" \
  -F "extracted_data={\"Name\":\"John\"}" \
  -F "original_data={\"Name\":\"John\"}"
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

## 🎯 Tips for Best Results

1. **Image Quality**: Use high-resolution, clear images
2. **Lighting**: Ensure good lighting and minimal shadows
3. **Orientation**: Keep documents straight and flat
4. **Format**: JPG/PNG formats work best
5. **Size**: Images under 10MB process faster

## 📞 Need Help?

Check the full `README.md` for detailed documentation.

