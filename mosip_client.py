"""
MOSIP Client - Handles communication with MOSIP Pre-Registration API
Supports both MOCK mode (for testing) and REAL mode (for production)
"""

import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from config import (
    MOSIP_ENABLED,
    MOSIP_BASE_URL,
    MOSIP_PREREG_URL,
    MOSIP_CLIENT_ID,
    MOSIP_CLIENT_SECRET,
    MOSIP_TIMEOUT
)


class MosipClient:
    """Client for MOSIP Pre-Registration API"""
    
    def __init__(self, mock_mode=True):
        """
        Initialize MOSIP client
        
        Args:
            mock_mode: If True, use mock responses. If False, call real MOSIP API
        """
        self.mock_mode = mock_mode or not MOSIP_ENABLED
        self.base_url = MOSIP_BASE_URL
        self.prereg_url = MOSIP_PREREG_URL
        self.token = None
        
    def authenticate(self) -> bool:
        """
        Authenticate with MOSIP and get access token
        
        Returns:
            bool: True if authentication successful
        """
        if self.mock_mode:
            self.token = "mock_token_12345"
            return True
            
        # Real MOSIP authentication
        try:
            auth_data = {
                "clientId": MOSIP_CLIENT_ID,
                "secretKey": MOSIP_CLIENT_SECRET,
                "appId": "prereg"
            }
            
            response = requests.post(
                f"{self.base_url}/v1/authmanager/authenticate/clientidsecretkey",
                json=auth_data,
                timeout=MOSIP_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get("response", {}).get("token")
                return self.token is not None
                
        except Exception as e:
            print(f"MOSIP authentication failed: {e}")
            
        return False
    
    def create_application(self, demographic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new pre-registration application
        
        Args:
            demographic_data: Dictionary containing demographic information
            
        Returns:
            dict: Response with preRegistrationId and status
        """
        if self.mock_mode:
            return self._mock_create_application(demographic_data)
        
        # Real MOSIP API call
        if not self.token:
            self.authenticate()
            
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "id": "mosip.pre-registration.demographic.create",
                "version": "1.0",
                "requesttime": datetime.utcnow().isoformat(),
                "request": {
                    "langCode": "eng",
                    "demographicDetails": demographic_data
                }
            }
            
            response = requests.post(
                f"{self.prereg_url}/applications",
                json=payload,
                headers=headers,
                timeout=MOSIP_TIMEOUT
            )
            
            if response.status_code in [200, 201]:
                return response.json()
                
        except Exception as e:
            print(f"MOSIP application creation failed: {e}")
            
        return {"success": False, "error": "Failed to create application"}
    
    def _mock_create_application(self, demographic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock implementation for testing"""
        prid = str(uuid.uuid4())[:16].upper()  # Generate mock PRID
        
        return {
            "id": "mosip.pre-registration.demographic.create",
            "version": "1.0",
            "responsetime": datetime.utcnow().isoformat(),
            "response": {
                "preRegistrationId": prid,
                "createdBy": "OCR_SYSTEM",
                "createdDateTime": datetime.utcnow().isoformat(),
                "langCode": "eng",
                "demographicDetails": demographic_data,
                "statusCode": "Pending_Appointment"
            },
            "errors": None
        }
    
    def book_appointment(self, prid: str, registration_center_id: str, 
                        appointment_date: str, time_slot_from: str, 
                        time_slot_to: str) -> Dict[str, Any]:
        """
        Book appointment for a pre-registration
        
        Args:
            prid: Pre-registration ID
            registration_center_id: Registration center ID
            appointment_date: Appointment date (YYYY-MM-DD format)
            time_slot_from: Start time (HH:MM format)
            time_slot_to: End time (HH:MM format)
            
        Returns:
            dict: Booking response
        """
        if self.mock_mode:
            return self._mock_book_appointment(prid, appointment_date, time_slot_from)
        
        # Real MOSIP booking
        if not self.token:
            self.authenticate()
            
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "id": "mosip.pre-registration.booking.book",
                "version": "1.0",
                "requesttime": datetime.utcnow().isoformat(),
                "request": {
                    "registration_center_id": registration_center_id,
                    "appointment_date": appointment_date,
                    "time_slot_from": time_slot_from,
                    "time_slot_to": time_slot_to
                }
            }
            
            response = requests.post(
                f"{self.prereg_url}/appointment/{prid}",
                json=payload,
                headers=headers,
                timeout=MOSIP_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"MOSIP appointment booking failed: {e}")
            
        return {"success": False, "error": "Failed to book appointment"}
    
    def _mock_book_appointment(self, prid: str, appointment_date: str, 
                               time_slot_from: str) -> Dict[str, Any]:
        """Mock implementation for appointment booking"""
        return {
            "id": "mosip.pre-registration.booking.book",
            "version": "1.0",
            "responsetime": datetime.utcnow().isoformat(),
            "response": {
                "bookingMessage": "Appointment booked successfully",
                "preRegistrationId": prid,
                "appointment_date": appointment_date,
                "time_slot_from": time_slot_from
            },
            "errors": None
        }
    
    def get_application(self, prid: str) -> Optional[Dict[str, Any]]:
        """
        Get application details
        
        Args:
            prid: Pre-registration ID
            
        Returns:
            dict: Application details or None
        """
        if self.mock_mode:
            return self._mock_get_application(prid)
        
        # Real MOSIP API call
        if not self.token:
            self.authenticate()
            
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(
                f"{self.prereg_url}/applications/{prid}",
                headers=headers,
                timeout=MOSIP_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            print(f"MOSIP get application failed: {e}")
            
        return None
    
    def _mock_get_application(self, prid: str) -> Dict[str, Any]:
        """Mock implementation for get application"""
        return {
            "response": {
                "preRegistrationId": prid,
                "statusCode": "Booked",
                "langCode": "eng"
            }
        }
