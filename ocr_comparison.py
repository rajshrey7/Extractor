def compare_ocr_results(yolo_result, tesseract_text):
    """
    Compare OCR results from YOLO+EasyOCR and Tesseract and return the best one.
    
    Args:
        yolo_result: Dict with extracted_fields and general_text from YOLO+EasyOCR
        tesseract_text: String with full text from Tesseract
        
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
    tesseract_score = calculate_text_quality(tesseract_text)
    
    # Comparison details
    comparison = {
        "yolo_length": len(yolo_all_text),
        "tesseract_length": len(tesseract_text),
        "yolo_score": yolo_score,
        "tesseract_score": tesseract_score,
        "winner": "tesseract" if tesseract_score > yolo_score else "yolo"
    }
    
    # Return best result
    if comparison["winner"] == "tesseract":
        return {
            "extracted_fields": parse_tesseract_to_fields(tesseract_text),
            "general_text": [tesseract_text],
            "found_idcard": len(tesseract_text) > 50,
            "comparison": comparison,
            "best_method": "tesseract"
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


def parse_tesseract_to_fields(text):
    """
    Parse Tesseract raw text into structured fields.
    Uses multiple strategies to extract fields.
    """
    import re
    fields = {}
    lines = text.split('\n')
    
    # Strategy 1: Key:Value pairs
    for line in lines:
        line = line.strip()
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key and value and len(key) < 50:  # Reasonable key length
                    fields[key] = value
    
    # Strategy 2: Common field patterns
    patterns = {
        'name': r'(?i)name[:\s]+([A-Za-z\s]+)',
        'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        'phone': r'(?:phone|mobile|tel)[:\s]*([0-9\s\-\+\(\)]{10,})',
        'dob': r'(?i)(?:dob|date\s*of\s*birth|birth\s*date)[:\s]*([0-9\/\-\.]+)',
        'address': r'(?i)(?:address|location)[:\s]+(.+)',
        'id': r'(?i)(?:id|identification)[:\s]*([A-Z0-9\-]+)',
    }
    
    full_text = ' '.join(lines)
    for field_name, pattern in patterns.items():
        if field_name not in fields:  # Don't override if already found
            match = re.search(pattern, full_text)
            if match:
                fields[field_name] = match.group(1).strip()
    
    # Strategy 3: Line-by-line field detection
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if line looks like a label
        if len(line) < 30 and not any(c.isdigit() for c in line):
            # Next line might be the value
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and len(next_line) < 100:
                    key = line.replace(':', '').strip()
                    if key and key not in fields:
                        fields[key] = next_line
    
    return fields
