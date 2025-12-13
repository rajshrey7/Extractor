# Architectural Design Document
## MOSIP Pre-Registration OCR System

**Version:** 2.0.0  
**Date:** December 13, 2025  
**Status:** Production Ready

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [Data Flow Architecture](#4-data-flow-architecture)
5. [Technology Stack](#5-technology-stack)
6. [Design Patterns](#6-design-patterns)
7. [Security Architecture](#7-security-architecture)
8. [Integration Architecture](#8-integration-architecture)

---

## 1. Executive Summary

### 1.1 System Overview

The MOSIP Pre-Registration OCR System is an enterprise-grade solution that combines:
- **OCR Document Processing** — Multi-engine text extraction (PaddleOCR, TrOCR)
- **MOSIP Pre-Registration UI** — Complete Angular-based identity registration portal
- **Mock Backend Services** — FastAPI backend simulating all MOSIP APIs

**Key Capabilities:**
- Multi-engine OCR with confidence scoring
- Complete MOSIP Pre-Registration workflow
- Support for 3 languages (English, Arabic, French)
- OCR-to-form auto-fill integration
- Quality-based document assessment
- Appointment booking and management

### 1.2 Design Principles

1. **Modularity** — Loosely coupled Angular components and Python modules
2. **Extensibility** — Plugin architecture for OCR engines and languages
3. **Mock-First Development** — Complete backend simulation for offline development
4. **Performance** — Asynchronous processing and lazy model loading
5. **Maintainability** — Clean code, comprehensive logging, documentation

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                          │
├─────────────────────────────────┬──────────────────────────────────────┤
│     OCR Extraction UI           │    MOSIP Pre-Registration UI          │
│     (index.html)                │    (Angular 7)                        │
│     Port: 8001                  │    Port: 4200                         │
│                                 │                                       │
│  ┌──────────────────────────┐   │   ┌─────────────────────────────┐    │
│  │ • Document Upload        │   │   │ • Login/OTP Authentication  │    │
│  │ • OCR Processing         │   │   │ • Demographic Form          │    │
│  │ • Quality Analysis       │   │   │ • Document Upload           │    │
│  │ • Field Correction       │   │   │ • Appointment Booking       │    │
│  │ • MOSIP Packet Creation  │   │   │ • Application Management    │    │
│  └──────────────────────────┘   │   └─────────────────────────────┘    │
├─────────────────────────────────┴──────────────────────────────────────┤
│                           BACKEND SERVICES LAYER                        │
│                            FastAPI (Port 8001)                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │  OCR Services   │  │  MOSIP Mock     │  │  Data Processing        │ │
│  │                 │  │  APIs           │  │                         │ │
│  │  • PaddleOCR    │  │                 │  │  • Verification         │ │
│  │  • TrOCR        │  │  • Auth/Login   │  │  • Data Cleaning        │ │
│  │  • Parser       │  │  • Applications │  │  • Field Mapping        │ │
│  │  • Quality      │  │  • Booking      │  │  • Confidence Score     │ │
│  │                 │  │  • Documents    │  │                         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘ │
│                                                                         │
├────────────────────────────────────────────────────────────────────────┤
│                           DATA STORAGE LAYER                            │
├─────────────────┬──────────────────┬───────────────────────────────────┤
│  uploads/       │  mock_packets/   │  In-Memory Store                  │
│  (Images/PDFs)  │  (MOSIP Packets) │  (Applications, Sessions)         │
└─────────────────┴──────────────────┴───────────────────────────────────┘
```

### 2.2 Component Interaction

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Browser    │──────▶│   Angular    │──────▶│   FastAPI    │
│   (User)     │◀──────│   (4200)     │◀──────│   (8001)     │
└──────────────┘       └──────────────┘       └──────────────┘
                              │                      │
                              ▼                      ▼
                       ┌──────────────┐       ┌──────────────┐
                       │  OCR Data    │       │  OCR Engine  │
                       │  Service     │       │  (Paddle/    │
                       │  (Angular)   │       │   TrOCR)     │
                       └──────────────┘       └──────────────┘
```

---

## 3. Component Design

### 3.1 Frontend Components (Angular)

#### 3.1.1 Core Services

| Service | Responsibility |
|---------|---------------|
| `DataStorageService` | API communication with backend |
| `ConfigService` | Application configuration management |
| `OcrDataService` | OCR data sharing between components |
| `RegistrationService` | Pre-registration state management |
| `BookingService` | Appointment booking logic |

#### 3.1.2 Feature Modules

| Module | Components |
|--------|------------|
| **Demographic** | Form generation, auto-fill, validation |
| **File Upload** | Document upload, OCR integration |
| **Booking** | Center selection, time slots, calendar |
| **Summary** | Preview, confirmation, status display |

#### 3.1.3 OCR Integration Component

```typescript
// OCR Integration Architecture
OcrIntegrationComponent
├── Opens OCR tool (localhost:8001) in iframe/popup
├── Receives extracted data via postMessage
├── Maps OCR fields to MOSIP schema
└── Triggers form auto-fill via OcrDataService
```

### 3.2 Backend Components (Python)

#### 3.2.1 FastAPI Application (`app.py`)

**Responsibilities:**
- HTTP request handling (OCR + MOSIP APIs)
- File upload processing
- Static file serving (index.html, uploads)
- CORS middleware for cross-origin requests

**Key Endpoints:**

| Category | Endpoints |
|----------|-----------|
| OCR | `/api/upload`, `/api/verify` |
| Auth | `/preregistration/v1/login/*` |
| Applications | `/preregistration/v1/applications/*` |
| Booking | `/preregistration/v1/appointment/*` |
| Master Data | `/preregistration/v1/proxy/masterdata/*` |

#### 3.2.2 OCR Processing Module

```
OCR Processing Pipeline
│
├── PaddleOCR (paddle_ocr_module.py)
│   ├── Printed text extraction
│   ├── Bounding box detection
│   └── Confidence per detection
│
├── TrOCR (trocr_handwritten.py)
│   ├── Handwritten text recognition
│   ├── Line-level processing
│   └── Transformer-based model
│
├── Parser (app.py)
│   ├── Field extraction (Name, DOB, etc.)
│   ├── Key-value normalization
│   └── Confidence mapping
│
└── Quality Scorer (quality_score.py)
    ├── Blur detection (Laplacian variance)
    ├── Brightness analysis
    └── Overall quality score
```

#### 3.2.3 MOSIP Mock Services

```python
# Mock Data Storage
mosip_applications = {}  # In-memory application store
mosip_appointments = {}  # In-memory appointment store

# Key Mock Endpoints
/preregistration/v1/config          → Configuration values
/preregistration/v1/uispec/latest   → Form field definitions
/preregistration/v1/applications/*  → CRUD for applications
/preregistration/v1/appointment/*   → Booking management
```

#### 3.2.4 Field Mapper (`mosip_field_mapper.py`)

Maps OCR-extracted fields to MOSIP identity schema:

```python
MOSIP_SCHEMA = {
    "fullName": ["name", "full_name", "full name"],
    "fatherName": ["father", "father_name", "father's name"],
    "motherName": ["mother", "mother_name", "mother's name"],
    "dateOfBirth": ["dob", "date_of_birth", "birth_date"],
    "gender": ["sex", "gender"],
    "phone": ["mobile", "phone_number"],
    "email": ["email", "email_address"],
    "addressLine1": ["address", "address_line_1"],
    "postalCode": ["pin", "pin_code", "postal_code"],
    "referenceIdentityNumber": ["aadhaar", "pan", "id_number"]
}
```

---

## 4. Data Flow Architecture

### 4.1 OCR Extraction Flow

```
1. User uploads document (index.html)
          │
          ▼
2. FastAPI receives file (/api/upload)
          │
          ▼
3. Quality Assessment (quality_score.py)
          │
          ├── Quality < 70% → Return warning, suggest retake
          │
          ▼
4. OCR Processing
          │
          ├── PaddleOCR → Printed text
          ├── TrOCR → Handwritten text (optional)
          │
          ▼
5. Field Parsing (parse_text_to_json_advanced)
          │
          ├── Key-value extraction
          ├── Normalization
          ├── Confidence mapping
          │
          ▼
6. Response with extracted fields + confidence
```

### 4.2 Pre-Registration Flow

```
1. User logs in (OTP validation)
          │
          ▼
2. Create/Edit Application
          │
          ├── Manual form entry
          │       OR
          ├── OCR Auto-fill (via OcrDataService)
          │
          ▼
3. Demographic Form Submission
          │
          ├── Frontend: createIdentityJSONDynamic()
          ├── Creates identity object with all fields
          ├── PUT /preregistration/v1/applications/prereg/{prid}
          │
          ▼
4. Document Upload (optional)
          │
          ▼
5. Appointment Booking
          │
          ├── Select registration center
          ├── Choose date/time slot
          │
          ▼
6. Preview & Confirmation
```

### 4.3 OCR to Form Auto-Fill Flow

```
┌─────────────────┐     postMessage     ┌─────────────────────────┐
│  OCR Tool       │ ─────────────────▶  │  Angular App            │
│  (index.html)   │                     │  (OcrIntegrationComponent)
│                 │                     │           │              │
│  Extracts:      │                     │           ▼              │
│  • Name         │                     │  OcrDataService          │
│  • Father Name  │                     │           │              │
│  • Mother Name  │                     │           ▼              │
│  • DOB          │                     │  DemographicComponent    │
│  • Address      │                     │           │              │
│                 │                     │           ▼              │
│                 │                     │  autoFillFromOCR()       │
│                 │                     │           │              │
│                 │                     │           ▼              │
│                 │                     │  Form fields populated   │
└─────────────────┘                     └─────────────────────────┘
```

---

## 5. Technology Stack

### 5.1 Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Core language |
| **FastAPI** | Latest | Web framework |
| **Uvicorn** | Latest | ASGI server |
| **PaddlePaddle** | Latest | OCR engine |
| **PaddleOCR** | Latest | OCR wrapper |
| **PyTorch** | 2.x | Deep learning |
| **Transformers** | ≥4.30 | TrOCR model |
| **OpenCV** | Latest | Image processing |
| **Pillow** | Latest | Image manipulation |
| **PyMuPDF** | Latest | PDF processing |

### 5.2 Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Angular** | 7.2 | Frontend framework |
| **Node.js** | 12.x ONLY | Runtime (Angular 7 requirement) |
| **TypeScript** | 3.2 | Language |
| **Angular Material** | 7.x | UI components |
| **RxJS** | 6.x | Reactive programming |
| **ngx-translate** | 10.x | Internationalization |
| **Moment.js** | Latest | Date handling |

### 5.3 Infrastructure

| Component | Details |
|-----------|---------|
| **Backend Port** | 8001 |
| **Frontend Port** | 4200 |
| **Storage** | Local file system |
| **Cache** | In-memory dictionaries |
| **Protocol** | HTTP (HTTPS for production) |

---

## 6. Design Patterns

### 6.1 Architectural Patterns

| Pattern | Usage |
|---------|-------|
| **Layered Architecture** | Clear separation of UI, business logic, data |
| **RESTful API** | Resource-based URLs, HTTP methods |
| **Mock-First** | Backend simulation for frontend development |
| **Component-Based** | Angular modular architecture |

### 6.2 Code-Level Patterns

| Pattern | Location | Usage |
|---------|----------|-------|
| **Strategy** | OCR modules | Multiple OCR engine support |
| **Factory** | Language support | Translation loading |
| **Adapter** | Field mapper | OCR → MOSIP schema |
| **Singleton** | OCR engines | Single instance per engine |
| **Observer** | RxJS services | Data change notifications |
| **Dependency Injection** | Angular services | Service composition |

---

## 7. Security Architecture

### 7.1 Security Measures

| Layer | Measures |
|-------|----------|
| **Input Validation** | File type verification, size limits |
| **CORS** | Configured origins for cross-domain requests |
| **Data Sanitization** | Regex-based cleaning, XSS prevention |
| **Error Handling** | Generic error messages, no sensitive data |

### 7.2 Authentication (Mock Mode)

- OTP-based login (accepts any 6-digit code)
- Session management via localStorage
- Token invalidation on logout

### 7.3 Data Privacy

- Local processing (no external data transmission except optional MOSIP)
- Temporary file storage
- No PII logging

---

## 8. Integration Architecture

### 8.1 Frontend-Backend Integration

```
Angular App (4200)
      │
      │  HTTP Requests
      │  - CORS enabled
      │  - JSON payloads
      │  - Multipart for files
      ▼
FastAPI Backend (8001)
```

### 8.2 OCR-Form Integration

```
OCR Tool (8001/index.html)
      │
      │  postMessage API
      │  - Origin validation
      │  - JSON data transfer
      ▼
Angular (OcrIntegrationComponent)
      │
      │  OcrDataService
      │  - BehaviorSubject
      │  - Field mapping
      ▼
DemographicComponent (autoFillFromOCR)
```

### 8.3 MOSIP Server Integration (Production)

When `MOSIP_ENABLED=True`:

```
FastAPI Mock APIs
      │
      │  Replaced by
      ▼
Real MOSIP Server
      │
      │  - Authentication (OAuth2)
      │  - Real application storage
      │  - Actual appointment booking
      ▼
MOSIP Pre-Registration Backend
```

---

## Appendix A: System Metrics

**Code Statistics:**
- Python Code: ~10,000 lines
- TypeScript Code: ~25,000 lines
- API Endpoints: 50+
- Angular Components: 30+
- Supported Languages: 3 (EN, AR, FR)

**Performance Benchmarks:**
- OCR Processing: 2-5 seconds
- Form Auto-fill: <100ms
- API Response: <200ms
- Quality Assessment: <100ms

---

**Document Version:** 2.0.0  
**Last Updated:** December 13, 2025
**Approved By:** Development Team
