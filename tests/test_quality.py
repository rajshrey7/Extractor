import pytest
import numpy as np
from utils.capture_quality import CaptureQualityAnalyzer, analyze_capture_quality


class TestCaptureQuality:
    def setup_method(self):
        self.analyzer = CaptureQualityAnalyzer()
    
    def test_blur_score_calculation(self):
        # Create a sharp image (high frequency)
        sharp_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        sharp_score = self.analyzer._calculate_blur_score(sharp_img)
        assert sharp_score >= 0 and sharp_score <= 100
        
        # Create a blurry image (low frequency)
        blurry_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        blurry_score = self.analyzer._calculate_blur_score(blurry_img)
        assert blurry_score >= 0 and blurry_score <= 100
        assert sharp_score > blurry_score
    
    def test_brightness_score_calculation(self):
        # Test normal brightness
        normal_img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        score = self.analyzer._calculate_brightness_score(normal_img)
        assert score > 70  # Should be good score
        
        # Test dark image
        dark_img = np.ones((100, 100, 3), dtype=np.uint8) * 30
        dark_score = self.analyzer._calculate_brightness_score(dark_img)
        assert dark_score < 50
        
        # Test bright image
        bright_img = np.ones((100, 100, 3), dtype=np.uint8) * 250
        bright_score = self.analyzer._calculate_brightness_score(bright_img)
        assert bright_score < 100
    
    def test_analyze_capture_quality(self):
        # Create test image
        test_img = np.random.randint(100, 150, (500, 500, 3), dtype=np.uint8)
        
        result = analyze_capture_quality(test_img, "document")
        
        assert 'score' in result
        assert 'quality_level' in result
        assert 'metrics' in result
        assert 'suggestions' in result
        
        assert result['score'] >= 0 and result['score'] <= 100
        assert result['quality_level'] in ['excellent', 'good', 'acceptable', 'poor', 'very_poor']