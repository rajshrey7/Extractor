from paddleocr import PaddleOCR
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PaddleOCRWrapper:
    def __init__(self, lang='en'):
        """
        Initialize the PaddleOCR engine.
        Args:
            lang (str): Language code (default: 'en').
        """
        try:
            # Initialize PaddleOCR with angle classification enabled
            self.ocr = PaddleOCR(use_angle_cls=True, lang=lang)
            logger.info("PaddleOCR initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise

    def extract_text(self, image_path):
        """
        Extract text from an image using PaddleOCR.
        Args:
            image_path (str): Path to the image file.
        Returns:
            str: Extracted text combined into a single string.
        """
        try:
            result = self.ocr.ocr(image_path)
            if not result or result[0] is None:
                return ""
            
            # Handle dictionary structure (PP-Structure / newer versions)
            if isinstance(result[0], dict) and 'rec_texts' in result[0]:
                return "\n".join(result[0]['rec_texts'])
            
            # Handle standard list structure
            # result structure: [[[[x1, y1], [x2, y2], [x3, y3], [x4, y4]], (text, confidence)], ...]
            extracted_text = []
            for line in result[0]:
                if isinstance(line, list) and len(line) >= 2:
                    text = line[1][0]
                    extracted_text.append(text)
            
            return "\n".join(extracted_text)
        except Exception as e:
            logger.error(f"Error during text extraction: {e}")
            return ""

    def extract_data(self, image_path):
        """
        Extract detailed data (text, confidence, box) from an image.
        Args:
            image_path (str): Path to the image file.
        Returns:
            list: List of dictionaries containing 'text', 'confidence', and 'box'.
        """
        try:
            result = self.ocr.ocr(image_path)
            if not result or result[0] is None:
                return []

            data = []
            
            # Handle dictionary structure
            if isinstance(result[0], dict) and 'rec_texts' in result[0]:
                texts = result[0]['rec_texts']
                scores = result[0].get('rec_scores', [])
                boxes = result[0].get('dt_polys', [])
                
                for i, text in enumerate(texts):
                    box = boxes[i] if i < len(boxes) else []
                    score = scores[i] if i < len(scores) else 0.0
                    data.append({
                        'text': text,
                        'confidence': score,
                        'box': box
                    })
                return data

            # Handle standard list structure
            for line in result[0]:
                if isinstance(line, list) and len(line) >= 2:
                    box = line[0]
                    text, confidence = line[1]
                    data.append({
                        'text': text,
                        'confidence': confidence,
                        'box': box
                    })
            return data
        except Exception as e:
            logger.error(f"Error during detailed extraction: {e}")
            return []
