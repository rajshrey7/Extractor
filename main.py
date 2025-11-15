"""
Enhanced FastAPI Main Application
Integrates all new features including MOSIP, quality scoring, multi-engine OCR
"""

import os
import io
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from dotenv import load_dotenv
import jwt
from passlib.context import CryptContext

# Import our modules
from integrations.mosip_client import MosipClient, MosipConfig, PreRegistrationRequest, RegistrationRequest
from utils.capture_quality import analyze_capture_quality
from extractor_core.multi_engine_ocr import MultiEngineOCR

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Extractor API with MOSIP Integration",
    description="Document extraction, OCR, quality scoring, and MOSIP integration",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize services
ocr_engine = MultiEngineOCR({
    'google_vision_api_key': os.getenv('GOOGLE_VISION_API_KEY')
})

# MOSIP client initialization
mosip_config = MosipConfig(
    base_url=os.getenv('MOSIP_BASE_URL', 'http://localhost:7000'),
    client_id=os.getenv('MOSIP_CLIENT_ID', 'test-client'),
    secret=os.getenv('MOSIP_SECRET', 'test-secret'),
    tenant=os.getenv('MOSIP_TENANT', 'default'),
    mode=os.getenv('MOSIP_MODE', 'mock')
)
mosip_client = None


# Request/Response Models
class QualityCheckRequest(BaseModel):
    image_type: str = "document"  # document, face, id_card


class FormExtractRequest(BaseModel):
    document_data: Dict[str, Any]
    form_fields: List[str]


class FormSubmitRequest(BaseModel):
    form_data: Dict[str, Any]
    pre_registration: bool = False
    registration: bool = False


class OCRAnnotateRequest(BaseModel):
    document_id: Optional[str] = None


