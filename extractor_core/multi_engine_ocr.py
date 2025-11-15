"""
Multi-Engine OCR Module
Integrates multiple OCR engines (Google Vision, EasyOCR, Tesseract) 
with confidence scoring, heatmap generation, and multi-page support.
"""

import os
import io
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import base64
import logging
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import pytesseract
from concurrent.futures import ThreadPoolExecutor
import tempfile
import zipfile

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TextRegion:
    """Represents a text region with bounding box and confidence"""
    text: str
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float
    engine: str
    page: Optional[int] = None


@dataclass
class OCRResult:
    """Complete OCR result for a document"""
    document_id: str
    pages: List[Dict[str, Any]]
    merged_fields: Dict[str, Any]
    quality: Dict[str, Any]
    raw_text: str
    total_pages: int
    processing_time: float
    engines_used: List[str]


class MultiEngineOCR:
    """Multi-engine OCR processor with advanced features"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize OCR processor with configuration"""
        self.config = config or {}
        self.engines = self._initialize_engines()
        self.field_patterns = self._initialize_field_patterns()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def _initialize_engines(self) -> Dict[str, bool]:
        """Initialize available OCR engines"""
        engines = {}
        
        # Check EasyOCR
        try:
            import easyocr
            self.easyocr_reader = easyocr.Reader(['en'])
            engines['easyocr'] = True
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            engines['easyocr'] = False
            logger.warning(f"EasyOCR not available: {e}")
            
        # Check Tesseract
        try:
            pytesseract.get_tesseract_version()
            engines['tesseract'] = True
            logger.info("Tesseract initialized successfully")
        except Exception as e:
            engines['tesseract'] = False
            logger.warning(f"Tesseract not available: {e}")
            
        # Check Google Vision
        google_api_key = self.config.get('google_vision_api_key') or os.getenv('GOOGLE_VISION_API_KEY')
        if google_api_key:
            try:
                from google.cloud import vision
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_api_key
                self.vision_client = vision.ImageAnnotatorClient()
                engines['google_vision'] = True
                logger.info("Google Vision initialized successfully")
            except Exception as e:
                engines['google_vision'] = False
                logger.warning(f"Google Vision not available: {e}")
        else:
            engines['google_vision'] = False
            
        return engines
        
    def _initialize_field_patterns(self) -> Dict[str, Any]:
        """Initialize regex patterns for field extraction"""
        return {
            'name': [
                r'(?:name|full\s*name)[:\s]+([A-Za-z\s]+)',
                r'(?:first\s*name)[:\s]+([A-Za-z]+).*(?:last\s*name)[:\s]+([A-Za-z]+)'
            ],
            'date': [
                r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
            ],
            'phone': [
                r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                r'\d{10,12}'
            ],
            'email': [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ],
            'id_number': [
                r'(?:id|passport|license)[:\s#]+([A-Z0-9]+)',
                r'\b[A-Z]{2}\d{6,10}\b'
            ],
            'address': [
                r'(?:address)[:\s]+(.+?)(?=\n|$)',
                r'\d+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|lane|ln)'
            ]
        }
        
    async def process_document(
        self, 
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        file_type: str = 'auto'
    ) -> OCRResult:
        """
        Process a document with multi-engine OCR
        
        Args:
            file_path: Path to the file
            file_bytes: File content as bytes
            file_type: Type of file ('pdf', 'image', 'auto')
            
        Returns:
            OCRResult object with complete OCR data
        """
        start_time = datetime.now()
        
        # Generate document ID
        document_id = self._generate_document_id()
        
        # Determine file type
        if file_type == 'auto':
            file_type = self._detect_file_type(file_path, file_bytes)
            
        # Process based on file type
        if file_type == 'pdf':
            pages_data = await self._process_pdf(file_path, file_bytes)
        else:
            pages_data = await self._process_image(file_path, file_bytes)
            
        # Merge fields from all pages
        merged_fields = self._merge_fields(pages_data)
        
        # Calculate quality score
        quality = self._calculate_document_quality(pages_data)
        
        # Extract raw text
        raw_text = self._extract_raw_text(pages_data)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Get engines used
        engines_used = self._get_engines_used(pages_data)
        
        return OCRResult(
            document_id=document_id,
            pages=pages_data,
            merged_fields=merged_fields,
            quality=quality,
            raw_text=raw_text,
            total_pages=len(pages_data),
            processing_time=processing_time,
            engines_used=engines_used
        )
        
    async def _process_pdf(
        self, 
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None
    ) -> List[Dict[str, Any]]:
        """Process PDF document"""
        pages_data = []
        
        # Open PDF
        if file_path:
            pdf_document = fitz.open(file_path)
        else:
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            
        try:
            # Process each page
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better quality
                img_data = pix.tobytes("png")
                
                # Process image with OCR
                page_result = await self._process_single_image(img_data, page_num + 1)
                pages_data.append(page_result)
                
        finally:
            pdf_document.close()
            
        return pages_data
        
    async def _process_image(
        self, 
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None
    ) -> List[Dict[str, Any]]:
        """Process single image"""
        if file_path:
            with open(file_path, 'rb') as f:
                img_data = f.read()
        else:
            img_data = file_bytes
            
        page_result = await self._process_single_image(img_data, 1)
        return [page_result]
        
    async def _process_single_image(self, img_data: bytes, page_num: int) -> Dict[str, Any]:
        """Process single image with multiple OCR engines"""
        # Convert to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Run OCR with available engines
        ocr_results = await self._run_multi_engine_ocr(img)
        
        # Combine results
        combined_regions = self._combine_ocr_results(ocr_results)
        
        # Extract fields
        extracted_fields = self._extract_fields(combined_regions)
        
        # Generate heatmap
        heatmap = self._generate_confidence_heatmap(img, combined_regions)
        
        return {
            "page": page_num,
            "raw_text": " ".join([r.text for r in combined_regions]),
            "regions": [asdict(r) for r in combined_regions],
            "fields": extracted_fields,
            "heatmap": heatmap,
            "image_size": img.shape[:2]
        }
        
    async def _run_multi_engine_ocr(self, img: np.ndarray) -> Dict[str, List[TextRegion]]:
        """Run OCR with multiple engines in parallel"""
        results = {}
        tasks = []
        
        if self.engines.get('easyocr'):
            tasks.append(('easyocr', self._run_easyocr(img)))
            
        if self.engines.get('tesseract'):
            tasks.append(('tesseract', self._run_tesseract(img)))
            
        if self.engines.get('google_vision'):
            tasks.append(('google_vision', self._run_google_vision(img)))
            
        # Run engines in parallel
        if tasks:
            engine_results = await asyncio.gather(*[task[1] for task in tasks])
            for i, (engine_name, _) in enumerate(tasks):
                results[engine_name] = engine_results[i]
                
        return results
        
    async def _run_easyocr(self, img: np.ndarray) -> List[TextRegion]:
        """Run EasyOCR on image"""
        try:
            results = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.easyocr_reader.readtext,
                img
            )
            
            regions = []
            for bbox, text, confidence in results:
                # Convert bbox format
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                regions.append(TextRegion(
                    text=text,
                    bbox=[min(x_coords), min(y_coords), max(x_coords), max(y_coords)],
                    confidence=confidence,
                    engine='easyocr'
                ))
                
            return regions
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return []
            
    async def _run_tesseract(self, img: np.ndarray) -> List[TextRegion]:
        """Run Tesseract on image"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Run Tesseract with detailed output
            data = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                pytesseract.image_to_data,
                gray,
                output_type=pytesseract.Output.DICT
            )
            
            regions = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                if int(data['conf'][i]) > 0:  # Filter out empty detections
                    text = data['text'][i].strip()
                    if text:
                        regions.append(TextRegion(
                            text=text,
                            bbox=[
                                data['left'][i],
                                data['top'][i],
                                data['left'][i] + data['width'][i],
                                data['top'][i] + data['height'][i]
                            ],
                            confidence=float(data['conf'][i]) / 100.0,
                            engine='tesseract'
                        ))
                        
            return regions
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return []
            
    async def _run_google_vision(self, img: np.ndarray) -> List[TextRegion]:
        """Run Google Vision on image"""
        try:
            # Convert to bytes
            _, buffer = cv2.imencode('.png', img)
            image_bytes = buffer.tobytes()
            
            # Create Vision API image
            from google.cloud import vision
            image = vision.Image(content=image_bytes)
            
            # Run text detection
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.vision_client.text_detection,
                image
            )
            
            regions = []
            for text in response.text_annotations[1:]:  # Skip first (full text)
                vertices = text.bounding_poly.vertices
                regions.append(TextRegion(
                    text=text.description,
                    bbox=[
                        vertices[0].x,
                        vertices[0].y,
                        vertices[2].x,
                        vertices[2].y
                    ],
                    confidence=0.95,  # Google Vision doesn't provide confidence
                    engine='google_vision'
                ))
                
            return regions
        except Exception as e:
            logger.error(f"Google Vision error: {e}")
            return []
            
    def _combine_ocr_results(self, results: Dict[str, List[TextRegion]]) -> List[TextRegion]:
        """Combine results from multiple engines using confidence scoring"""
        all_regions = []
        for engine_regions in results.values():
            all_regions.extend(engine_regions)
            
        if not all_regions:
            return []
            
        # Group overlapping regions
        combined_regions = []
        used_indices = set()
        
        for i, region1 in enumerate(all_regions):
            if i in used_indices:
                continue
                
            overlapping = [region1]
            used_indices.add(i)
            
            for j, region2 in enumerate(all_regions[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                if self._calculate_iou(region1.bbox, region2.bbox) > 0.5:
                    overlapping.append(region2)
                    used_indices.add(j)
                    
            # Choose best from overlapping regions
            best_region = max(overlapping, key=lambda r: r.confidence)
            combined_regions.append(best_region)
            
        return combined_regions
        
    def _calculate_iou(self, box1: List[int], box2: List[int]) -> float:
        """Calculate Intersection over Union for two boxes"""
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
            
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
        
    def _extract_fields(self, regions: List[TextRegion]) -> Dict[str, Any]:
        """Extract structured fields from text regions"""
        full_text = " ".join([r.text for r in regions])
        fields = {}
        
        for field_name, patterns in self.field_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    # Find confidence for this field
                    field_confidence = self._calculate_field_confidence(
                        matches[0] if isinstance(matches[0], str) else " ".join(matches[0]),
                        regions
                    )
                    
                    fields[field_name] = {
                        "value": matches[0] if isinstance(matches[0], str) else " ".join(matches[0]),
                        "confidence": field_confidence,
                        "source": f"pattern_{field_name}"
                    }
                    break
                    
        return fields
        
    def _calculate_field_confidence(self, field_text: str, regions: List[TextRegion]) -> float:
        """Calculate confidence for extracted field"""
        confidences = []
        for region in regions:
            if field_text.lower() in region.text.lower():
                confidences.append(region.confidence)
                
        return sum(confidences) / len(confidences) if confidences else 0.5
        
    def _generate_confidence_heatmap(
        self, 
        img: np.ndarray, 
        regions: List[TextRegion]
    ) -> str:
        """Generate confidence heatmap overlay"""
        # Create overlay
        overlay = np.zeros_like(img)
        
        for region in regions:
            x1, y1, x2, y2 = region.bbox
            
            # Choose color based on confidence
            if region.confidence >= 0.8:
                color = (0, 255, 0)  # Green - high confidence
            elif region.confidence >= 0.6:
                color = (0, 165, 255)  # Orange - medium confidence
            else:
                color = (0, 0, 255)  # Red - low confidence
                
            # Draw rectangle
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            
        # Apply transparency
        result = cv2.addWeighted(img, 0.7, overlay, 0.3, 0)
        
        # Convert to base64
        _, buffer = cv2.imencode('.png', result)
        heatmap_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/png;base64,{heatmap_base64}"
        
    def _merge_fields(self, pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge fields from multiple pages, choosing best confidence"""
        merged = {}
        
        for page in pages_data:
            for field_name, field_data in page.get('fields', {}).items():
                if field_name not in merged or field_data['confidence'] > merged[field_name]['confidence']:
                    merged[field_name] = {
                        **field_data,
                        'source_page': page['page']
                    }
                    
        return merged
        
    def _calculate_document_quality(self, pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall document quality"""
        all_confidences = []
        
        for page in pages_data:
            for region in page.get('regions', []):
                all_confidences.append(region['confidence'])
                
        if all_confidences:
            avg_confidence = sum(all_confidences) / len(all_confidences)
            min_confidence = min(all_confidences)
            max_confidence = max(all_confidences)
        else:
            avg_confidence = min_confidence = max_confidence = 0
            
        return {
            "score": round(avg_confidence * 100, 2),
            "metrics": {
                "average_confidence": round(avg_confidence, 3),
                "min_confidence": round(min_confidence, 3),
                "max_confidence": round(max_confidence, 3),
                "total_regions": len(all_confidences)
            }
        }
        
    def _extract_raw_text(self, pages_data: List[Dict[str, Any]]) -> str:
        """Extract raw text from all pages"""
        text_parts = []
        for page in pages_data:
            text_parts.append(page.get('raw_text', ''))
        return "\n\n".join(text_parts)
        
    def _get_engines_used(self, pages_data: List[Dict[str, Any]]) -> List[str]:
        """Get list of engines used in processing"""
        engines = set()
        for page in pages_data:
            for region in page.get('regions', []):
                engines.add(region['engine'])
        return list(engines)
        
    def _generate_document_id(self) -> str:
        """Generate unique document ID"""
        import uuid
        return str(uuid.uuid4())
        
    def _detect_file_type(
        self, 
        file_path: Optional[str] = None,
        file_bytes: Optional[bytes] = None
    ) -> str:
        """Detect file type from path or bytes"""
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.pdf':
                return 'pdf'
            elif ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                return 'image'
                
        if file_bytes:
            # Check PDF signature
            if file_bytes[:4] == b'%PDF':
                return 'pdf'
                
        return 'image'  # Default to image
        
    async def process_multipart_upload(
        self,
        files: List[Union[str, bytes]],
        file_types: Optional[List[str]] = None
    ) -> List[OCRResult]:
        """Process multiple files uploaded together"""
        tasks = []
        
        for i, file_data in enumerate(files):
            file_type = file_types[i] if file_types and i < len(file_types) else 'auto'
            
            if isinstance(file_data, str):
                tasks.append(self.process_document(file_path=file_data, file_type=file_type))
            else:
                tasks.append(self.process_document(file_bytes=file_data, file_type=file_type))
                
        results = await asyncio.gather(*tasks)
        return results