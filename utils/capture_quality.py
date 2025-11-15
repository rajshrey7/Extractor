"""
Capture Quality Scoring Module
Computes various quality metrics on images including blur, exposure, glare, 
face pose, document skew, resolution, and occlusion.
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image
import io
import base64
import logging
from dataclasses import dataclass
from enum import Enum
import math

# Configure logging
logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality level classification"""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"           # 75-89
    ACCEPTABLE = "acceptable"  # 60-74
    POOR = "poor"           # 40-59
    VERY_POOR = "very_poor"  # 0-39


@dataclass
class QualityMetrics:
    """Data class for quality metrics"""
    blur_score: float
    brightness_score: float
    exposure_score: float
    glare_score: float
    face_confidence: Optional[float]
    document_skew: Optional[float]
    resolution_score: float
    occlusion_score: float
    overall_score: float
    quality_level: QualityLevel
    suggestions: List[str]


class CaptureQualityAnalyzer:
    """Analyzes image capture quality"""
    
    def __init__(self):
        """Initialize quality analyzer"""
        self.face_cascade = None
        try:
            # Try to load face cascade for face detection
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        except Exception as e:
            logger.warning(f"Could not load face cascade: {e}")
            
    def analyze_image(self, image_data: Any, image_type: str = "document") -> QualityMetrics:
        """
        Analyze image quality
        
        Args:
            image_data: Image data (bytes, numpy array, or PIL Image)
            image_type: Type of image ("document", "face", "id_card")
            
        Returns:
            QualityMetrics object with all metrics and overall score
        """
        # Convert image to numpy array
        img = self._prepare_image(image_data)
        
        if img is None:
            return self._get_error_metrics("Failed to process image")
            
        # Calculate individual metrics
        blur_score = self._calculate_blur_score(img)
        brightness_score = self._calculate_brightness_score(img)
        exposure_score = self._calculate_exposure_score(img)
        glare_score = self._calculate_glare_score(img)
        resolution_score = self._calculate_resolution_score(img)
        occlusion_score = self._calculate_occlusion_score(img)
        
        # Type-specific metrics
        face_confidence = None
        document_skew = None
        
        if image_type == "face" or image_type == "id_card":
            face_confidence = self._calculate_face_confidence(img)
            
        if image_type == "document" or image_type == "id_card":
            document_skew = self._calculate_document_skew(img)
            
        # Calculate overall score
        scores = [
            blur_score * 0.25,
            brightness_score * 0.15,
            exposure_score * 0.15,
            glare_score * 0.15,
            resolution_score * 0.15,
            occlusion_score * 0.15
        ]
        
        # Add type-specific scores
        if face_confidence is not None:
            scores.append(face_confidence * 0.2)
            # Adjust other weights
            scores = [s * 0.8 for s in scores[:6]]
            scores.append(face_confidence * 0.2)
            
        if document_skew is not None:
            skew_score = max(0, 100 - abs(document_skew) * 10)
            scores.append(skew_score * 0.1)
            # Adjust other weights
            base_scores = scores[:6] if face_confidence is None else scores[:7]
            scores = [s * 0.9 for s in base_scores]
            scores.append(skew_score * 0.1)
            
        overall_score = sum(scores)
        
        # Determine quality level
        quality_level = self._get_quality_level(overall_score)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            blur_score=blur_score,
            brightness_score=brightness_score,
            exposure_score=exposure_score,
            glare_score=glare_score,
            resolution_score=resolution_score,
            occlusion_score=occlusion_score,
            face_confidence=face_confidence,
            document_skew=document_skew
        )
        
        return QualityMetrics(
            blur_score=blur_score,
            brightness_score=brightness_score,
            exposure_score=exposure_score,
            glare_score=glare_score,
            face_confidence=face_confidence,
            document_skew=document_skew,
            resolution_score=resolution_score,
            occlusion_score=occlusion_score,
            overall_score=overall_score,
            quality_level=quality_level,
            suggestions=suggestions
        )
        
    def _prepare_image(self, image_data: Any) -> Optional[np.ndarray]:
        """Convert various image formats to numpy array"""
        try:
            if isinstance(image_data, np.ndarray):
                return image_data
            elif isinstance(image_data, Image.Image):
                return np.array(image_data)
            elif isinstance(image_data, bytes):
                # Decode from bytes
                nparr = np.frombuffer(image_data, np.uint8)
                return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif isinstance(image_data, str):
                # Check if it's base64 encoded
                if image_data.startswith('data:image'):
                    # Extract base64 data
                    base64_data = image_data.split(',')[1]
                    image_bytes = base64.b64decode(base64_data)
                    nparr = np.frombuffer(image_bytes, np.uint8)
                    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                else:
                    # Assume file path
                    return cv2.imread(image_data)
            else:
                logger.error(f"Unsupported image data type: {type(image_data)}")
                return None
        except Exception as e:
            logger.error(f"Error preparing image: {e}")
            return None
            
    def _calculate_blur_score(self, img: np.ndarray) -> float:
        """
        Calculate blur score using Laplacian variance
        Higher variance = sharper image
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-100 scale
            # Empirically determined thresholds
            if laplacian_var > 500:
                score = 100
            elif laplacian_var < 50:
                score = 0
            else:
                score = (laplacian_var - 50) / 450 * 100
                
            return min(100, max(0, score))
        except Exception as e:
            logger.error(f"Error calculating blur score: {e}")
            return 50.0
            
    def _calculate_brightness_score(self, img: np.ndarray) -> float:
        """Calculate brightness score based on histogram analysis"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            mean_brightness = np.mean(gray)
            
            # Ideal brightness range: 100-155
            if 100 <= mean_brightness <= 155:
                score = 100
            elif mean_brightness < 100:
                score = mean_brightness  # 0-100
            else:
                # Too bright
                score = max(0, 100 - (mean_brightness - 155) * 0.5)
                
            return min(100, max(0, score))
        except Exception as e:
            logger.error(f"Error calculating brightness score: {e}")
            return 50.0
            
    def _calculate_exposure_score(self, img: np.ndarray) -> float:
        """Calculate exposure score based on histogram distribution"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = hist.flatten() / hist.sum()
            
            # Check for over/under exposure
            underexposed = hist[:50].sum()  # Dark pixels
            overexposed = hist[205:].sum()   # Bright pixels
            
            if underexposed > 0.5:
                score = (1 - underexposed) * 100
            elif overexposed > 0.5:
                score = (1 - overexposed) * 100
            else:
                # Calculate histogram spread (standard deviation)
                mean = np.sum(np.arange(256) * hist)
                std = np.sqrt(np.sum(((np.arange(256) - mean) ** 2) * hist))
                
                # Ideal std range: 40-80
                if 40 <= std <= 80:
                    score = 100
                elif std < 40:
                    score = std * 2.5
                else:
                    score = max(0, 100 - (std - 80) * 0.5)
                    
            return min(100, max(0, score))
        except Exception as e:
            logger.error(f"Error calculating exposure score: {e}")
            return 50.0
            
    def _calculate_glare_score(self, img: np.ndarray) -> float:
        """Calculate glare score by detecting bright spots"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            
            # Detect bright spots (potential glare)
            _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
            glare_pixels = np.sum(thresh == 255)
            total_pixels = gray.shape[0] * gray.shape[1]
            glare_ratio = glare_pixels / total_pixels
            
            # Calculate score (less glare = higher score)
            if glare_ratio < 0.01:
                score = 100
            elif glare_ratio > 0.2:
                score = 0
            else:
                score = 100 - (glare_ratio * 500)
                
            return min(100, max(0, score))
        except Exception as e:
            logger.error(f"Error calculating glare score: {e}")
            return 50.0
            
    def _calculate_face_confidence(self, img: np.ndarray) -> Optional[float]:
        """Calculate face detection confidence"""
        try:
            if self.face_cascade is None:
                return None
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return 0.0
            elif len(faces) == 1:
                # Calculate face size relative to image
                x, y, w, h = faces[0]
                face_area = w * h
                image_area = img.shape[0] * img.shape[1]
                face_ratio = face_area / image_area
                
                # Ideal face size: 10-40% of image
                if 0.1 <= face_ratio <= 0.4:
                    score = 100
                elif face_ratio < 0.1:
                    score = face_ratio * 1000
                else:
                    score = max(0, 100 - (face_ratio - 0.4) * 200)
                    
                return min(100, max(0, score))
            else:
                # Multiple faces detected - reduce confidence
                return 50.0
        except Exception as e:
            logger.error(f"Error calculating face confidence: {e}")
            return None
            
    def _calculate_document_skew(self, img: np.ndarray) -> Optional[float]:
        """Calculate document skew angle using Hough transform"""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
            
            if lines is None:
                return 0.0
                
            # Calculate average angle
            angles = []
            for line in lines[:min(20, len(lines))]:
                rho, theta = line[0]
                angle = np.degrees(theta) - 90
                angles.append(angle)
                
            if angles:
                # Find dominant angle (most common)
                avg_angle = np.median(angles)
                return avg_angle
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Error calculating document skew: {e}")
            return None
            
    def _calculate_resolution_score(self, img: np.ndarray) -> float:
        """Calculate resolution score based on image dimensions"""
        try:
            height, width = img.shape[:2]
            pixels = height * width
            
            # Minimum acceptable resolution thresholds
            min_resolution = 640 * 480    # VGA
            good_resolution = 1280 * 720  # HD
            ideal_resolution = 1920 * 1080  # Full HD
            
            if pixels >= ideal_resolution:
                score = 100
            elif pixels >= good_resolution:
                score = 75 + (pixels - good_resolution) / (ideal_resolution - good_resolution) * 25
            elif pixels >= min_resolution:
                score = 50 + (pixels - min_resolution) / (good_resolution - min_resolution) * 25
            else:
                score = pixels / min_resolution * 50
                
            return min(100, max(0, score))
        except Exception as e:
            logger.error(f"Error calculating resolution score: {e}")
            return 50.0
            
    def _calculate_occlusion_score(self, img: np.ndarray) -> float:
        """
        Calculate occlusion score by detecting blocked areas
        Uses edge detection and contour analysis
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            
            # Edge detection
            edges = cv2.Canny(gray, 100, 200)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return 100.0  # No occlusion detected
                
            # Calculate area covered by large contours (potential occlusions)
            total_area = img.shape[0] * img.shape[1]
            occluded_area = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # Consider large irregular shapes as potential occlusions
                if area > total_area * 0.05:  # More than 5% of image
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter * perimeter)
                        if circularity < 0.5:  # Irregular shape
                            occluded_area += area
                            
            occlusion_ratio = occluded_area / total_area
            
            if occlusion_ratio < 0.05:
                score = 100
            elif occlusion_ratio > 0.3:
                score = 0
            else:
                score = 100 - (occlusion_ratio * 333)
                
            return min(100, max(0, score))
        except Exception as e:
            logger.error(f"Error calculating occlusion score: {e}")
            return 50.0
            
    def _get_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level based on overall score"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 75:
            return QualityLevel.GOOD
        elif score >= 60:
            return QualityLevel.ACCEPTABLE
        elif score >= 40:
            return QualityLevel.POOR
        else:
            return QualityLevel.VERY_POOR
            
    def _generate_suggestions(self, **metrics) -> List[str]:
        """Generate improvement suggestions based on metrics"""
        suggestions = []
        
        if metrics.get('blur_score', 100) < 60:
            suggestions.append("Hold the camera steady and ensure proper focus")
            
        if metrics.get('brightness_score', 100) < 60:
            suggestions.append("Increase lighting or move to a brighter area")
        elif metrics.get('brightness_score', 100) > 90 and metrics.get('exposure_score', 100) < 70:
            suggestions.append("Reduce direct light to avoid overexposure")
            
        if metrics.get('glare_score', 100) < 60:
            suggestions.append("Avoid reflective surfaces and direct light sources")
            
        if metrics.get('resolution_score', 100) < 60:
            suggestions.append("Move closer to the document or use higher resolution camera")
            
        if metrics.get('occlusion_score', 100) < 60:
            suggestions.append("Ensure the entire document is visible without obstructions")
            
        if metrics.get('face_confidence') is not None and metrics['face_confidence'] < 60:
            suggestions.append("Ensure face is clearly visible and properly positioned")
            
        if metrics.get('document_skew') is not None and abs(metrics['document_skew']) > 5:
            suggestions.append("Align the document parallel to the camera frame")
            
        if not suggestions:
            suggestions.append("Image quality is good!")
            
        return suggestions
        
    def _get_error_metrics(self, error_message: str) -> QualityMetrics:
        """Return error metrics when processing fails"""
        return QualityMetrics(
            blur_score=0,
            brightness_score=0,
            exposure_score=0,
            glare_score=0,
            face_confidence=None,
            document_skew=None,
            resolution_score=0,
            occlusion_score=0,
            overall_score=0,
            quality_level=QualityLevel.VERY_POOR,
            suggestions=[error_message]
        )


def analyze_capture_quality(image_data: Any, image_type: str = "document") -> Dict[str, Any]:
    """
    Convenience function to analyze capture quality
    
    Args:
        image_data: Image data (bytes, numpy array, PIL Image, or base64 string)
        image_type: Type of image ("document", "face", "id_card")
        
    Returns:
        Dictionary with quality metrics and suggestions
    """
    analyzer = CaptureQualityAnalyzer()
    metrics = analyzer.analyze_image(image_data, image_type)
    
    return {
        "score": round(metrics.overall_score, 2),
        "quality_level": metrics.quality_level.value,
        "metrics": {
            "blur": round(metrics.blur_score, 2),
            "brightness": round(metrics.brightness_score, 2),
            "exposure": round(metrics.exposure_score, 2),
            "glare": round(metrics.glare_score, 2),
            "resolution": round(metrics.resolution_score, 2),
            "occlusion": round(metrics.occlusion_score, 2),
            "face_confidence": round(metrics.face_confidence, 2) if metrics.face_confidence is not None else None,
            "document_skew": round(metrics.document_skew, 2) if metrics.document_skew is not None else None
        },
        "suggestions": metrics.suggestions
    }