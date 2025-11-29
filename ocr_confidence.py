"""
OCR Confidence Computation Module
Computes per-region confidence scores for OCR results by combining:
- OCR engine native confidence (PaddleOCR)
- Image quality metrics (blur, lighting)
- Text quality heuristics (length, character diversity)
"""

import cv2
import numpy as np
import re
from typing import Dict, List, Tuple, Optional, Any
from quality_score import calculate_blur_score, calculate_lighting_score


def get_text_quality_score(text: str) -> float:
    """
    Calculate text quality score based on heuristics.
    Returns a score between 0 and 1.
    
    Heuristics:
    - Length: Prefer 3-30 characters (too short or too long reduces confidence)
    - Character diversity: Mix of letters and numbers is good
    - Special characters: Too many reduces confidence
    - Whitespace ratio: Too much whitespace is suspicious
    """
    if not text or len(text.strip()) == 0:
        return 0.0
    
    text = text.strip()
    length = len(text)
    
    # Length score (optimal: 3-30 chars)
    if length < 3:
        length_score = length / 3.0
    elif length <= 30:
        length_score = 1.0
    else:
        length_score = max(0.5, 1.0 - (length - 30) / 100.0)
    
    # Character diversity score
    has_letters = bool(re.search(r'[a-zA-Z]', text))
    has_numbers = bool(re.search(r'\d', text))
    has_both = has_letters and has_numbers
    diversity_score = 1.0 if has_both else 0.7 if (has_letters or has_numbers) else 0.3
    
    # Special character ratio (penalize excessive special chars)
    special_chars = len(re.findall(r'[^a-zA-Z0-9\s\-/.]', text))
    special_ratio = special_chars / length if length > 0 else 0
    special_score = max(0.3, 1.0 - (special_ratio * 2.0))
    
    # Whitespace ratio (penalize excessive whitespace)
    whitespace_count = text.count(' ') + text.count('\t') + text.count('\n')
    whitespace_ratio = whitespace_count / length if length > 0 else 0
    whitespace_score = max(0.5, 1.0 - (whitespace_ratio * 2.0))
    
    # Combined text quality score
    text_quality = (
        length_score * 0.3 +
        diversity_score * 0.3 +
        special_score * 0.2 +
        whitespace_score * 0.2
    )
    
    return min(1.0, max(0.0, text_quality))


def compute_image_quality_score(blur_score: float, lighting_score: float) -> float:
    """
    Compute normalized image quality score from blur and lighting metrics.
    Returns a score between 0 and 1.
    
    Args:
        blur_score: Laplacian variance (higher = sharper)
        lighting_score: Mean grayscale intensity (0-255)
    """
    # Blur quality (based on thresholds from quality_score.py)
    if blur_score > 150:
        blur_quality = 1.0
    elif blur_score >= 70:
        # Linear interpolation between 70-150
        blur_quality = 0.5 + 0.5 * ((blur_score - 70) / 80.0)
    else:
        # Linear below 70
        blur_quality = max(0.0, blur_score / 140.0)
    
    # Lighting quality (optimal range: 90-150)
    if 90 <= lighting_score <= 150:
        lighting_quality = 1.0
    elif lighting_score < 90:
        # Too dark
        lighting_quality = max(0.0, lighting_score / 90.0)
    else:
        # Too bright (> 150)
        lighting_quality = max(0.3, 1.0 - ((lighting_score - 150) / 200.0))
    
    # Combined image quality (weighted average)
    image_quality = blur_quality * 0.6 + lighting_quality * 0.4
    
    return min(1.0, max(0.0, image_quality))


def compute_combined_score(
    ocr_conf: float,
    blur_score: float,
    lighting_score: float,
    text: str
) -> float:
    """
    Compute final combined confidence score from all signals.
    
    Args:
        ocr_conf: OCR engine confidence (0-1)
        blur_score: Image blur score
        lighting_score: Image lighting score
        text: Extracted text
        
    Returns:
        Combined confidence score (0-1)
    """
    # Compute component scores
    image_quality = compute_image_quality_score(blur_score, lighting_score)
    text_quality = get_text_quality_score(text)
    
    # Weighted combination
    # OCR confidence is most important, followed by image quality, then text heuristics
    combined = (
        ocr_conf * 0.5 +
        image_quality * 0.3 +
        text_quality * 0.2
    )
    
    return min(1.0, max(0.0, combined))


def suggest_corrections(text: str, confidence: float) -> List[str]:
    """
    Generate correction suggestions for low-confidence text.
    
    Args:
        text: Extracted text
        confidence: Confidence score (0-1)
        
    Returns:
        List of suggested corrections
    """
    suggestions = []
    
    if not text or confidence >= 0.85:
        # High confidence, no suggestions needed
        return suggestions
    
    # Common OCR confusion patterns
    confusion_map = {
        '0': ['O', 'D'],
        'O': ['0', 'Q'],
        '1': ['I', 'l'],
        'I': ['1', 'l'],
        'l': ['1', 'I'],
        '5': ['S'],
        'S': ['5'],
        '8': ['B'],
        'B': ['8'],
        '2': ['Z'],
        'Z': ['2']
    }
    
    # Generate simple character substitution suggestions
    for i, char in enumerate(text):
        if char in confusion_map:
            for replacement in confusion_map[char]:
                suggestion = text[:i] + replacement + text[i+1:]
                if suggestion != text and suggestion not in suggestions:
                    suggestions.append(suggestion)
    
    # Limit to top 3 suggestions
    return suggestions[:3]


