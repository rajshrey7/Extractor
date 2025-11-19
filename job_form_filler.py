"""
Job Form Filler - Integrated with OCR System
Automatically fills job application forms using OCR extracted data or resume information
"""
import json
import re
import logging
import os
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Any, Tuple, Union
from config import OPENROUTER_API_KEY, OPENROUTER_MODELS, DEFAULT_MODEL, SELECTED_LANGUAGE
from language_support import LanguageLoader

# Initialize Language Loader
language_loader = LanguageLoader(SELECTED_LANGUAGE)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add Auto-Job-Form-Filler-Agent to path to use original modules
_agent_path = os.path.join(os.path.dirname(__file__), 'Auto-Job-Form-Filler-Agent')
GoogleFormHandler = None

# Try to import GoogleFormHandler if the module exists
if os.path.exists(_agent_path):
    if _agent_path not in sys.path:
        sys.path.insert(0, _agent_path)
    
    try:
        from google_form_handler import GoogleFormHandler
    except ImportError:
        # Fallback: try importing with explicit path
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "google_form_handler",
                os.path.join(_agent_path, "google_form_handler.py")
            )
            if spec and spec.loader:
                google_form_handler = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(google_form_handler)
                GoogleFormHandler = google_form_handler.GoogleFormHandler
        except Exception as e:
            logger.warning(f"Failed to load GoogleFormHandler: {e}")
            GoogleFormHandler = None

@dataclass
class FieldMatch:
    """Represents a match between a form field and extracted data"""
    field_name: str
    field_value: Any
    confidence: float
    source: str  # 'direct', 'alias', 'fuzzy', 'inferred'
    field_type: str = 'text'
    required: bool = False