# Authentication
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            os.getenv('JWT_SECRET', 'your-jwt-secret-key-change-in-production'),
            algorithms=[os.getenv('JWT_ALGORITHM', 'HS256')]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_api_key(api_key: str):
    """Verify API key"""
    expected_key = os.getenv('API_KEY', 'dev-api-key')
    if api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Extractor API",
        "version": "2.0.0",
        "features": [
            "Multi-engine OCR",
            "Quality scoring",
            "MOSIP integration",
            "Multi-page PDF support",
            "Confidence heatmaps",
            "Form auto-fill with verification"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "ocr": "ready",
            "mosip": "ready" if mosip_client else "not_configured",
            "quality_check": "ready"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/quality")
@limiter.limit("3/second")
async def check_quality(
    request: Request,
    file: UploadFile = File(...),
    image_type: str = Form("document")
):
    """Check image quality and return scores with suggestions"""
    try:
        # Read image data
        image_data = await file.read()
        
        # Analyze quality
        result = analyze_capture_quality(image_data, image_type)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Quality check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ocr")
async def process_ocr(
    file: UploadFile = File(...),
    use_google_vision: bool = Form(False)
):
    """Process single file with OCR"""
    try:
        # Read file data
        file_data = await file.read()
        
        # Process with OCR
        result = await ocr_engine.process_document(
            file_bytes=file_data,
            file_type='auto'
        )
        
        return JSONResponse(content={
            "success": True,
            "document_id": result.document_id,
            "pages": result.pages,
            "merged_fields": result.merged_fields,
            "quality": result.quality,
            "raw_text": result.raw_text,
            "total_pages": result.total_pages,
            "processing_time": result.processing_time,
            "engines_used": result.engines_used
        })
        
    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ocr/multi")
async def process_multi_ocr(
    files: List[UploadFile] = File(...)
):
    """Process multiple files or multi-page documents"""
    try:
        results = []
        
        for file in files:
            file_data = await file.read()
            result = await ocr_engine.process_document(
                file_bytes=file_data,
                file_type='auto'
            )
            results.append({
                "filename": file.filename,
                "document_id": result.document_id,
                "pages": result.pages,
                "merged_fields": result.merged_fields,
                "quality": result.quality,
                "total_pages": result.total_pages
            })
            
        # Merge all results
        all_pages = []
        all_fields = {}
        
        for r in results:
            all_pages.extend(r['pages'])
            all_fields.update(r['merged_fields'])
            
        return JSONResponse(content={
            "success": True,
            "documents": results,
            "merged_data": {
                "pages": all_pages,
                "merged_fields": all_fields,
                "total_documents": len(results),
                "total_pages": sum(r['total_pages'] for r in results)
            }
        })
        
    except Exception as e:
        logger.error(f"Multi-OCR processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ocr/annotate")
async def get_ocr_annotations(
    file: UploadFile = File(...)
):
    """Get OCR results with confidence zones and heatmap"""
    try:
        # Read file data
        file_data = await file.read()
        
        # Process with OCR
        result = await ocr_engine.process_document(
            file_bytes=file_data,
            file_type='auto'
        )
        
        # Prepare annotated response
        annotations = []
        for page in result.pages:
            annotations.append({
                "page": page['page'],
                "regions": page['regions'],
                "heatmap": page['heatmap'],
                "fields": page['fields']
            })
            
        return JSONResponse(content={
            "success": True,
            "document_id": result.document_id,
            "annotations": annotations,
            "quality": result.quality
        })
        
    except Exception as e:
        logger.error(f"OCR annotation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/form/extract")
async def extract_form_fields(
    request: FormExtractRequest,
    token: dict = Depends(verify_token)
):
    """Extract and match form fields from document data"""
    try:
        document_data = request.document_data
        form_fields = request.form_fields
        
        # Match fields
        matches = {}
        for field in form_fields:
            field_lower = field.lower().replace('_', ' ')
            
            # Check merged fields
            for doc_field, value in document_data.get('merged_fields', {}).items():
                if field_lower in doc_field.lower() or doc_field.lower() in field_lower:
                    matches[field] = {
                        "value": value.get('value') if isinstance(value, dict) else value,
                        "confidence": value.get('confidence', 0.8) if isinstance(value, dict) else 0.8,
                        "match_rate": 0.9,
                        "edit_token": f"edit_{field}_{datetime.utcnow().timestamp()}"
                    }
                    break
                    
        return JSONResponse(content={
            "success": True,
            "fields": matches,
            "match_summary": {
                "total_fields": len(form_fields),
                "matched_fields": len(matches),
                "match_rate": len(matches) / len(form_fields) if form_fields else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Form extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/form/submit")
async def submit_form_to_mosip(
    request: FormSubmitRequest,
    background_tasks: BackgroundTasks,
    token: dict = Depends(verify_token)
):
    """Submit verified form data to MOSIP"""
    global mosip_client
    
    try:
        # Initialize MOSIP client if not already done
        if not mosip_client:
            mosip_client = MosipClient(mosip_config)
            await mosip_client.authenticate()
            
        response_data = {
            "success": True,
            "form_data": request.form_data
        }
        
        # Pre-registration if requested
        if request.pre_registration:
            pre_reg_data = PreRegistrationRequest(
                firstName=request.form_data.get('first_name', ''),
                lastName=request.form_data.get('last_name', ''),
                dateOfBirth=request.form_data.get('date_of_birth', ''),
                gender=request.form_data.get('gender', 'Other'),
                phone=request.form_data.get('phone', ''),
                addressLine1=request.form_data.get('address', ''),
                city=request.form_data.get('city', 'Unknown'),
                postalCode=request.form_data.get('postal_code', '00000')
            )
            
            pre_reg_result = await mosip_client.pre_register(pre_reg_data)
            response_data['pre_registration'] = pre_reg_result
            
        # Full registration if requested
        if request.registration:
            reg_data = RegistrationRequest(
                preRegId=response_data.get('pre_registration', {}).get('preRegId'),
                biometricData={},
                demographicData=request.form_data,
                deviceInfo={"type": "web", "id": "web-client"}
            )
            
            reg_result = await mosip_client.register(reg_data)
            response_data['registration'] = reg_result
            
            # Schedule status check
            if reg_result.get('registrationId'):
                background_tasks.add_task(
                    check_registration_status,
                    reg_result['registrationId']
                )
                
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Form submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mosip/status/{registration_id}")
async def get_mosip_status(
    registration_id: str,
    token: dict = Depends(verify_token)
):
    """Get MOSIP registration status"""
    global mosip_client
    
    try:
        if not mosip_client:
            mosip_client = MosipClient(mosip_config)
            await mosip_client.authenticate()
            
        status = await mosip_client.get_registration_status(registration_id)
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/android/device/register")
async def register_android_device(
    device_info: Dict[str, Any]
):
    """Register Android device for MOSIP integration"""
    global mosip_client
    
    try:
        if not mosip_client:
            mosip_client = MosipClient(mosip_config)
            await mosip_client.authenticate()
            
        result = await mosip_client.android_device_register(device_info)
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Device registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/android/sync")
async def sync_android_data(
    sync_data: Dict[str, Any]
):
    """Sync data from Android client"""
    global mosip_client
    
    try:
        if not mosip_client:
            mosip_client = MosipClient(mosip_config)
            await mosip_client.authenticate()
            
        result = await mosip_client.android_sync_data(sync_data)
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Data sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task
async def check_registration_status(registration_id: str):
    """Background task to check registration status"""
    global mosip_client
    
    try:
        if mosip_client:
            # Wait a bit before checking
            await asyncio.sleep(5)
            status = await mosip_client.get_registration_status(registration_id)
            logger.info(f"Registration {registration_id} status: {status}")
            
    except Exception as e:
        logger.error(f"Background status check error: {e}")


# Generate JWT token for testing
@app.post("/api/auth/token")
async def generate_token(
    api_key: str = Form(...)
):
    """Generate JWT token for API access"""
    try:
        verify_api_key(api_key)
        
        payload = {
            "sub": "api_user",
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(
            payload,
            os.getenv('JWT_SECRET', 'your-jwt-secret-key-change-in-production'),
            algorithm=os.getenv('JWT_ALGORITHM', 'HS256')
        )
        
        return JSONResponse(content={
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 86400
        })
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", 9000)),
        reload=True
    )