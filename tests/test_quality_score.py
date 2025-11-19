import pytest
import numpy as np
import cv2
import os
import sys

# Add parent directory to path to import quality_score
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import quality_score

def test_calculate_blur_score():
    # Create a sharp image (checkerboard)
    sharp_img = np.zeros((100, 100), dtype=np.uint8)
    for i in range(0, 100, 10):
        for j in range(0, 100, 10):
            if (i + j) % 20 == 0:
                sharp_img[i:i+10, j:j+10] = 255
                
    score_sharp = quality_score.calculate_blur_score(sharp_img)
    print(f"Sharp score: {score_sharp}")
    
    # Create a blurry image (Gaussian blur)
    blur_img = cv2.GaussianBlur(sharp_img, (15, 15), 0)
    score_blur = quality_score.calculate_blur_score(blur_img)
    print(f"Blur score: {score_blur}")
    
    assert score_sharp > score_blur
    assert score_sharp > 150  # Should be considered GOOD
    assert score_blur < 150   # Should be lower

def test_calculate_lighting_score():
    # Dark image
    dark_img = np.zeros((100, 100), dtype=np.uint8)
    score_dark = quality_score.calculate_lighting_score(dark_img)
    assert score_dark == 0
    
    # Bright image
    bright_img = np.ones((100, 100), dtype=np.uint8) * 255
    score_bright = quality_score.calculate_lighting_score(bright_img)
    assert score_bright == 255
    
    # Mid-gray image
    gray_img = np.ones((100, 100), dtype=np.uint8) * 127
    score_gray = quality_score.calculate_lighting_score(gray_img)
    assert 126 <= score_gray <= 128

def test_get_quality_report():
    # Create a dummy image bytes
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), -1) # White square
    
    success, encoded_img = cv2.imencode('.jpg', img)
    img_bytes = encoded_img.tobytes()
    
    report = quality_score.get_quality_report(img_bytes)
    
    assert "blur_score" in report
    assert "lighting_score" in report
    assert "overall" in report
    assert "message" in report
    
    # The image is mostly black with a white square, so lighting might be low
    # Blur score for a simple shape might be high (sharp edges)
    print(f"Report: {report}")
