# 🔍 Advanced OCR Verification System Guide

## Overview

The Advanced OCR Verification System validates and verifies structured data extracted from scanned documents (ID cards, forms, certificates, applications, etc.) with intelligent error detection and correction.

## Features

### 1️⃣ OCR Data Accuracy Verification

- **Semantic Understanding**: Compares OCR-extracted text with expected field meaning
- **Error Detection**: Identifies:
  - Spelling mistakes
  - Formatting errors
  - Missing values
  - Swapped fields
  - Incomplete extraction
  - Blurred text indicators
  - Partially cropped text
  - Misrecognized characters (O/0, I/1, B/8, etc.)

### 2️⃣ Field Format Validation

Strict validation rules for each field type:

| Field Type | Validation Rules |
|-----------|------------------|
| **Name** | Only alphabets, no numbers/symbols |
| **DOB** | DD/MM/YYYY or standard date formats |
| **Mobile** | 10 digits, no letters |
| **Email** | Valid email pattern |
| **ID Numbers** | Must match expected format (Aadhaar, PAN, driving license, etc.) |
| **Addresses** | Not empty, no nonsensical tokens |
| **Gender** | Valid values (male/female/M/F/other) |

### 3️⃣ Source Document Matching

- Confirms each field exists in the original text block
- Highlights mismatches and confidence issues
- Suggests corrected values

### 4️⃣ Output Structure

Returns three main components:

#### A. Cleaned & Verified Data (JSON)
- Corrected formatting
- Normalized values
- Trimmed whitespaces
- Corrected spelling where possible

#### B. Verification Report (JSON)
For each field:
```json
{
  "field": "name",
  "field_type": "name",
  "ocr_value": "J0HN D0E",
  "corrected_value": "John Doe",
  "original_value": "John Doe",
  "status": "corrected",
  "confidence": "high",
  "similarity_score": 95.5,
  "format_valid": true,
  "issues": ["Possible misrecognized characters (O/0)", "Correction: Removed numbers from name"]
}
```

#### C. Final Decision
```json
{
  "overall_verification_status": "PASS" | "PASS WITH CORRECTIONS" | "FAIL"
}
```

## How to Use

### Via Web Interface

1. Go to the **Verify Data** tab
2. Enter **Structured Data (JSON)** - OCR extracted data:
   ```json
   {
     "name": "J0HN D0E",
     "dob": "01/01/1990",
     "mobile": "1234567890",
     "email": "john@example.com",
     "id_number": "ABCD123456"
   }
   ```
3. (Optional) Enter **Original Data (JSON)** - Reference data for comparison
4. (Optional) Enter **OCR Text Block** - Raw OCR text
5. Click **🔍 Verify & Validate Data**

### Via API

**Endpoint**: `POST /api/verify`

**Request**:
```json
{
  "extracted_data": "{\"name\": \"J0HN D0E\", \"dob\": \"01/01/1990\"}",
  "original_data": "{\"name\": \"John Doe\", \"dob\": \"01/01/1990\"}",
  "ocr_text_block": "Optional raw OCR text"
}
```

**Response**:
```json
{
  "success": true,
  "cleaned_data": {
    "name": "John Doe",
    "dob": "01/01/1990"
  },
  "verification_report": [
    {
      "field": "name",
      "ocr_value": "J0HN D0E",
      "corrected_value": "John Doe",
      "status": "corrected",
      "confidence": "high",
      "similarity_score": 95.5,
      "format_valid": true,
      "issues": ["Possible misrecognized characters (O/0)"]
    }
  ],
  "overall_verification_status": "PASS WITH CORRECTIONS",
  "summary": {
    "total_fields": 2,
    "correct": 1,
    "corrected": 1,
    "mismatch": 0,
    "issues_found": 1
  }
}
```

## Status Values

- **correct**: Field is valid and matches original (if provided)
- **corrected**: Field was corrected but is now valid
- **mismatch**: Field has format issues or doesn't match original
- **missing**: Field is empty

## Confidence Levels

- **high**: >95% similarity or format perfectly valid
- **medium**: 60-95% similarity or minor format issues
- **low**: <60% similarity or major format issues

## Overall Verification Status

- **PASS**: All fields correct, no issues
- **PASS WITH CORRECTIONS**: Some fields corrected but all valid
- **FAIL**: Multiple mismatches or critical errors

## Example Use Cases

### Example 1: Name Correction
**Input**:
```json
{"name": "J0HN D0E"}
```

**Output**:
- OCR Value: `J0HN D0E`
- Corrected: `John Doe`
- Status: `corrected`
- Issues: `["Possible misrecognized characters (O/0)", "Removed numbers from name"]`

### Example 2: Date Format Validation
**Input**:
```json
{"dob": "1990-01-01"}
```

**Output**:
- OCR Value: `1990-01-01`
- Corrected: `01/01/1990`
- Status: `corrected`
- Format Valid: `true`

### Example 3: Mobile Number Validation
**Input**:
```json
{"mobile": "123-456-7890"}
```

**Output**:
- OCR Value: `123-456-7890`
- Corrected: `1234567890`
- Status: `corrected`
- Format Valid: `true`

## Tips for Best Results

1. **Provide Original Data**: For best accuracy, provide original/reference data
2. **Include OCR Text Block**: Helps with context-aware validation
3. **Use Standard Field Names**: System auto-detects field types (name, dob, mobile, email, etc.)
4. **Check Issues**: Review the issues list for detailed problem descriptions
5. **Use Cleaned Data**: Always use the `cleaned_data` output for further processing

## Field Type Detection

The system automatically detects field types based on field names:
- `name`, `full name`, `first name`, `last name` → **name**
- `dob`, `date of birth`, `birthdate` → **dob**
- `mobile`, `phone`, `phone number` → **mobile**
- `email`, `e-mail` → **email**
- `id`, `id number`, `aadhaar`, `pan`, `passport` → **id_number**
- `address`, `residence`, `location` → **address**
- `gender`, `sex` → **gender**

## Error Detection Capabilities

The system detects:
- ✅ Character misrecognitions (O/0, I/1, B/8, etc.)
- ✅ Format inconsistencies
- ✅ Missing or empty values
- ✅ Invalid characters in fields
- ✅ Date format issues
- ✅ Email format problems
- ✅ Mobile number format errors
- ✅ Excessive whitespace
- ✅ All uppercase text (OCR indicator)

