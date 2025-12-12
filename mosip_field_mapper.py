import re
import difflib
from typing import Dict, Any, Optional

class MosipFieldMapper:
    """
    Maps OCR-extracted fields to the MOSIP ID Schema.
    """

    # MOSIP ID Schema Standard Fields (v1.2.0 based)
    MOSIP_SCHEMA = {
        "fullName": ["name", "full name", "given name", "applicant name", "candidate name"],
        "fatherName": ["father name", "father's name", "fathers name", "name of father", "father"],
        "motherName": ["mother name", "mother's name", "mothers name", "name of mother", "mother"],
        "dateOfBirth": ["dob", "date of birth", "birth date", "year of birth"],
        "gender": ["gender", "sex"],
        "placeOfBirth": ["place of birth", "birth place", "pob"],
        "addressLine1": ["address line 1", "address", "residence", "house no", "flat no", "permanent address", "present address"],
        "addressLine2": ["address line 2", "street", "road", "colony", "locality"],
        "city": ["city", "district", "town", "village"],
        "region": ["region", "state"],
        "province": ["province"],
        "postalCode": ["pin code", "pincode", "postal code", "zip code", "pin"],
        "phone": ["phone", "mobile", "contact number", "cell", "phone no", "mobile no"],
        "email": ["email", "e-mail", "mail id", "email id"],
        "referenceIdentityNumber": ["registration no", "certificate no", "aadhaar", "aadhaar no", "pan", "passport no", "id number"],
        "documentType": ["document type", "doc type"],
        "documentNumber": ["document no", "passport no", "id no", "card no", "identity no"],
    }

    def __init__(self, language: str = "eng"):
        self.language = language

    def map_to_mosip_schema(self, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a dictionary of OCR extracted fields to MOSIP schema fields.
        """
        mosip_data = {}
        
        # 1. Direct & Fuzzy Mapping
        for ocr_key, ocr_value in ocr_data.items():
            if not ocr_value:
                continue
                
            normalized_key = ocr_key.lower().strip()
            mapped_key = self._find_mosip_key(normalized_key)
            
            if mapped_key:
                # If we already have a value, we might want to decide which one is better.
                # For now, first match wins or we can implement priority.
                if mapped_key not in mosip_data:
                    mosip_data[mapped_key] = self._clean_value(mapped_key, ocr_value)
        
        # 2. Post-Processing / Formatting
        self._format_dates(mosip_data)
        self._format_gender(mosip_data)
        
        return mosip_data

    def map_metadata(self, ocr_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps a dictionary of OCR metadata (like confidence scores) to MOSIP schema fields.
        """
        mosip_metadata = {}
        
        for ocr_key, ocr_value in ocr_metadata.items():
            normalized_key = ocr_key.lower().strip()
            mapped_key = self._find_mosip_key(normalized_key)
            
            if mapped_key:
                # Store the metadata for the mapped key
                mosip_metadata[mapped_key] = ocr_value
                
        return mosip_metadata

    def _find_mosip_key(self, ocr_key: str) -> Optional[str]:
        """
        Finds the corresponding MOSIP key for a given OCR key using keyword matching and fuzzy logic.
        """
        # Exact/Keyword match
        for mosip_key, keywords in self.MOSIP_SCHEMA.items():
            if ocr_key in keywords:
                return mosip_key
            for keyword in keywords:
                if keyword in ocr_key:
                    return mosip_key
        
        # Fuzzy match
        all_keywords = []
        keyword_map = {}
        for mosip_key, keywords in self.MOSIP_SCHEMA.items():
            for k in keywords:
                all_keywords.append(k)
                keyword_map[k] = mosip_key
                
        matches = difflib.get_close_matches(ocr_key, all_keywords, n=1, cutoff=0.8)
        if matches:
            return keyword_map[matches[0]]
            
        return None

    def _clean_value(self, key: str, value: Any) -> Any:
        """
        Cleans and normalizes values based on the target field type.
        """
        if not isinstance(value, str):
            return value
            
        value = value.strip()
        
        if key == "email":
            return value.replace(" ", "").lower()
        if key == "phone":
            return re.sub(r"[^0-9+]", "", value)
        if key == "postalCode":
            return re.sub(r"[^0-9]", "", value)
            
        return value

    def _format_dates(self, data: Dict[str, Any]):
        """
        Standardizes date format to YYYY/MM/DD required by MOSIP.
        """
        if "dateOfBirth" in data:
            val = data["dateOfBirth"]
            # Try parsing common formats
            # DD/MM/YYYY
            match = re.search(r"(\d{1,2})[./-](\d{1,2})[./-](\d{4})", val)
            if match:
                d, m, y = match.groups()
                data["dateOfBirth"] = f"{y}/{m.zfill(2)}/{d.zfill(2)}"
                return

            # YYYY/MM/DD
            match = re.search(r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})", val)
            if match:
                y, m, d = match.groups()
                data["dateOfBirth"] = f"{y}/{m.zfill(2)}/{d.zfill(2)}"
                return
            
            # DD-MMM-YYYY (e.g., 01-JAN-2000) - Basic handling
            # Add more sophisticated parsing if needed (e.g. dateutil)

    def _format_gender(self, data: Dict[str, Any]):
        """
        Standardizes gender to MOSIP codes (MLE, FEM, TSP).
        """
        if "gender" in data:
            val = data["gender"].lower()
            if "m" in val or "male" in val:
                data["gender"] = "MLE"
            elif "f" in val or "female" in val:
                data["gender"] = "FEM"
            elif "t" in val or "trans" in val:
                data["gender"] = "TSP"
