# API Documentation
## OCR Text Extraction & Verification System

**Base URL:** `http://localhost:8001`  
**API Version:** 1.0  
**Protocol:** HTTP/HTTPS  
**Content Type:** `application/json`, `multipart/form-data`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Error Handling](#error-handling)
3. [Rate Limiting](#rate-limiting)
4. [Endpoints](#endpoints)
   - [OCR Extraction](#ocr-extraction)
   - [Data Verification](#data-verification)
   - [MOSIP Integration](#mosip-integration)
   - [Configuration](#configuration)
5. [Response Codes](#response-codes)
6. [Examples](#examples)

---

## Authentication

**Current Version:** No authentication required (local deployment)

**Future Versions:** Bearer token authentication planned

```http
Authorization: Bearer {token}
```

---

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error message description",
  "detail": "Detailed error information",
  "status_code": 400
}
```

### Common Error Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid input parameters |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side error |

---

## Rate Limiting

**Current:** No rate limits (local deployment)

**Recommended for Production:**
- 100 requests/minute per IP
- 1000 requests/hour per IP

---

## Endpoints

### OCR Extraction

#### POST `/api/upload`

Upload and process a document for OCR extraction.

**Request:**

```http
POST /api/upload HTTP/1.1
Host: localhost:8001
Content-Type: multipart/form-data
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Image or PDF file (JPG, PNG, PDF) |
| `use_openai` | String | No | "true" to enable PaddleOCR |
| `use_trocr` | String | No | "true" to enable TrOCR (handwritten) |
| `stream` | String | No | "true" for streaming response |

**Request Example:**

```bash
curl -X POST http://localhost:8001/api/upload \
  -F "file=@passport.jpg" \
  -F "use_openai=true" \
  -F "use_trocr=false"
```

**Response (Success):**

```json
{
  "success": true,
  "filename": "passport.jpg",
  "file_type": "image",
  "method": "paddle_trocr_combined",
  "found_idcard": true,
  "extracted_fields": {
    "Name": "John Smith",
    "Passport No": "AB1234567",
    "Date of Birth": "01/01/1990",
    "Nationality": "American",
    "Expiry Date": "01/01/2030"
  },
  "trocr_confidence": {
    "Name": 0.976,
    "Passport No": 0.942,
    "Date of Birth": 0.883,
    "Nationality": 0.891,
    "Expiry Date": 0.867
  },
  "general_text": [
    "PASSPORT",
    "UNITED STATES OF AMERICA",
    "Full extracted text..."
  ],
  "quality": {
    "overall": 95.2,
    "blur": 158.32,
    "brightness": 125.45,
    "contrast": 92.3,
    "noise": 88.5,
    "resolution": 98.7,
    "warnings": [],
    "recommendation": "Excellent quality - proceed"
  }
}
```

**Response Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid file format
- `500 Internal Server Error` - Processing failed

---

#### POST `/api/upload-stream`

Upload with real-time streaming feedback.

**Request:**

```http
POST /api/upload-stream HTTP/1.1
Content-Type: multipart/form-data
```

**Parameters:** Same as `/api/upload`

**Response:** Server-Sent Events (SSE) stream

```
event: progress
data: {"stage": "quality_check", "percent": 20}

event: progress
data: {"stage": "ocr_processing", "percent": 60}

event: complete
data: {"success": true, "extracted_fields": {...}}
```

---

### Data Verification

#### POST `/api/verify`

Verify extracted data against original source.

**Request:**

```http
POST /api/verify HTTP/1.1
Content-Type: application/x-www-form-urlencoded
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `extracted_data` | JSON String | Yes | OCR extracted fields |
| `original_data` | JSON String | No | Reference/source data |
| `ocr_text_block` | String | No | Raw OCR text for validation |

**Request Example:**

```bash
curl -X POST http://localhost:8001/api/verify \
  -d "extracted_data={\"Name\":\"John\",\"Email\":\"john@example.com\"}" \
  -d "original_data={\"Name\":\"John\",\"Email\":\"john@example.com\"}"
```

**Response (Success):**

```json
{
  "success": true,
  "overall_verification_status": "PASS WITH CORRECTIONS",
  "cleaned_data": {
    "Name": "John Smith",
    "Email": "john@example.com",
    "Phone": "+1-555-1234"
  },
  "verification_report": [
    {
      "field": "Name",
      "extracted": "John Smith",
      "original": "John Smith",
      "status": "PASS",
      "confidence": 100,
      "match_percentage": 100,
      "issues": []
    },
    {
      "field": "Email",
      "extracted": "john@example.com",
      "original": "john@example.com",
      "status": "PASS",
      "confidence": 95.5,
      "match_percentage": 100,
      "issues": []
    }
  ],
  "summary": {
    "total_fields": 5,
    "passed_fields": 5,
    "failed_fields": 0,
    "corrected_fields": 0,
    "overall_confidence": 97.8
  }
}
```

**Response Codes:**
- `200 OK` - Verification complete
- `400 Bad Request` - Invalid JSON data

---

### MOSIP Integration

#### POST `/api/mosip/send`

Create MOSIP registration packet.

**Request:**

```http
POST /api/mosip/send HTTP/1.1
Content-Type: application/json
```

**Body:**

```json
{
  "extracted_fields": {
    "Name": "John Smith",
    "Date of Birth": "01/01/1990"
  },
  "extracted_metadata": {
    "trocr_confidence": {
      "Name": 0.95,
      "Date of Birth": 0.88
    },
    "quality": {
      "overall": 92.5
    }
  }
}
```

**Response (Success):**

```json
{
  "success": true,
  "packet_id": "PKT_20241130_001",
  "message": "Packet created successfully",
  "packet_location": "mock_packets/PKT_20241130_001.json"
}
```

---

#### GET `/api/mosip/packets`

List all created MOSIP packets.

**Request:**

```bash
curl http://localhost:8001/api/mosip/packets
```

**Response:**

```json
{
  "success": true,
  "packets": [
    {
      "packet_id": "PKT_20241130_001",
      "created_at": "2024-11-30T10:30:00",
      "status": "created",
      "field_count": 8
    },
    {
      "packet_id": "PKT_20241130_002",
      "created_at": "2024-11-30T11:15:00",
      "status": "uploaded",
      "mosip_prid": "1234567890"
    }
  ]
}
```

---

#### GET `/api/mosip/packet/{packet_id}`

Retrieve specific packet details.

**Request:**

```bash
curl http://localhost:8001/api/mosip/packet/PKT_20241130_001
```

**Response:**

```json
{
  "packet_id": "PKT_20241130_001",
  "data": {
    "identity": {
      "fullName": [{"language": "en", "value": "John Smith"}],
      "dateOfBirth": "1990/01/01",
      "gender": [{"language": "en", "value": "Male"}]
    },
    "metadata": {
      "created_at": "2024-11-30T10:30:00",
      "quality_score": 92.5,
      "confidence_scores": {
        "Name": 0.95
      }
    }
  }
}
```

---

#### POST `/api/mosip/upload/{packet_id}`

Upload packet to MOSIP Pre-Registration server.

**Request:**

```bash
curl -X POST http://localhost:8001/api/mosip/upload/PKT_20241130_001
```

**Response (Success):**

```json
{
  "success": true,
  "packet_id": "PKT_20241130_001",
  "mosip_prid": "1234567890123456",
  "message": "Packet uploaded successfully to MOSIP"
}
```

---

### Configuration

#### GET `/api/config`

Get current application configuration.

**Request:**

```bash
curl http://localhost:8001/api/config
```

**Response:**

```json
{
  "language": "en",
  "supported_languages": ["en", "ar", "hi"],
  "translations": {
    "app_title": "OCR Text Extraction & Verification",
    "tab_extract": "Extract Text",
    ...
  }
}
```

---

#### POST `/api/set-language`

Change application language.

**Request:**

```bash
curl -X POST http://localhost:8001/api/set-language \
  -d "language=hi"
```

**Response:**

```json
{
  "success": true,
  "language": "hi",
  "translations": {
    "app_title": "OCR टेक्स्ट निष्कर्षण और सत्यापन",
    ...
  }
}
```

---

#### GET `/api/health`

Health check endpoint.

**Request:**

```bash
curl http://localhost:8001/api/health
```

**Response:**

```json
{
  "status": "healthy",
  "model_loaded": true,
  "ocr_loaded": true,
  "mosip_available": true
}
```

---

## Response Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation failed |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | OCR engine not loaded |

---

## Examples

### Example 1: Extract Text from Image (Python)

```python
import requests

url = "http://localhost:8001/api/upload"
files = {"file": open("passport.jpg", "rb")}
data = {"use_openai": "true", "use_trocr": "false"}

response = requests.post(url, files=files, data=data)
result = response.json()

if result["success"]:
    print("Extracted Fields:")
    for field, value in result["extracted_fields"].items():
        confidence = result["trocr_confidence"].get(field, 0)
        print(f"  {field}: {value} (Confidence: {confidence:.2%})")
else:
    print(f"Error: {result['error']}")
```

### Example 2: Verify Data (JavaScript)

```javascript
const formData = new FormData();
formData.append('extracted_data', JSON.stringify({
  Name: "John Smith",
  Email: "john@example.com"
}));

fetch('http://localhost:8001/api/verify', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(data => {
    console.log('Verification Status:', data.overall_verification_status);
    console.log('Confidence:', data.summary.overall_confidence);
  });
```

### Example 3: Create MOSIP Packet (cURL)

```bash
curl -X POST http://localhost:8001/api/mosip/send \
  -H "Content-Type: application/json" \
  -d '{
    "extracted_fields": {
      "Name": "John Smith",
      "Date of Birth": "01/01/1990",
      "Nationality": "American"
    },
    "extracted_metadata": {
      "trocr_confidence": {
        "Name": 0.95,
        "Date of Birth": 0.88,
        "Nationality": 0.91
      }
    }
  }' | jq '.'
```

### Example 4: Change Language (Python)

```python
import requests

response = requests.post(
    "http://localhost:8001/api/set-language",
    data={"language": "ar"}
)

result = response.json()
print(f"Language changed to: {result['language']}")
print(f"App Title: {result['translations']['app_title']}")
```

---

## API Versioning

**Current Version:** v1.0

**Future Versioning Strategy:**
- URL-based: `/api/v2/upload`
- Header-based: `Accept: application/vnd.ocr.v2+json`

---

## Webhooks (Planned)

Future versions will support webhooks for async processing:

```json
{
  "webhook_url": "https://your-server.com/webhook",
  "events": ["ocr_complete", "verification_complete"]
}
```

---

## SDK Support (Planned)

Official SDKs planned for:
- Python
- JavaScript/TypeScript
- Java
- C#

---

**API Version:** 1.0  
**Last Updated:** November 30, 2024  
**Maintained By:** Development Team
