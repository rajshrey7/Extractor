
import sys
import os
import cv2
import numpy as np
import traceback

print("Python executable:", sys.executable)
print("Current working directory:", os.getcwd())

try:
    print("Importing app modules...")
    from app import initialize_models, process_image, yolo_model, ocr_reader
    print("Imports successful.")
except Exception as e:
    print("Error importing app modules:")
    traceback.print_exc()
    sys.exit(1)

def test_initialization():
    print("\nTesting model initialization...")
    try:
        initialize_models()
        from app import yolo_model, ocr_reader
        if yolo_model is None:
            print("❌ YOLO model failed to load.")
        else:
            print("✅ YOLO model loaded.")
            
        if ocr_reader is None:
            print("❌ EasyOCR reader failed to load.")
        else:
            print("✅ EasyOCR reader loaded.")
            
    except Exception as e:
        print("❌ Initialization error:")
        traceback.print_exc()

def test_processing():
    print("\nTesting image processing (with blank image)...")
    try:
        # Create a blank white image
        img = np.zeros((500, 500, 3), dtype=np.uint8)
        img.fill(255)
        
        # Add some text
        cv2.putText(img, "Test Name: John Doe", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Encode to bytes
        _, img_encoded = cv2.imencode('.jpg', img)
        img_bytes = img_encoded.tobytes()
        
        # Process
        result = process_image(img_bytes)
        print("✅ Processing successful!")
        print("Result keys:", result.keys())
        print("Extracted fields:", result.get('extracted_fields'))
        
    except Exception as e:
        print("❌ Processing error:")
        traceback.print_exc()

if __name__ == "__main__":
    test_initialization()
    test_processing()
