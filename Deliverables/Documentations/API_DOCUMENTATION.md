# API Documentation
## MOSIP Pre-Registration OCR System

**Base URL (Backend):** `http://localhost:8001`  
**Base URL (Frontend):** `http://localhost:4200`  
**API Version:** 2.0  
**Protocol:** HTTP/HTTPS  
**Content Type:** `application/json`, `multipart/form-data`

---

## Table of Contents

1. [Overview](#overview)
2. [OCR Extraction APIs](#ocr-extraction-apis)
3. [MOSIP Pre-Registration APIs](#mosip-pre-registration-apis)
4. [Data Verification APIs](#data-verification-apis)
5. [Packet Management APIs](#packet-management-apis)
6. [Configuration APIs](#configuration-apis)
7. [Response Codes](#response-codes)
8. [Examples](#examples)

---

## Overview

This system provides two sets of APIs:

| API Set | Purpose | Port |
|---------|---------|------|
| **OCR APIs** | Document processing, text extraction, quality analysis | 8001 |
| **MOSIP Mock APIs** | Pre-registration workflow (login, applications, booking) | 8001 |

The Angular frontend (port 4200) consumes the MOSIP Mock APIs for the complete pre-registration experience.

---

## OCR Extraction APIs

### POST `/api/upload`

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
    "Father Name": "Robert Smith",
    "Date of Birth": "01/01/1990",
    "Gender": "Male",
    "Address": "123 Main St"
  },
  "trocr_confidence": {
    "Name": 0.976,
    "Father Name": 0.942,
    "Date of Birth": 0.883
  },
  "quality": {
    "overall": 95.2,
    "blur": 158.32,
    "brightness": 125.45,
    "recommendation": "Excellent quality - proceed"
  }
}
```

---

## MOSIP Pre-Registration APIs

### Authentication

#### POST `/preregistration/v1/login/sendOtp`

Send OTP for login.

**Request:**
```json
{
  "request": {
    "userId": "test@example.com"
  }
}
```

**Response:**
```json
{
  "response": {
    "message": "OTP sent successfully",
    "status": "true"
  },
  "errors": null
}
```

#### POST `/preregistration/v1/login/validateOtp`

Validate OTP (mock mode accepts any 6-digit OTP).

**Request:**
```json
{
  "request": {
    "userId": "test@example.com",
    "otp": "123456"
  }
}
```

**Response:**
```json
{
  "response": {
    "message": "OTP validated successfully",
    "status": "true"
  },
  "errors": null
}
```

#### POST `/preregistration/v1/login/invalidateToken`

Logout and invalidate session.

**Response:**
```json
{
  "response": {
    "message": "Token invalidated successfully"
  },
  "errors": null
}
```

---

### Configuration

#### GET `/preregistration/v1/config`

Get application configuration including languages, validation rules, and feature flags.

**Response:**
```json
{
  "response": {
    "mosip.supported-languages": "eng,ara,fra",
    "mosip.primary-language": "eng",
    "preregistration.identity.name": "fullName",
    "preregistration.documentupload.allowed.file.type": "application/pdf,image/jpeg,image/png",
    "preregistration.preview.fields": "fullName,fatherName,motherName,dateOfBirth,gender,phone,email"
  },
  "errors": null
}
```

#### GET `/preregistration/v1/uispec/latest`

Get UI specification for demographic form fields.

**Response:**
```json
{
  "response": {
    "jsonSpec": {
      "identity": {
        "identity": [
          {
            "id": "fullName",
            "inputRequired": true,
            "controlType": "textbox",
            "type": "simpleType",
            "required": true,
            "labelName": {"eng": "Full Name", "ara": "الاسم الكامل"}
          },
          {
            "id": "fatherName",
            "inputRequired": true,
            "controlType": "textbox",
            "labelName": {"eng": "Father's Name", "ara": "اسم الأب"}
          },
          {
            "id": "motherName",
            "inputRequired": true,
            "controlType": "textbox",
            "labelName": {"eng": "Mother's Name", "ara": "اسم الأم"}
          }
        ],
        "locationHierarchy": ["region", "province", "city"]
      }
    },
    "idSchemaVersion": "0.1"
  }
}
```

---

### Applications

#### GET `/preregistration/v1/applications/prereg`

List all pre-registration applications.

**Response:**
```json
{
  "response": {
    "basicDetails": [
      {
        "preRegistrationId": "1234567890",
        "statusCode": "Pending_Appointment",
        "demographicMetadata": {
          "fullName": [{"language": "eng", "value": "John Smith"}]
        }
      }
    ],
    "totalRecords": 1
  }
}
```

#### POST `/preregistration/v1/applications`

Create a new application.

**Response:**
```json
{
  "response": {
    "preRegistrationId": "ABCD12345678",
    "createdDateTime": "2024-12-12T00:00:00.000Z",
    "statusCode": "Pending_Appointment"
  }
}
```

#### GET `/preregistration/v1/applications/prereg/{prid}`

Get application details.

**Response:**
```json
{
  "response": {
    "preRegistrationId": "1234567890",
    "demographicDetails": {
      "identity": {
        "fullName": [{"language": "eng", "value": "John Smith"}],
        "fatherName": [{"language": "eng", "value": "Robert Smith"}],
        "motherName": [{"language": "eng", "value": "Mary Smith"}],
        "dateOfBirth": "1990/01/01",
        "gender": [{"language": "eng", "value": "Male"}],
        "phone": "0612345678",
        "email": "john@example.com"
      }
    }
  }
}
```

#### PUT `/preregistration/v1/applications/prereg/{prid}`

Update application demographic data.

**Request:**
```json
{
  "request": {
    "demographicDetails": {
      "identity": {
        "fullName": [{"language": "eng", "value": "Updated Name"}]
      }
    }
  }
}
```

#### DELETE `/preregistration/v1/applications/prereg/{prid}`

Delete an application.

---

### Booking

#### GET `/preregistration/v1/appointment/availability/{regCenterId}`

Get available appointment slots.

**Response:**
```json
{
  "response": {
    "availabilityDto": [
      {
        "date": "2024-12-15",
        "timeslots": [
          {
            "fromTime": "09:00",
            "toTime": "09:30",
            "availability": 10
          }
        ]
      }
    ]
  }
}
```

#### POST `/preregistration/v1/applications/appointment`

Book an appointment.

**Request:**
```json
{
  "request": {
    "preRegistrationId": "1234567890",
    "registrationCenterId": "10001",
    "appointment_date": "2024-12-15",
    "time_slot_from": "09:00",
    "time_slot_to": "09:30"
  }
}
```

#### PUT `/preregistration/v1/applications/appointment/{prid}`

Cancel an appointment.

---

## Data Verification APIs

### POST `/api/verify`

Verify and validate extracted OCR data.

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

**Response:**
```json
{
  "success": true,
  "overall_verification_status": "PASS",
  "cleaned_data": {
    "Name": "John Smith",
    "Email": "john@example.com"
  },
  "verification_report": [
    {
      "field": "Name",
      "status": "PASS",
      "confidence": 100,
      "match_percentage": 100
    }
  ],
  "summary": {
    "total_fields": 5,
    "passed_fields": 5,
    "overall_confidence": 97.8
  }
}
```

---

## Packet Management APIs

### POST `/api/mosip/send`

Create MOSIP registration packet from OCR data.

**Request:**
```json
{
  "extracted_fields": {
    "Name": "John Smith",
    "Father Name": "Robert Smith",
    "Date of Birth": "01/01/1990"
  },
  "extracted_metadata": {
    "trocr_confidence": {
      "Name": 0.95
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "packet_id": "PKT_20241212_001",
  "message": "Packet created successfully"
}
```

### GET `/api/mosip/packets`

List all created packets.

### GET `/api/mosip/packet/{packet_id}`

Get packet details.

---

## Response Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation failed |
| 500 | Internal Server Error | Server error |

---

## Examples

### Example 1: Complete Pre-Registration Flow (cURL)

```bash
# 1. Send OTP
curl -X POST http://localhost:8001/preregistration/v1/login/sendOtp \
  -H "Content-Type: application/json" \
  -d '{"request": {"userId": "test@example.com"}}'

# 2. Validate OTP
curl -X POST http://localhost:8001/preregistration/v1/login/validateOtp \
  -H "Content-Type: application/json" \
  -d '{"request": {"userId": "test@example.com", "otp": "123456"}}'

# 3. Create Application
curl -X POST http://localhost:8001/preregistration/v1/applications \
  -H "Content-Type: application/json"

# 4. Update with Demographic Data
curl -X PUT http://localhost:8001/preregistration/v1/applications/prereg/{prid} \
  -H "Content-Type: application/json" \
  -d '{"request": {"demographicDetails": {...}}}'
```

### Example 2: OCR with Auto-Fill (Python)

```python
import requests

# Extract from document
files = {"file": open("birth_certificate.jpg", "rb")}
response = requests.post(
    "http://localhost:8001/api/upload",
    files=files,
    data={"use_openai": "true", "use_trocr": "true"}
)
ocr_data = response.json()

# Extracted fields are automatically available in Angular form
# via OcrDataService when using the integrated workflow
print("Extracted:", ocr_data["extracted_fields"])
```

---

**API Version:** 2.0  
**Last Updated:** December 13, 2025
**Maintained By:** Development Team
