"""
Data Cleaner and Validator Module
Post-processes OCR extraction results to remove noise, validate fields, and clean up data
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime


class DataCleaner:
    """
    Cleans and validates OCR extracted data
    """
    
    # Common OCR noise patterns to filter out
    GARBAGE_PATTERNS = [
        r'^[^a-zA-Z0-9\s]{3,}$',  # Only special characters
        r'^\?+$',  # Only question marks
        r'^[^\w\s]{1,3}$',  # 1-3 non-word characters
        r'^[A-Z0-9]{1,2}[^A-Za-z0-9\s]{2,}[A-Z0-9]{1,2}$',  # Garbage like "W419404T"
        r'^[A-Z]\s*[^a-zA-Z0-9]{1,3}\s*$',  # Like "G  /" or "A  :"
    ]
    
    # Field labels that might be extracted as values
    FIELD_LABELS_TO_REMOVE = [
        r'of parents at the time of birth of the child:?',
        r'address of parents',
        r'permanent address of parents',
        r'name of (father|mother):?',
        r'date of (birth|registration|issue):?',
        r'registration no\.?:?',
        r'certificate no\.?:?',
        r'place of (birth|issue):?',
        r'district:?',
        r'pin code:?',
        r'religion:?',
        r'sex:?',
        r'gender:?',
    ]
    
    # Minimum lengths for different field types
    MIN_LENGTHS = {
        'Name': 3,
        'Father Name': 3,
        'Mother Name': 3,
        'Address': 10,
        'Place of Birth': 3,
        'Place of Issue': 3,
        'District': 3,
        'Religion': 3,
    }
    
    # Phone validation patterns
    VALID_PHONE_PATTERN = r'^[+]?[\d\s\-()]{8,15}$'
    
    # Date patterns
    DATE_PATTERNS = [
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
    ]
    
    def __init__(self):
        pass
    
    def is_garbage(self, value: str) -> bool:
        """
        Check if a value is OCR garbage/noise
        """
        if not value or len(value.strip()) == 0:
            return True
        
        # Check against garbage patterns
        for pattern in self.GARBAGE_PATTERNS:
            if re.match(pattern, value.strip()):
                return True
        
        # Very short values (1-2 chars) are likely garbage unless they're valid codes
        if len(value.strip()) <= 2 and not value.strip().isdigit():
            return True
        
        return False
    
    def is_field_label(self, value: str) -> bool:
        """
        Check if the value is actually a field label, not data
        """
        value_lower = value.lower().strip()
        
        for pattern in self.FIELD_LABELS_TO_REMOVE:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False
    
    def validate_phone(self, phone: str) -> bool:
        """
        Validate if a string is a valid phone number
        """
        if not phone:
            return False
        
        # Remove spaces for validation
        clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Reject 12-digit numbers - those are Aadhaar, not phone!
        if len(clean_phone) == 12 and clean_phone.isdigit():
            return False
        
        # Reject 16-digit numbers - those are VID, not phone!
        if len(clean_phone) == 16 and clean_phone.isdigit():
            return False
        
        # Phone should be 8-15 digits (but not 12 or 16)
        if not re.match(r'^[+]?\d{8,15}$', clean_phone):
            return False
        
        # If it's too long (>15 digits), it's likely OCR error
        if len(clean_phone) > 15:
            return False
        
        return True
    
    def validate_date(self, date_str: str) -> bool:
        """
        Validate if a string is a valid date
        """
        if not date_str:
            return False
        
        # Check if it matches date pattern
        matches_pattern = any(re.match(pattern, date_str) for pattern in self.DATE_PATTERNS)
        
        if not matches_pattern:
            return False
        
        # Try to parse it
        date_formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d', '%d-%m-%y', '%d/%m/%y']
        for fmt in date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except:
                continue
        
        return False
    
    def clean_address(self, address: str) -> Optional[str]:
        """
        Clean and validate address field
        """
        if not address:
            return None
        
        # Remove field labels if they're present (but keep the actual address data)
        cleaned = address
        for pattern in self.FIELD_LABELS_TO_REMOVE:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = cleaned.strip().strip(':').strip('-').strip().strip(',').strip()
        
        # If after removing labels, there's still meaningful data, keep it
        # Otherwise if it was ONLY a label with no data, reject it
        if len(cleaned) < 10:
            # Check if the original was ONLY a field label
            if self.is_field_label(address) and len(cleaned) < 5:
                return None
            # If we have some data but less than 10 chars, it might still be valid
            # (like "Gaya" for a city/district)
            if len(cleaned) >= 3:
                return cleaned
            return None
        
        return cleaned
    
    def clean_name(self, name: str, field_type: str = 'Name') -> Optional[str]:
        """
        Clean and validate name fields
        """
        if not name or self.is_field_label(name):
            return None
        
        # Remove common OCR artifacts
        cleaned = name.strip()
        
        # Reject institutional/header text that's not a person's name
        institutional_words = [
            'government', 'india', 'republic', 'bharath', 'bharat',
            'ministry',  'department', 'office', 'directorate',
            'governmentofindia', 'republicofindia', 'भारत', 'सरकार'
        ]
        
        name_lower = cleaned.lower().replace(' ', '')
        if any(word in name_lower for word in institutional_words):
            return None
        
        # Name should have at least 2 characters
        min_len = self.MIN_LENGTHS.get(field_type, 3)
        if len(cleaned) < min_len:
            return None
        
        # Name should contain at least one letter
        if not re.search(r'[a-zA-Z]', cleaned):
            return None
        
        return cleaned
    
    def clean_district(self, district: str) -> Optional[str]:
        """
        Clean district field - often gets partial words like 'rict'
        """
        if not district:
            return None
        
        # If it's a partial word, try common fixes
        partial_fixes = {
            'rict': 'District',  # This is a label, not a value
            'dist': 'District',  # This is also a label
        }
        
        district_lower = district.lower().strip()
        
        # If it's just a partial label, return None
        if district_lower in partial_fixes:
            return None
        
        # Clean it
        cleaned = district.strip()
        
        # District should be at least 3 characters
        if len(cleaned) < 3:
            return None
        
        return cleaned
    
    def extract_place_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Try to extract place information from address or other fields
        For birth certificates, often "Place of Birth" and "Address" contain similar info
        """
        # Look for address with district info
        address = data.get('Address', '')
        
        if address and 'Dist-' in address or 'District' in address:
            # Try to extract district from address
            district_match = re.search(r'Dist[-.:\s]*([A-Z][a-z]+)', address, re.IGNORECASE)
            if district_match and not data.get('District'):
                data['District'] = district_match.group(1)
        
        return data
    
    def clean_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to clean extracted OCR data
        """
        cleaned_data = {}
        
        for field, value in raw_data.items():
            # Skip if value is None or empty
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
            
            # Convert to string if needed
            if not isinstance(value, str):
                value = str(value)
            
            # Check if it's garbage
            if self.is_garbage(value):
                continue
            
            # Check if it's a field label
            if self.is_field_label(value):
                continue
            
            # Field-specific cleaning
            if 'Name' in field:
                cleaned_value = self.clean_name(value, field)
            elif field == 'Address' or 'Address' in field:
                cleaned_value = self.clean_address(value)
            elif field == 'District':
                cleaned_value = self.clean_district(value)
            elif field == 'Phone' or field == 'Mobile':
                if not self.validate_phone(value):
                    continue  # Skip invalid phone numbers
                cleaned_value = value
            elif 'Date' in field:
                if not self.validate_date(value):
                    continue  # Skip invalid dates
                cleaned_value = value
            else:
                # General cleaning
                cleaned_value = value.strip()
            
            # Only add if the cleaned value is valid
            if cleaned_value and len(cleaned_value) > 0:
                cleaned_data[field] = cleaned_value
        
        # Try to extract place info from addresses
        cleaned_data = self.extract_place_info(cleaned_data)
        
        return cleaned_data
    
    def get_quality_score(self, cleaned_data: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate data quality metrics
        """
        total_fields = len(original_data)
        cleaned_fields = len(cleaned_data)
        removed_fields = total_fields - cleaned_fields
        
        return {
            'total_extracted': total_fields,
            'valid_fields': cleaned_fields,
            'removed_fields': removed_fields,
            'quality_percentage': round((cleaned_fields / total_fields * 100) if total_fields > 0 else 0, 2),
            'removed_field_names': list(set(original_data.keys()) - set(cleaned_data.keys()))
        }


# Singleton instance
data_cleaner = DataCleaner()


# Convenience functions
def clean_ocr_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean OCR extracted data"""
    return data_cleaner.clean_data(raw_data)


def get_data_quality(cleaned_data: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
    """Get data quality metrics"""
    return data_cleaner.get_quality_score(cleaned_data, original_data)
