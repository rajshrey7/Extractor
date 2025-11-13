# OCR Text Extraction & Verification System

A comprehensive web application for extracting text from scanned documents (ID cards, forms), intelligently auto-filling digital forms, and verifying extracted data against original sources.

## Features

- 📄 **Document OCR**: Extract text from scanned documents using YOLOv8 object detection and EasyOCR
- 🎯 **Intelligent Form Auto-Fill**: Automatically match extracted data to form fields with confidence scoring
- ✅ **Data Verification**: Compare extracted data with original sources to ensure accuracy
- 🎨 **Modern Web Interface**: Beautiful, responsive UI with drag-and-drop file upload
- 🔍 **Field Detection**: Automatically detects ID card fields (Name, Date of Birth, Passport No, etc.)

## Prerequisites

- Python 3.8 or higher
- Pre-trained YOLOv8 model (`Mymodel.pt`) - Place in the root directory
- Web browser (Chrome, Firefox, Edge, etc.)

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements_web.txt
   ```

   Or if you want to use the full requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure the model file is present**:
   - Download `Mymodel.pt` from the link in `mymodel.md`
   - Place it in the root directory as `Mymodel.pt`

## Usage

### Starting the Server

Run the FastAPI server:

```bash
python app.py
```

Or using uvicorn directly:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at: `http://localhost:8000`

### Using the Web Interface

1. **Extract Text Tab**:
   - Upload an image of a document (ID card, form, etc.)
   - Click "Process Image" or drag and drop the image
   - View extracted fields and general text

2. **Verify Data Tab**:
   - Paste extracted data (JSON format)
   - Paste original/reference data (JSON format)
   - Click "Verify Data" to see confidence scores and matches

3. **Auto-Fill Form Tab**:
   - Enter form field names (one per line or JSON array)
   - Paste extracted data (JSON format)
   - Click "Match Fields" to see which extracted fields match form fields

## API Endpoints

### POST `/api/upload`
Upload and process an image for OCR extraction.

**Request**: Multipart form data with `file` field

**Response**:
```json
{
  "success": true,
  "filename": "image.jpg",
  "extracted_fields": {
    "Name": "John Doe",
    "Date of Birth": "01/01/1990",
    ...
  },
  "general_text": ["line1", "line2", ...],
  "found_idcard": true
}
```

### POST `/api/verify`
Verify extracted data against original source.

**Request**: Form data with:
- `extracted_data`: JSON string of extracted fields
- `original_data`: JSON string of original/reference fields

**Response**:
```json
{
  "success": true,
  "verification_results": {
    "Name": {
      "extracted": "John Doe",
      "original": "John Doe",
      "match": true,
      "confidence": 100.0
    },
    ...
  },
  "overall_confidence": 95.5,
  "fields_verified": 5
}
```

### POST `/api/autofill`
Match extracted data to form fields.

**Request**: Form data with:
- `form_fields`: JSON array of form field names
- `extracted_data`: JSON string of extracted fields

**Response**:
```json
{
  "success": true,
  "matches": {
    "Full Name": {
      "matched_field": "Name",
      "value": "John Doe",
      "confidence": 85.5
    },
    ...
  },
  "fields_matched": 3
}
```

### GET `/api/health`
Health check endpoint to verify server and model status.

## Project Structure

```
extractor/
├── app.py                 # FastAPI backend application
├── index.html             # Frontend web interface
├── Mymodel.pt            # YOLOv8 pre-trained model (required)
├── requirements_web.txt  # Web app dependencies
├── requirements.txt      # Full dependencies
├── README.md             # This file
├── imgID_final.py        # Original single image processor
└── img_ID_det_folder.py  # Original batch processor
```

## Supported Document Fields

The system can extract the following ID card fields:
- Surname
- Name
- Nationality
- Sex
- Date of Birth
- Place of Birth
- Issue Date
- Expiry Date
- Issuing Office
- Height
- Type
- Country
- Passport No
- Personal No
- Card No

Plus additional fields like Phone No, Email, Address, etc.

## Troubleshooting

1. **Model not found error**:
   - Ensure `Mymodel.pt` is in the root directory
   - Check the file name matches exactly (case-sensitive)

2. **OCR not working**:
   - Ensure EasyOCR models are downloaded (first run will download automatically)
   - Check internet connection for initial model download

3. **Server won't start**:
   - Check if port 8000 is available
   - Verify all dependencies are installed: `pip install -r requirements_web.txt`

4. **Poor extraction accuracy**:
   - Ensure image quality is good (high resolution, clear text)
   - Try preprocessing images (adjust brightness/contrast)
   - Check if document type matches training data

## Development

To modify or extend the application:

- Backend: Edit `app.py` to add new endpoints or modify OCR logic
- Frontend: Edit `index.html` to change UI or add features
- Model: Replace `Mymodel.pt` with your own trained YOLOv8 model

## License

This project is provided as-is for educational and development purposes.

## Acknowledgments

- Uses YOLOv8 from Ultralytics for object detection
- Uses EasyOCR for text recognition
- Built with FastAPI for the backend
- Modern UI with vanilla JavaScript

