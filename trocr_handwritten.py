from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import numpy as np
import cv2
import logging
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrOCRWrapper:
    def __init__(self, model_name='microsoft/trocr-large-handwritten'):
        """
        Initialize the TrOCR model for handwritten text recognition.
        Args:
            model_name (str): Hugging Face model name. Default is TrOCR-large-handwritten.
        """
        try:
            logger.info(f"Loading TrOCR model: {model_name}")
            # Force use of safetensors to avoid torch.load security issue (CVE-2025-32434)
            # Disable fast tokenizer to avoid 'torch.compiler' has no attribute 'is_compiling' error
            self.processor = TrOCRProcessor.from_pretrained(model_name, use_fast=False)
            self.model = VisionEncoderDecoderModel.from_pretrained(
                model_name,
                use_safetensors=True  # Force safetensors format
            )
            
            # Use GPU if available
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            logger.info(f"TrOCR model loaded successfully on {self.device}!")
        except Exception as e:
            logger.error(f"Failed to initialize TrOCR: {e}")
            raise

    def extract_text_from_image(self, image):
        """
        Extract text from a PIL Image or numpy array.
        Args:
            image: PIL Image or numpy array (OpenCV format BGR)
        Returns:
            str: Extracted text
        """
        try:
            # Convert to PIL Image if it's a numpy array
            if isinstance(image, np.ndarray):
                # OpenCV uses BGR, PIL uses RGB
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(image)
            
            # Preprocess the image
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self.device)
            
            # Generate text
            generated_ids = self.model.generate(pixel_values)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            return generated_text.strip()
        except Exception as e:
            logger.error(f"Error during text extraction: {e}")
            return ""

    def extract_text(self, image_path):
        """
        Extract text from an image file.
        Args:
            image_path (str): Path to the image file
        Returns:
            str: Extracted text
        """
        try:
            image = Image.open(image_path).convert("RGB")
            return self.extract_text_from_image(image)
        except Exception as e:
            logger.error(f"Error loading image from path: {e}")
            return ""

    def extract_text_from_bytes(self, image_bytes):
        """
        Extract text from image bytes.
        Args:
            image_bytes (bytes): Image data as bytes
        Returns:
            str: Extracted text
        """
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return self.extract_text_from_image(image)
        except Exception as e:
            logger.error(f"Error loading image from bytes: {e}")
            return ""

    def extract_text_from_regions(self, image, regions):
        """
        Extract text from multiple regions in an image.
        Args:
            image: PIL Image or numpy array
            regions: List of (x1, y1, x2, y2) bounding boxes
        Returns:
            dict: Mapping of region index to extracted text
        """
        results = {}
        
        # Convert to numpy array if it's a PIL Image
        if isinstance(image, Image.Image):
            image_np = np.array(image)
            if len(image_np.shape) == 3:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        else:
            image_np = image
        
        for idx, (x1, y1, x2, y2) in enumerate(regions):
            try:
                # Crop the region
                crop = image_np[y1:y2, x1:x2]
                
                # Extract text from the cropped region
                text = self.extract_text_from_image(crop)
                results[idx] = text
            except Exception as e:
                logger.error(f"Error extracting text from region {idx}: {e}")
                results[idx] = ""
        
        return results
