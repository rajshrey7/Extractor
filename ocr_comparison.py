def compare_ocr_results(yolo_result, paddle_text):
    """
    Compare OCR results from YOLO+EasyOCR and PaddleOCR and return the best one.
    
    Args:
        yolo_result: Dict with extracted_fields and general_text from YOLO+EasyOCR
        paddle_text: String with full text from PaddleOCR
        
    Returns:
        Dict with best result and comparison details
    """
    # Extract YOLO text
    yolo_fields = yolo_result.get("extracted_fields", {})
    yolo_general = yolo_result.get("general_text", [])
    
    # Combine YOLO text for comparison
    yolo_all_text = " ".join(str(v) for v in yolo_fields.values())
    yolo_all_text += " " + " ".join(yolo_general)
    yolo_all_text = yolo_all_text.strip()
    
    # Calculate scores
    yolo_score = calculate_text_quality(yolo_all_text)
    paddle_score = calculate_text_quality(paddle_text)
    
    # Comparison details
    comparison = {
        "yolo_length": len(yolo_all_text),
        "paddle_length": len(paddle_text),
        "yolo_score": yolo_score,
        "paddle_score": paddle_score,
        "winner": "paddle" if paddle_score > yolo_score else "yolo"
    }
    
    # Return best result
    if comparison["winner"] == "paddle":
        return {
            "extracted_fields": parse_paddle_to_fields(paddle_text),
            "general_text": [paddle_text],
            "found_idcard": len(paddle_text) > 50,
            "comparison": comparison,
            "best_method": "paddle"
        }
    else:
        result = yolo_result.copy()
        result["comparison"] = comparison
        result["best_method"] = "yolo_easyocr"
        return result


def calculate_text_quality(text):
    """
    Calculate quality score for OCR text.
    Higher score = better quality.
    
    Factors:
    - Length (more text usually better)
    - Unique characters (variety)
    - Alphanumeric ratio
    - Word count
    """
    if not text or len(text) == 0:
        return 0
    
    score = 0
    
    # Length score (up to 100 points)
    score += min(len(text), 100)
    
    # Unique character ratio (up to 50 points)
    unique_chars = len(set(text))
    if len(text) > 0:
        unique_ratio = unique_chars / len(text)
        score += unique_ratio * 50
    
    # Alphanumeric ratio (up to 30 points)
    alnum_count = sum(c.isalnum() for c in text)
    if len(text) > 0:
        alnum_ratio = alnum_count / len(text)
        score += alnum_ratio * 30
    
    # Word count (up to 20 points)
    words = text.split()
    score += min(len(words), 20)
    
    return score


def parse_paddle_to_fields(text):
    """
    Parse PaddleOCR raw text into structured fields.
    Uses multiple strategies to extract fields.
    """
    import re
    fields = {}
    lines = text.split('\n')
    
    # Helper to add field with normalization
    def add_field(k, v):
        k_clean = k.strip().title()
        v_clean = v.strip()
        if k_clean and v_clean and len(k_clean) < 50:
            # Avoid overwriting with shorter/empty values unless new one is much better?
            # For now, just overwrite or keep first? 
            # Let's keep the longest value for a given key
            if k_clean in fields:
                if len(v_clean) > len(fields[k_clean]):
                    fields[k_clean] = v_clean
            else:
                fields[k_clean] = v_clean

    # Strategy 1: Key:Value pairs
    for line in lines:
        line = line.strip()
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                add_field(parts[0], parts[1])
    
    # Strategy 2: Common field patterns with lookaheads to prevent bleeding
    # We use a lookahead (?=...) to stop matching when we see another field label or end of string
    field_labels = r'(?:Name|Email|Emall|Phone|Mobile|Tel|Dob|Date\s*of\s*birth|Birth\s*date|Address|Location|Id|Identification|Occupation|Job|Position|Age|Gender|Sex)'
    
    patterns = {
        'Name': r'(?i)name[:\s]+((?:(?!' + field_labels + r').)+)',
        'Email': r'(?i)(?:email|e-mail|emall)(?:\s*id)?[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        'Phone': r'(?i)(?:phone|mobile|tel)(?:\s*(?:number|no|#))?[:\s]*([0-9\s\-\+\(\)]{10,})',
        'Dob': r'(?i)(?:dob|date\s*of\s*birth|birth\s*date)[:\s]*([0-9\/\-\.]+)',
        'Address': r'(?i)(?:address|location)[:\s]+((?:(?!' + field_labels + r').)+)',
        'Id': r'(?i)(?:id|identification)[:\s]*([A-Z0-9\-]+)',
        'Occupation': r'(?i)(?:occupation|job|position)[:\s]+((?:(?!' + field_labels + r').)+)',
        'Age': r'(?i)age[:\s]*([0-9]+)',
        'Gender': r'(?i)(?:gender|sex)[:\s]*([A-Za-z]+)',
    }
    
    full_text = ' '.join(lines)
    for field_name, pattern in patterns.items():
        match = re.search(pattern, full_text)
        if match:
            add_field(field_name, match.group(1))
    
    # Strategy 3: Line-by-line field detection
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if line looks like a label
        if len(line) < 30 and not any(c.isdigit() for c in line) and line.endswith(':'):
             # Next line might be the value
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and len(next_line) < 100:
                    key = line.replace(':', '').strip()
                    add_field(key, next_line)
    
    # Enforce standard field order
    ordered_keys = ['Name', 'Address', 'Date of Birth', 'Dob', 'Phone', 'Email', 'Occupation', 'Id']
    ordered_fields = {}
    
    # Add fields in standard order
    for key in ordered_keys:
        # Handle case-insensitive matching for keys
        for field_key in list(fields.keys()):
            if field_key.lower() == key.lower():
                ordered_fields[field_key] = fields[field_key]
                break
            # Handle mapped keys (e.g. Dob -> Date of Birth)
            if key == 'Date of Birth' and field_key in ['Dob', 'Date Of Birth']:
                ordered_fields[field_key] = fields[field_key]
                break
                
    # Add any remaining fields
    for k, v in fields.items():
        if k not in ordered_fields:
            ordered_fields[k] = v
            
    return ordered_fields
