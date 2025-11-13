"""
Advanced OCR Verification Engine
Validates and verifies structured data extracted from scanned documents
"""
import re
import json
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher

class OCRVerifier:
    """Advanced OCR Verification System"""
    
    # Common OCR misrecognitions
    OCR_MISRECOGNITIONS = {
        '0': 'O', 'O': '0',
        '1': 'I', 'I': '1',
        '5': 'S', 'S': '5',
        '8': 'B', 'B': '8',
        '6': 'G', 'G': '6',
        'Z': '2', '2': 'Z',
        'D': '0', 'Q': 'O'
    }
    
    # Field type mappings
    FIELD_TYPES = {
        'name': ['name', 'full name', 'first name', 'last name', 'surname', 'given name'],
        'dob': ['dob', 'date of birth', 'birthdate', 'birth date', 'date_of_birth'],
        'mobile': ['mobile', 'phone', 'phone number', 'contact', 'mobile number', 'telephone'],
        'email': ['email', 'e-mail', 'email address', 'mail'],
        'id_number': ['id', 'id number', 'aadhaar', 'pan', 'passport', 'driving license', 'license number', 'card number'],
        'address': ['address', 'residence', 'location', 'street', 'city', 'state', 'country'],
        'gender': ['gender', 'sex'],
        'pincode': ['pincode', 'pin code', 'postal code', 'zip code', 'zip']
    }
    
    def __init__(self):
        self.verification_report = []
        self.cleaned_data = {}
        self.issues_found = []
    
    def normalize_field_name(self, field_name: str) -> str:
        """Normalize field name to standard format"""
        field_lower = field_name.lower().strip()
        for standard, variants in self.FIELD_TYPES.items():
            if field_lower in variants or any(v in field_lower for v in variants):
                return standard
        return field_lower.replace(' ', '_').replace('-', '_')
    
    def detect_ocr_errors(self, text: str) -> List[str]:
        """Detect common OCR errors"""
        issues = []
        
        if not text or len(text.strip()) == 0:
            issues.append("Empty or missing value")
            return issues
        
        # Check for suspicious character patterns
        if re.search(r'[Il1]{3,}', text):
            issues.append("Possible misrecognized characters (I/l/1)")
        
        if re.search(r'[O0]{3,}', text):
            issues.append("Possible misrecognized characters (O/0)")
        
        # Check for mixed case inconsistencies
        if text.isupper() and len(text) > 10:
            issues.append("All uppercase - may indicate OCR processing")
        
        # Check for excessive whitespace
        if '  ' in text or '\n' in text:
            issues.append("Excessive whitespace detected")
        
        # Check for special characters in names
        if re.search(r'[^a-zA-Z\s\.\-\']', text) and 'name' in text.lower():
            issues.append("Unexpected characters in name field")
        
        return issues
    
    def correct_ocr_errors(self, text: str, field_type: str) -> Tuple[str, List[str]]:
        """Attempt to correct common OCR errors"""
        corrected = text.strip()
        corrections = []
        
        # Remove excessive whitespace
        corrected = re.sub(r'\s+', ' ', corrected)
        
        # Common corrections based on field type
        if field_type == 'name':
            # Remove numbers from names
            if re.search(r'\d', corrected):
                corrected = re.sub(r'\d', '', corrected)
                corrections.append("Removed numbers from name")
            # Capitalize properly
            corrected = ' '.join(word.capitalize() for word in corrected.split())
        
        elif field_type == 'mobile':
            # Remove non-digit characters
            digits_only = re.sub(r'\D', '', corrected)
            if len(digits_only) == 10:
                corrected = digits_only
                corrections.append("Cleaned mobile number")
        
        elif field_type == 'email':
            # Fix common email errors
            corrected = corrected.lower()
            if '@' not in corrected and '.' in corrected:
                # Try to fix missing @
                parts = corrected.split('.')
                if len(parts) == 2:
                    corrected = f"{parts[0]}@{parts[1]}"
                    corrections.append("Fixed missing @ in email")
        
        elif field_type == 'dob':
            # Normalize date formats
            date_patterns = [
                (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', r'\1/\2/\3'),
                (r'(\d{2})(\d{2})(\d{4})', r'\1/\2/\3')
            ]
            for pattern, replacement in date_patterns:
                if re.search(pattern, corrected):
                    corrected = re.sub(pattern, replacement, corrected)
                    corrections.append("Normalized date format")
                    break
        
        return corrected, corrections
    
    def validate_field_format(self, field_name: str, value: str) -> Tuple[bool, str, Optional[str]]:
        """Validate field format based on field type"""
        field_type = self.normalize_field_name(field_name)
        value = str(value).strip()
        
        if not value:
            return False, "missing", "Field is empty"
        
        # Name validation
        if field_type == 'name':
            if re.search(r'\d', value):
                return False, "mismatch", "Name contains numbers"
            if len(value) < 2:
                return False, "mismatch", "Name too short"
            if not re.match(r'^[a-zA-Z\s\.\-\']+$', value):
                return False, "mismatch", "Invalid characters in name"
            return True, "correct", None
        
        # Date of Birth validation
        elif field_type == 'dob':
            date_patterns = [
                r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',
                r'^\d{2}[/-]\d{2}[/-]\d{4}$',
                r'^\d{4}[/-]\d{2}[/-]\d{2}$'
            ]
            for pattern in date_patterns:
                if re.match(pattern, value):
                    return True, "correct", None
            return False, "mismatch", "Invalid date format (expected DD/MM/YYYY)"
        
        # Mobile validation
        elif field_type == 'mobile':
            digits = re.sub(r'\D', '', value)
            if len(digits) == 10:
                return True, "correct", None
            elif len(digits) > 10:
                return False, "mismatch", f"Mobile number has {len(digits)} digits (expected 10)"
            else:
                return False, "mismatch", f"Mobile number has {len(digits)} digits (expected 10)"
        
        # Email validation
        elif field_type == 'email':
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if re.match(email_pattern, value):
                return True, "correct", None
            return False, "mismatch", "Invalid email format"
        
        # ID Number validation
        elif field_type == 'id_number':
            if len(value) < 8:
                return False, "mismatch", "ID number too short"
            if re.match(r'^[A-Z0-9]{8,}$', value.upper()):
                return True, "correct", None
            return False, "mismatch", "Invalid ID number format"
        
        # Address validation
        elif field_type == 'address':
            if len(value) < 10:
                return False, "mismatch", "Address too short"
            return True, "correct", None
        
        # Gender validation
        elif field_type == 'gender':
            if value.lower() in ['male', 'female', 'm', 'f', 'other']:
                return True, "correct", None
            return False, "mismatch", f"Invalid gender value: {value}"
        
        # Default: just check if not empty
        return True, "correct", None
    
    def verify_field(self, field_name: str, ocr_value: str, original_value: Optional[str] = None) -> Dict:
        """Verify a single field"""
        field_type = self.normalize_field_name(field_name)
        
        # Detect OCR errors
        ocr_issues = self.detect_ocr_errors(ocr_value)
        
        # Correct OCR errors
        corrected_value, corrections = self.correct_ocr_errors(ocr_value, field_type)
        
        # Validate format
        format_valid, format_status, format_issue = self.validate_field_format(field_name, corrected_value)
        
        # Compare with original if provided
        match_status = None
        confidence = "medium"
        similarity_score = None
        
        if original_value:
            original_str = str(original_value).strip().lower()
            corrected_str = corrected_value.strip().lower()
            similarity_score = SequenceMatcher(None, corrected_str, original_str).ratio()
            
            if similarity_score > 0.95:
                match_status = "correct"
                confidence = "high"
            elif similarity_score > 0.8:
                match_status = "corrected"
                confidence = "high"
            elif similarity_score > 0.6:
                match_status = "mismatch"
                confidence = "medium"
            else:
                match_status = "mismatch"
                confidence = "low"
        else:
            # No original to compare, use format validation
            if format_valid:
                match_status = "correct"
                confidence = "medium"
            else:
                match_status = "mismatch"
                confidence = "low"
        
        # Determine final status
        if match_status == "correct" and format_valid:
            final_status = "correct"
        elif corrections or (match_status == "corrected"):
            final_status = "corrected"
        elif not format_valid or match_status == "mismatch":
            final_status = "mismatch"
        else:
            final_status = "correct"
        
        # Collect issues
        all_issues = ocr_issues + ([format_issue] if format_issue else [])
        if corrections:
            all_issues.extend([f"Correction: {c}" for c in corrections])
        
        return {
            "field": field_name,
            "field_type": field_type,
            "ocr_value": ocr_value,
            "corrected_value": corrected_value,
            "original_value": original_value,
            "status": final_status,
            "confidence": confidence,
            "similarity_score": round(similarity_score * 100, 2) if similarity_score else None,
            "format_valid": format_valid,
            "issues": all_issues if all_issues else None
        }
    
    def verify_all_fields(self, structured_data: Dict, original_data: Optional[Dict] = None, ocr_text_block: Optional[str] = None) -> Dict:
        """Verify all fields in structured data"""
        self.verification_report = []
        self.cleaned_data = {}
        self.issues_found = []
        
        for field_name, ocr_value in structured_data.items():
            original_value = original_data.get(field_name) if original_data else None
            
            verification_result = self.verify_field(field_name, str(ocr_value), original_value)
            self.verification_report.append(verification_result)
            
            # Add to cleaned data
            self.cleaned_data[field_name] = verification_result["corrected_value"]
            
            # Collect issues
            if verification_result["issues"]:
                self.issues_found.extend(verification_result["issues"])
        
        # Determine overall status
        statuses = [r["status"] for r in self.verification_report]
        correct_count = statuses.count("correct")
        corrected_count = statuses.count("corrected")
        mismatch_count = statuses.count("mismatch")
        total_count = len(statuses)
        
        if mismatch_count == 0 and corrected_count == 0:
            overall_status = "PASS"
        elif mismatch_count == 0:
            overall_status = "PASS WITH CORRECTIONS"
        elif mismatch_count < total_count / 2:
            overall_status = "PASS WITH CORRECTIONS"
        else:
            overall_status = "FAIL"
        
        return {
            "cleaned_data": self.cleaned_data,
            "verification_report": self.verification_report,
            "overall_verification_status": overall_status,
            "summary": {
                "total_fields": total_count,
                "correct": correct_count,
                "corrected": corrected_count,
                "mismatch": mismatch_count,
                "issues_found": len(self.issues_found)
            }
        }