def get_region_confidence(
    ocr_result: Any,
    crop_image_bytes: bytes,
    ocr_method: str = 'easyocr'
) -> Dict[str, Any]:
    """
    Compute confidence score for a single detected text region.
    
    Args:
        ocr_result: OCR engine result (format depends on ocr_method)
        crop_image_bytes: Cropped region image as bytes
        ocr_method: OCR engine used ('easyocr', 'tesseract', etc.)
        
    Returns:
        Dictionary with:
        - text: Extracted text
        - confidence: Combined confidence score (0-1)
        - ocr_confidence: Raw OCR confidence
        - blur_score: Image blur metric
        - lighting_score: Image lighting metric
        - image_quality: Computed image quality (0-1)
        - text_quality: Computed text quality (0-1)
        - suggestions: List of correction suggestions
    """
    # Default values
    text = ""
    ocr_conf = 0.5  # Default if not available
    
    # Extract text and confidence based on OCR method
    if ocr_method == 'easyocr':
        # EasyOCR returns list of (bbox, text, confidence) tuples
        # If ocr_result is already processed, it might be just text or (text, conf)
        if isinstance(ocr_result, str):
            text = ocr_result
            ocr_conf = 0.7  # Default assumption
        elif isinstance(ocr_result, (list, tuple)):
            if len(ocr_result) >= 2:
                text = str(ocr_result[0]) if len(ocr_result) == 2 else str(ocr_result[1])
                # Try to get confidence (might be 2nd or 3rd element)
                try:
                    conf_idx = 1 if len(ocr_result) == 2 else 2
                    ocr_conf = float(ocr_result[conf_idx]) if conf_idx < len(ocr_result) else 0.7
                except (ValueError, TypeError, IndexError):
                    ocr_conf = 0.7
            else:
                text = str(ocr_result[0]) if ocr_result else ""
                ocr_conf = 0.7
        else:
            text = str(ocr_result)
            ocr_conf = 0.7
    elif ocr_method == 'paddle':
        # PaddleOCR result passed as (text, confidence) tuple
        if isinstance(ocr_result, (list, tuple)) and len(ocr_result) >= 2:
            text = str(ocr_result[0])
            ocr_conf = float(ocr_result[1])
        else:
            text = str(ocr_result)
            ocr_conf = 0.9 # Default high confidence for Paddle
    else:
        # Generic fallback
        text = str(ocr_result) if ocr_result else ""
        ocr_conf = 0.7
    
    # Decode image and calculate quality metrics
    try:
        nparr = np.frombuffer(crop_image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is not None:
            blur_score = calculate_blur_score(img)
            lighting_score = calculate_lighting_score(img)
        else:
            blur_score = 0.0
            lighting_score = 0.0
    except Exception as e:
        print(f"Warning: Error computing image quality for region: {e}")
        blur_score = 0.0
        lighting_score = 0.0
    
    # Compute component scores
    image_quality = compute_image_quality_score(blur_score, lighting_score)
    text_quality = get_text_quality_score(text)
    
    # Compute final combined confidence
    combined_confidence = compute_combined_score(ocr_conf, blur_score, lighting_score, text)
    
    # Generate suggestions for low confidence
    suggestions = suggest_corrections(text, combined_confidence)
    
    return {
        'text': text,
        'confidence': round(combined_confidence, 3),
        'ocr_confidence': round(ocr_conf, 3),
        'blur_score': round(blur_score, 2),
        'lighting_score': round(lighting_score, 2),
        'image_quality': round(image_quality, 3),
        'text_quality': round(text_quality, 3),
        'suggestions': suggestions
    }


def compute_document_confidence(regions: List[Dict[str, Any]]) -> float:
    """
    Compute overall document confidence from region confidences.
    Uses weighted average based on region area (if available) or simple average.
    
    Args:
        regions: List of region dictionaries with 'confidence' and optionally 'box' (x, y, w, h)
        
    Returns:
        Document-level confidence score (0-1)
    """
    if not regions:
        return 0.0
    
    total_weight = 0.0
    weighted_sum = 0.0
    
    for region in regions:
        confidence = region.get('confidence', 0.0)
        
        # Use region area as weight if box is available
        box = region.get('box')
        if box and len(box) >= 4:
            # Box format: [x, y, w, h] or [x1, y1, x2, y2]
            if len(box) == 4:
                # Assume [x, y, w, h]
                area = box[2] * box[3] if box[2] > 0 and box[3] > 0 else 1.0
            else:
                # Could be [x1, y1, x2, y2]
                area = abs(box[2] - box[0]) * abs(box[3] - box[1])
        else:
            area = 1.0  # Default weight
        
        weighted_sum += confidence * area
        total_weight += area
    
    if total_weight > 0:
        return round(weighted_sum / total_weight, 3)
    else:
        # Fallback to simple average
        return round(sum(r.get('confidence', 0.0) for r in regions) / len(regions), 3)
