"""
MOSIP Integration Client
Provides adapter layer for MOSIP APIs including pre-registration, 
registration client, and Android registration client hooks.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import httpx
from pydantic import BaseModel, Field
import hashlib
import base64
import hmac
from functools import wraps

# Configure logging
logger = logging.getLogger(__name__)


class RegistrationStatus(Enum):
    """MOSIP Registration Status Enum"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class PreRegistrationRequest(BaseModel):
    """Pre-registration request model"""
    firstName: str
    lastName: str
    middleName: Optional[str] = None
    dateOfBirth: str  # Format: YYYY-MM-DD
    gender: str
    email: Optional[str] = None
    phone: str
    addressLine1: str
    addressLine2: Optional[str] = None
    city: str
    postalCode: str
    languageCode: str = "eng"
    documentType: Optional[str] = None
    documentNumber: Optional[str] = None


class RegistrationRequest(BaseModel):
    """Registration request model"""
    preRegId: Optional[str] = None
    biometricData: Dict[str, Any]  # Face, fingerprints, iris
    demographicData: Dict[str, Any]
    documentData: Optional[Dict[str, Any]] = None
    deviceInfo: Dict[str, Any]
    location: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BiometricCapture(BaseModel):
    """Biometric capture model"""
    type: str  # face, fingerprint, iris
    format: str  # ISO format
    data: str  # Base64 encoded
    qualityScore: float
    deviceId: str
    captureTime: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MosipConfig(BaseModel):
    """MOSIP Configuration"""
    base_url: str
    client_id: str
    secret: str
    tenant: str = "default"
    mode: str = "mock"  # mock or live
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 2


