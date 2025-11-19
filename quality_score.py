import cv2
import numpy as np

def calculate_blur_score(image: np.ndarray) -> float:
    """
    Calculate the blur score of an image using Laplacian variance.
    Higher score means sharper image.
    """
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Calculate Laplacian variance
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return float(variance)
    except Exception as e:
        print(f"Error calculating blur score: {e}")
        return 0.0

def calculate_lighting_score(image: np.ndarray) -> float:
    """
    Calculate the lighting score of an image using grayscale mean intensity.
    Range 0-255.
    """
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        return float(np.mean(gray))
    except Exception as e:
        print(f"Error calculating lighting score: {e}")
        return 0.0

def get_quality_report(image_bytes: bytes) -> dict:
    """
    Analyze image quality and return a report with scores and suggestions.
    """
    try:
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {
                "blur_score": 0,
                "lighting_score": 0,
                "overall": "POOR",
                "message": "Could not decode image."
            }

        blur_score = calculate_blur_score(img)
        lighting_score = calculate_lighting_score(img)
        
        # Determine Blur Status
        if blur_score > 150:
            blur_status = "GOOD"
        elif blur_score >= 70:
            blur_status = "AVERAGE"
        else:
            blur_status = "POOR"
            
        # Determine Lighting Status
        if lighting_score > 150:
            lighting_status = "TOO_BRIGHT" # Treated as warning but maybe acceptable
        elif lighting_score >= 90:
            lighting_status = "GOOD"
        else:
            lighting_status = "TOO_DARK"
            
        # Overall Assessment
        suggestions = []
        overall = "GOOD"
        
        if blur_status == "POOR":
            overall = "POOR"
            suggestions.append("Image is blurry — try holding your phone steady.")
        elif blur_status == "AVERAGE":
            if overall != "POOR": overall = "AVERAGE"
            suggestions.append("Image is slightly blurry.")
            
        if lighting_status == "TOO_DARK":
            if overall != "POOR": overall = "POOR" # Dark is usually bad for OCR
            suggestions.append("Lighting is low — turn on flash or move to a brighter area.")
        elif lighting_status == "TOO_BRIGHT":
            if overall != "POOR": overall = "AVERAGE"
            suggestions.append("Image might be too bright/washed out.")
            
        if overall == "GOOD":
            message = "Image quality is good."
        else:
            message = " ".join(suggestions)
            
        return {
            "blur_score": round(blur_score, 2),
            "lighting_score": round(lighting_score, 2),
            "overall": overall,
            "message": message
        }
        
    except Exception as e:
        print(f"Error generating quality report: {e}")
        return {
            "blur_score": 0,
            "lighting_score": 0,
            "overall": "POOR",
            "message": f"Error analyzing image: {str(e)}"
        }
