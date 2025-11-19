import pytesseract
from PIL import Image
import io
import numpy as np
import cv2
import platform
import os

class TesseractOCR:
    def __init__(self):
        """
        Initialize Tesseract OCR.
        Note: Tesseract binary must be installed on the system.
        Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
        """
        # Set Tesseract path for Windows
        if platform.system() == 'Windows':
            tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                print(f"✅ Tesseract path set to: {tesseract_path}")
            else:
                print(f"⚠️ Warning: Tesseract not found at {tesseract_path}")
        
        print("✅ Tesseract OCR initialized!")

    def preprocess_image(self, image_input):
        """
        Preprocess image for better OCR results.
        Args:
            image_input (str, bytes, np.ndarray, PIL.Image): Input image.
        Returns:
            PIL.Image: Preprocessed image.
        """
        image = None
        
        # Load image based on type
        if isinstance(image_input, str):
            image = Image.open(image_input)
        elif isinstance(image_input, bytes):
            image = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, np.ndarray):
            image = Image.fromarray(cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB))
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            raise ValueError("Unsupported image format")
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        return image

    def read_text(self, image_input, lang='eng'):
        """
        Perform OCR on the input image.
        Args:
            image_input: Image path, bytes, numpy array, or PIL Image.
            lang: Language code (default: 'eng' for English).
        Returns:
            str: Extracted text.
        """
        try:
            image = self.preprocess_image(image_input)
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang=lang)
            
            # Clean up text
            text = text.strip()
            
            return text
        except Exception as e:
            print(f"❌ Tesseract OCR error: {e}")
            return ""