def retry_on_failure(max_retries: int = 3, delay: int = 2):
    """Decorator for retrying failed requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                        await asyncio.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator


class MosipClient:
    """MOSIP Integration Client"""
    
    def __init__(self, config: MosipConfig):
        """Initialize MOSIP client with configuration"""
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=config.timeout)
        self.auth_token = None
        self.token_expiry = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
        
    def _generate_signature(self, data: str) -> str:
        """Generate HMAC signature for request"""
        signature = hmac.new(
            self.config.secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode('utf-8')
        
    async def authenticate(self) -> str:
        """Authenticate with MOSIP and get auth token"""
        if self.config.mode == "mock":
            # Mock mode - return dummy token
            self.auth_token = "mock-auth-token-" + datetime.utcnow().isoformat()
            self.token_expiry = datetime.utcnow() + timedelta(hours=1)
            return self.auth_token
            
        # Live mode authentication
        auth_endpoint = f"{self.base_url}/v1/authmanager/authenticate"
        
        timestamp = datetime.utcnow().isoformat()
        auth_data = {
            "id": "mosip.auth.login",
            "version": "1.0",
            "requesttime": timestamp,
            "request": {
                "appId": self.config.client_id,
                "clientId": self.config.client_id,
                "secretKey": self.config.secret
            }
        }
        
        try:
            response = await self.client.post(
                auth_endpoint,
                json=auth_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                self.auth_token = result["response"]["token"]
                self.token_expiry = datetime.utcnow() + timedelta(hours=1)
                logger.info("Successfully authenticated with MOSIP")
                return self.auth_token
            else:
                raise Exception(f"Authentication failed: {result.get('errors', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise
            
    async def _ensure_authenticated(self):
        """Ensure we have a valid auth token"""
        if not self.auth_token or (self.token_expiry and datetime.utcnow() >= self.token_expiry):
            await self.authenticate()
            
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
        
    @retry_on_failure(max_retries=3)
    async def pre_register(self, data: PreRegistrationRequest) -> Dict[str, Any]:
        """Create pre-registration"""
        await self._ensure_authenticated()
        
        endpoint = f"{self.base_url}/preregistration/v1/applications"
        
        request_data = {
            "id": "mosip.pre-registration.create",
            "version": "1.0",
            "requesttime": datetime.utcnow().isoformat(),
            "request": {
                "langCode": data.languageCode,
                "demographicDetails": {
                    "identity": {
                        "fullName": [
                            {
                                "language": data.languageCode,
                                "value": f"{data.firstName} {data.middleName or ''} {data.lastName}".strip()
                            }
                        ],
                        "dateOfBirth": data.dateOfBirth,
                        "gender": [
                            {
                                "language": data.languageCode,
                                "value": data.gender
                            }
                        ],
                        "addressLine1": [
                            {
                                "language": data.languageCode,
                                "value": data.addressLine1
                            }
                        ],
                        "city": [
                            {
                                "language": data.languageCode,
                                "value": data.city
                            }
                        ],
                        "postalCode": data.postalCode,
                        "phone": data.phone,
                        "email": data.email
                    }
                }
            }
        }
        
        if data.documentType and data.documentNumber:
            request_data["request"]["demographicDetails"]["identity"]["referenceIdentityNumber"] = data.documentNumber
            
        try:
            response = await self.client.post(
                endpoint,
                json=request_data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                pre_reg_id = result["response"]["preRegistrationId"]
                logger.info(f"Pre-registration created: {pre_reg_id}")
                return {
                    "success": True,
                    "preRegId": pre_reg_id,
                    "status": "PENDING",
                    "createdAt": datetime.utcnow().isoformat(),
                    "data": result["response"]
                }
            else:
                errors = result.get("errors", [{"message": "Unknown error"}])
                raise Exception(f"Pre-registration failed: {errors}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during pre-registration: {e}")
            raise
        except Exception as e:
            logger.error(f"Pre-registration error: {str(e)}")
            raise
            
    @retry_on_failure(max_retries=3)
    async def update_pre_registration(self, pre_reg_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update pre-registration"""
        await self._ensure_authenticated()
        
        endpoint = f"{self.base_url}/preregistration/v1/applications/{pre_reg_id}"
        
        request_data = {
            "id": "mosip.pre-registration.update",
            "version": "1.0",
            "requesttime": datetime.utcnow().isoformat(),
            "request": data
        }
        
        try:
            response = await self.client.put(
                endpoint,
                json=request_data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                logger.info(f"Pre-registration updated: {pre_reg_id}")
                return {
                    "success": True,
                    "preRegId": pre_reg_id,
                    "updatedAt": datetime.utcnow().isoformat(),
                    "data": result["response"]
                }
            else:
                raise Exception(f"Update failed: {result.get('errors', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Update pre-registration error: {str(e)}")
            raise
            
    @retry_on_failure(max_retries=3)
    async def get_pre_registration(self, pre_reg_id: str) -> Dict[str, Any]:
        """Get pre-registration by ID"""
        await self._ensure_authenticated()
        
        endpoint = f"{self.base_url}/preregistration/v1/applications/{pre_reg_id}"
        
        try:
            response = await self.client.get(
                endpoint,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                return {
                    "success": True,
                    "preRegId": pre_reg_id,
                    "data": result["response"]
                }
            else:
                raise Exception(f"Get pre-registration failed: {result.get('errors', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Get pre-registration error: {str(e)}")
            raise
            
    @retry_on_failure(max_retries=3)
    async def register(self, data: RegistrationRequest) -> Dict[str, Any]:
        """Submit registration request"""
        await self._ensure_authenticated()
        
        endpoint = f"{self.base_url}/registrationprocessor/v1/registrationtransaction"
        
        # Generate RID (Registration ID)
        rid = self._generate_rid()
        
        request_data = {
            "id": "mosip.registration.create",
            "version": "1.0",
            "requesttime": data.timestamp,
            "request": {
                "registrationId": rid,
                "preRegistrationId": data.preRegId,
                "registrationType": "NEW",
                "packetCreationDate": data.timestamp,
                "demographicDetails": data.demographicData,
                "biometrics": data.biometricData,
                "documents": data.documentData,
                "deviceDetails": data.deviceInfo,
                "locationDetails": data.location
            }
        }
        
        try:
            response = await self.client.post(
                endpoint,
                json=request_data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                logger.info(f"Registration submitted: {rid}")
                return {
                    "success": True,
                    "registrationId": rid,
                    "status": RegistrationStatus.IN_PROGRESS.value,
                    "submittedAt": datetime.utcnow().isoformat(),
                    "data": result["response"]
                }
            else:
                raise Exception(f"Registration failed: {result.get('errors', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise
            
    @retry_on_failure(max_retries=3)
    async def submit_biometric_capture(self, capture: BiometricCapture) -> Dict[str, Any]:
        """Submit biometric capture reference"""
        await self._ensure_authenticated()
        
        endpoint = f"{self.base_url}/bioapi/v1/capture"
        
        request_data = {
            "id": "mosip.biometric.capture",
            "version": "1.0",
            "requesttime": capture.captureTime,
            "request": {
                "type": capture.type,
                "format": capture.format,
                "data": capture.data,
                "qualityScore": capture.qualityScore,
                "deviceId": capture.deviceId,
                "captureTime": capture.captureTime
            }
        }
        
        try:
            response = await self.client.post(
                endpoint,
                json=request_data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                capture_id = result["response"]["captureId"]
                logger.info(f"Biometric capture submitted: {capture_id}")
                return {
                    "success": True,
                    "captureId": capture_id,
                    "type": capture.type,
                    "qualityScore": capture.qualityScore,
                    "data": result["response"]
                }
            else:
                raise Exception(f"Biometric capture failed: {result.get('errors', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Biometric capture error: {str(e)}")
            raise
            
    @retry_on_failure(max_retries=3)
    async def get_registration_status(self, registration_id: str) -> Dict[str, Any]:
        """Poll registration status"""
        await self._ensure_authenticated()
        
        endpoint = f"{self.base_url}/registrationprocessor/v1/registrationstatus/{registration_id}"
        
        try:
            response = await self.client.get(
                endpoint,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                status_data = result["response"]
                status = status_data.get("registrationStatus", RegistrationStatus.PENDING.value)
                
                response_data = {
                    "success": True,
                    "registrationId": registration_id,
                    "status": status,
                    "statusMessage": status_data.get("statusMessage", ""),
                    "lastUpdated": status_data.get("lastUpdatedTime", datetime.utcnow().isoformat())
                }
                
                # Check if UIN is available
                if status == RegistrationStatus.COMPLETED.value:
                    response_data["uin"] = status_data.get("uin")
                    response_data["acknowledgement"] = status_data.get("acknowledgement")
                    
                return response_data
            else:
                raise Exception(f"Get status failed: {result.get('errors', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Get registration status error: {str(e)}")
            raise
            
    def _generate_rid(self) -> str:
        """Generate unique Registration ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = hashlib.md5(f"{timestamp}{self.config.client_id}".encode()).hexdigest()[:6].upper()
        return f"{self.config.tenant.upper()}{timestamp}{random_suffix}"
        
    # Android Registration Client Hooks
    async def android_device_register(self, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Register Android device for registration client"""
        await self._ensure_authenticated()
        
        endpoint = f"{self.base_url}/devicemanager/v1/devices/register"
        
        request_data = {
            "id": "mosip.device.register",
            "version": "1.0",
            "requesttime": datetime.utcnow().isoformat(),
            "request": {
                "deviceId": device_info.get("deviceId"),
                "deviceType": "ANDROID",
                "deviceSubType": device_info.get("model", "Unknown"),
                "certification": device_info.get("certification", "L0"),
                "deviceInfo": device_info
            }
        }
        
        try:
            response = await self.client.post(
                endpoint,
                json=request_data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                return {
                    "success": True,
                    "deviceId": device_info.get("deviceId"),
                    "registered": True,
                    "data": result["response"]
                }
            else:
                raise Exception(f"Device registration failed: {result.get('errors', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Android device registration error: {str(e)}")
            raise
            
    async def android_sync_data(self, sync_request: Dict[str, Any]) -> Dict[str, Any]:
        """Sync data from Android registration client"""
        await self._ensure_authenticated()
        
        endpoint = f"{self.base_url}/sync/v1/registrations"
        
        request_data = {
            "id": "mosip.sync.registration",
            "version": "1.0",
            "requesttime": datetime.utcnow().isoformat(),
            "request": sync_request
        }
        
        try:
            response = await self.client.post(
                endpoint,
                json=request_data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                return {
                    "success": True,
                    "syncId": result["response"].get("syncId"),
                    "synced": True,
                    "data": result["response"]
                }
            else:
                raise Exception(f"Data sync failed: {result.get('errors', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Android data sync error: {str(e)}")
            raise
            
    async def android_upload_packet(self, packet_data: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Upload registration packet from Android client"""
        await self._ensure_authenticated()
        
        endpoint = f"{self.base_url}/registrationprocessor/v1/packetreceiver/registrationpackets"
        
        files = {
            "file": ("packet.zip", packet_data, "application/zip")
        }
        
        data = {
            "metadata": json.dumps(metadata)
        }
        
        try:
            response = await self.client.post(
                endpoint,
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("response"):
                return {
                    "success": True,
                    "packetId": result["response"].get("packetId"),
                    "uploaded": True,
                    "data": result["response"]
                }
            else:
                raise Exception(f"Packet upload failed: {result.get('errors', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Android packet upload error: {str(e)}")
            raise


# Factory function for creating MOSIP client
def create_mosip_client(config_dict: Dict[str, Any]) -> MosipClient:
    """Create MOSIP client from configuration dictionary"""
    config = MosipConfig(**config_dict)
    return MosipClient(config)