class JobFormFiller:
    """
    Intelligent job form filler using OCR extracted data
    
    Features:
    - Field matching with confidence scoring
    - Support for multiple field types
    - Alias detection for common field names
    - Required field validation
    - Data type validation and formatting
    """
    
    # Job application field mappings with weights
    JOB_FIELD_ALIASES = {
        "name": {
            "aliases": ["full name", "first name", "last name", "surname", "given name", "applicant name"],
            "type": "text",
            "required": True,
            "weight": 1.0
        },
        "email": {
            "aliases": ["email address", "e-mail", "email", "contact email"],
            "type": "email",
            "required": True,
            "weight": 1.0,
            "validation": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        },
        "phone": {
            "aliases": ["phone", "mobile", "telephone", "phone number", "mobile number", "contact number"],
            "type": "tel",
            "required": True,
            "weight": 0.9
        },
        "address": {
            "aliases": ["address", "residence", "location", "street address", "home address"],
            "type": "text",
            "required": True,
            "weight": 0.8
        },
        "city": {
            "aliases": ["city", "town"],
            "type": "text",
            "required": True,
            "weight": 0.7
        },
        "state": {
            "aliases": ["state", "province", "region"],
            "type": "text",
            "required": True,
            "weight": 0.7
        },
        "zip": {
            "aliases": ["zip code", "postal code", "pincode", "zip"],
            "type": "text",
            "required": True,
            "weight": 0.7
        },
        "country": {
            "aliases": ["country", "nation"],
            "type": "text",
            "required": True,
            "weight": 0.7
        },
        "date_of_birth": {
            "aliases": ["dob", "birthdate", "date of birth", "birth date"],
            "type": "date",
            "required": True,
            "weight": 0.8
        },
        "education": {
            "aliases": ["education", "qualification", "degree", "university", "college", "school"],
            "type": "text",
            "required": False,
            "weight": 0.6
        },
        "experience": {
            "aliases": ["experience", "work experience", "employment", "job history", "career"],
            "type": "text",
            "required": False,
            "weight": 0.7
        },
        "skills": {
            "aliases": ["skills", "technical skills", "competencies", "abilities"],
            "type": "text",
            "required": False,
            "weight": 0.5
        },
        "resume": {
            "aliases": ["resume", "cv", "curriculum vitae"],
            "type": "file",
            "required": True,
            "weight": 0.9
        },
        "cover_letter": {
            "aliases": ["cover letter", "motivation letter"],
            "type": "file",
            "required": False,
            "weight": 0.4
        },
        "linkedin": {
            "aliases": ["linkedin", "linkedin profile", "linkedin url"],
            "type": "url",
            "required": False,
            "weight": 0.3,
            "validation": r'(https?:\/\/)?(www\.)?linkedin\.com\/in\/.*'
        },
        "website": {
            "aliases": ["website", "portfolio", "personal website"],
            "type": "url",
            "required": False,
            "weight": 0.3
        },
        "availability": {
            "aliases": ["availability", "start date", "when can you start"],
            "type": "date",
            "required": False,
            "weight": 0.5
        },
        "salary": {
            "aliases": ["salary", "expected salary", "compensation", "pay"],
            "type": "number",
            "required": False,
            "weight": 0.4
        },
        "references": {
            "aliases": ["references", "referees", "reference contacts"],
            "type": "text",
            "required": False,
            "weight": 0.3
        },
        "Date": {
            "aliases": ["Date", "Today's Date", "Current Date", "Date of Application"],
            "type": "date",
            "required": False,
            "weight": 0.5
        }
    }
    
    def get_job_field_aliases(self):
        """Get job field aliases based on current language"""
        return language_loader.get_job_field_aliases()
    
    def __init__(self):
        self.form_handler = None
        self.field_aliases = self.get_job_field_aliases()
    
    def match_field_to_data(self, question_text: str, extracted_data: Dict[str, Any], threshold: float = 0.5) -> Optional[tuple]:
        """
        Match a form question to extracted data
        
        Returns:
            (field_key, value, confidence) or None
        """
        question_lower = question_text.lower().strip()
        best_match = None
        best_score = 0
        
        # Normalize extracted data keys (handle various formats from OCR)
        normalized_data = {}
        for key, value in extracted_data.items():
            if value and str(value).strip():  # Only include non-empty values
                # Normalize key
                key_normalized = key.lower().strip()
                normalized_data[key_normalized] = value
        
        # Direct field matching
        for field_key, field_value in normalized_data.items():
            field_key_lower = field_key.lower()
            
            # Check if question contains field key or vice versa
            if field_key_lower in question_lower or question_lower in field_key_lower:
                score = SequenceMatcher(None, field_key_lower, question_lower).ratio()
                if score > best_score:
                    best_score = score
                    best_match = (field_key, field_value, score)
            
            # Check aliases
            aliases_info = self.field_aliases.get(field_key_lower, {})
            aliases = aliases_info.get("aliases", [])
            for alias in aliases:
                if alias in question_lower or question_lower in alias:
                    score = SequenceMatcher(None, alias, question_lower).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = (field_key, field_value, score)
        
        # Semantic matching for common patterns (lower threshold for these)
        if not best_match or best_score < threshold:
            # Name matching
            if any(word in question_lower for word in ["name", "first", "last", "full", "surname"]):
                for key in ["name", "first name", "last name", "full name", "surname", "given name"]:
                    key_lower = key.lower()
                    if key_lower in normalized_data:
                        return (key_lower, normalized_data[key_lower], 0.9)
                    # Also check partial matches
                    for data_key in normalized_data:
                        if "name" in data_key:
                            return (data_key, normalized_data[data_key], 0.85)
            
            # Email matching
            if "email" in question_lower or "e-mail" in question_lower:
                for key in ["email", "email address", "e-mail"]:
                    key_lower = key.lower()
                    if key_lower in normalized_data:
                        return (key_lower, normalized_data[key_lower], 0.95)
                    # Check for email pattern in values
                    for data_key, data_value in normalized_data.items():
                        if "@" in str(data_value):
                            return (data_key, data_value, 0.9)
            
            # Phone matching
            if any(word in question_lower for word in ["phone", "mobile", "telephone", "contact", "number"]):
                for key in ["phone", "mobile", "phone number", "telephone", "contact number"]:
                    key_lower = key.lower()
                    if key_lower in normalized_data:
                        return (key_lower, normalized_data[key_lower], 0.9)
                    # Check for phone pattern
                    for data_key, data_value in normalized_data.items():
                        value_str = str(data_value).replace(" ", "").replace("-", "")
                        if value_str.isdigit() and len(value_str) >= 10:
                            return (data_key, data_value, 0.85)
            
            # Address matching
            if "address" in question_lower:
                for key in ["address", "street address", "home address", "residence"]:
                    key_lower = key.lower()
                    if key_lower in normalized_data:
                        return (key_lower, normalized_data[key_lower], 0.85)
            
            # Date of birth matching
            if any(word in question_lower for word in ["dob", "birth", "date of birth"]):
                for key in ["date of birth", "dob", "birthdate", "birth date"]:
                    key_lower = key.lower()
                    if key_lower in normalized_data:
                        return (key_lower, normalized_data[key_lower], 0.9)
        
        if best_score >= threshold:
            return best_match
        return None
    
    def fill_form_with_data(self, form_url: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill a Google Form with extracted data
        
        Returns:
            Dictionary with form questions and matched answers
        """
        if GoogleFormHandler is None:
            return {
                "success": False,
                "error": "Google Form Handler module not available. Please ensure Auto-Job-Form-Filler-Agent folder exists."
            }
        
        self.form_handler = GoogleFormHandler(url=form_url)
        questions_df = self.form_handler.get_form_questions_df(only_required=False)
        
        if questions_df.empty:
            return {
                "success": False,
                "error": "Could not parse form. Make sure the form is publicly accessible."
            }
        
        matches = {}
        used_fields = set()
        
        for _, row in questions_df.iterrows():
            question = row['Question']
            entry_id = row['Entry_ID']
            field_type = row['Field_Type']
            selection_type = row.get('Selection_Type')
            options = row.get('Options')
            
            # Try to match field
            match = self.match_field_to_data(question, extracted_data, threshold=0.5)
            
            if match:
                field_key, value, confidence = match
                
                # Handle different field types
                if selection_type in ["Single Choice", "Dropdown"]:
                    # For multiple choice, try to match value to options
                    if options:
                        option_list = [opt.strip() for opt in options.split(',')]
                        matched_option = self._match_to_options(str(value), option_list)
                        if matched_option:
                            matches[entry_id] = {
                                "question": question,
                                "answer": matched_option,
                                "matched_field": field_key,
                                "confidence": confidence,
                                "type": "option_match"
                            }
                        else:
                            matches[entry_id] = {
                                "question": question,
                                "answer": str(value),
                                "matched_field": field_key,
                                "confidence": confidence * 0.8,  # Lower confidence if option doesn't match
                                "type": "text_fallback"
                            }
                    else:
                        matches[entry_id] = {
                            "question": question,
                            "answer": str(value),
                            "matched_field": field_key,
                            "confidence": confidence,
                            "type": "direct_match"
                        }
                else:
                    # Text field
                    matches[entry_id] = {
                        "question": question,
                        "answer": str(value),
                        "matched_field": field_key,
                        "confidence": confidence,
                        "type": "direct_match"
                    }
                
                used_fields.add(field_key.lower())
            else:
                matches[entry_id] = {
                    "question": question,
                    "answer": None,
                    "matched_field": None,
                    "confidence": 0,
                    "type": "no_match"
                }
        
        # Prepare submission-ready data
        submission_data = {}
        display_data = {
            "answers": [],
            "summary": {}
        }
        
        for entry_id, match_info in matches.items():
            if match_info["answer"] is not None:
                # Format entry_id for submission (ensure it has 'entry.' prefix if needed)
                if not entry_id.startswith('entry.'):
                    submission_entry_id = f"entry.{entry_id}" if not entry_id.startswith('entry') else entry_id
                else:
                    submission_entry_id = entry_id
                
                submission_data[submission_entry_id] = match_info["answer"]
                
                # Add to display data
                display_data["answers"].append({
                    "entry_id": submission_entry_id,
                    "question": match_info["question"],
                    "answer": match_info["answer"],
                    "matched_field": match_info["matched_field"],
                    "confidence": round(match_info["confidence"], 2),
                    "type": match_info["type"]
                })
        
        # Calculate summary
        total_required = len(questions_df[questions_df["Required"] == True])
        matched_required = 0
        for entry_id, match_info in matches.items():
            if match_info["answer"] is not None:
                # Check if this entry is required
                entry_row = questions_df[questions_df["Entry_ID"] == entry_id]
                if len(entry_row) > 0 and entry_row.iloc[0]["Required"]:
                    matched_required += 1
        
        matched_count = len([m for m in matches.values() if m["answer"] is not None])
        unmatched_count = len([m for m in matches.values() if m["answer"] is None])
        
        display_data["summary"] = {
            "total_questions": len(questions_df),
            "matched_fields": matched_count,
            "unmatched_fields": unmatched_count,
            "total_required": total_required,
            "matched_required": matched_required,
            "match_rate": round(matched_count / len(questions_df) * 100, 1) if len(questions_df) > 0 else 0
        }
        
        return {
            "success": True,
            "form_url": form_url,
            "total_questions": len(questions_df),
            "matched_fields": len([m for m in matches.values() if m["answer"] is not None]),
            "matches": matches,
            "submission_data": submission_data,  # Ready for submission
            "display": display_data,  # For UI display
            "questions_df": questions_df.to_dict(orient="records")
        }
    
    def _match_to_options(self, value: str, options: List[str]) -> Optional[str]:
        """Match a value to the best option"""
        value_lower = value.lower().strip()
        best_match = None
        best_score = 0
        
        for option in options:
            option_lower = option.lower().strip()
            score = SequenceMatcher(None, value_lower, option_lower).ratio()
            if score > best_score and score > 0.7:
                best_score = score
                best_match = option
        
        return best_match
    
    def submit_filled_form(self, form_url: str, filled_data: Dict[str, str]) -> bool:
        """Submit filled form data"""
        if GoogleFormHandler is None:
            return False
        
        if not self.form_handler or self.form_handler.url != form_url:
            self.form_handler = GoogleFormHandler(url=form_url)
        
        return self.form_handler.submit_form(filled_data)
