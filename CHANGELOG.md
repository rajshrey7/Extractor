# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-11-14

### Added
- **OCR Text Extraction System**
  - YOLOv8-based object detection for document field identification
  - EasyOCR integration for text recognition from scanned documents
  - Google Vision API support for enhanced OCR accuracy
  - Support for both image (JPG, PNG) and PDF document processing
  - Multi-page PDF processing with automatic page-to-image conversion
  - Structured field extraction for ID cards (Name, DOB, Passport No, etc.)
  - General text extraction with intelligent field detection
  - JSON output format for easy integration

- **Intelligent Form Auto-Fill**
  - Smart field matching algorithm with confidence scoring
  - Field name alias support for common variations
  - Google Forms integration capabilities
  - Batch form processing support
  - Sequence matching for intelligent field mapping
  - Customizable field equivalents and variations

- **Data Verification System**
  - Advanced OCR verification engine for data validation
  - Field-by-field comparison with confidence scores
  - Data cleaning and normalization utilities
  - Verification reports with detailed match analysis
  - Overall confidence metrics calculation
  - Support for original data comparison

- **Modern Web Interface**
  - Responsive single-page application with drag-and-drop upload
  - Real-time processing feedback and status updates
  - Multi-tab interface for Extract, Verify, and Auto-Fill features
  - Interactive JSON result visualization
  - Export functionality for extracted data
  - Mobile-friendly responsive design

- **RESTful API Endpoints**
  - `/api/upload` - Upload and process images/PDFs for OCR
  - `/api/verify` - Verify extracted data against original sources
  - `/api/autofill` - Match extracted data to form fields
  - `/api/health` - Server health check and model status
  - `/api/test-json` - Test endpoint for JSON response validation
  - Job form endpoints for Google Forms integration
  - Resume processing endpoints with AI-powered filling

- **Google Forms Integration**
  - Automatic form structure analysis
  - Intelligent question extraction
  - Form submission automation
  - AI-powered form filling with RAG workflow
  - Resume-based form auto-completion

- **Configuration System**
  - Centralized configuration via `config.py`
  - Support for multiple API keys (Google Vision, OpenRouter, Llama Cloud)
  - Model selection and customization options
  - Environment-based configuration support

- **Development Tools**
  - Server startup script (`run_server.py`)
  - Comprehensive error handling and logging
  - Model lazy loading for efficient startup
  - CORS middleware for cross-origin requests
  - Static file serving support

### Features
- Support for 15+ document field types (ID cards, passports, forms)
- Non-maximum suppression for accurate bounding box filtering
- IOU-based box overlap calculation
- Pattern-based text cleaning and normalization
- Unknown field detection with custom markers
- Confidence-based field matching (threshold: 70%)
- PDF to image conversion with quality optimization
- Multi-method OCR processing (YOLO+EasyOCR or Google Vision)

### Technical Details
- Built with FastAPI for high-performance async API
- YOLOv8 object detection (`Mymodel.pt` required)
- EasyOCR for text recognition (English language support)
- OpenCV for image processing and manipulation
- Pillow for image format conversion
- NumPy for numerical array operations
- PyMuPDF/pdf2image for PDF processing
- Uvicorn ASGI server with hot-reload support

### Documentation
- Comprehensive README with installation and usage instructions
- API endpoint documentation with request/response examples
- Troubleshooting guide for common issues
- Project structure overview
- Configuration guide for API keys and models
- Supported document fields reference
- Development guidelines for extending functionality

### Initial Release
- First stable release of the OCR Text Extraction & Verification System
- Complete web application with frontend and backend
- Production-ready API endpoints
- Comprehensive error handling and validation
- Health check and monitoring endpoints

[Unreleased]: https://github.com/shreyansh-raj/Extractor/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/shreyansh-raj/Extractor/releases/tag/v1.0.0
