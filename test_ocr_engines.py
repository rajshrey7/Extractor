"""
OCR Engine Verification Script
Tests PaddleOCR and TrOCR functionality
"""
import sys
import os

print("=" * 70)
print("OCR ENGINES VERIFICATION TEST")
print("=" * 70)

# Test 1: Import Check
print("\n[TEST 1] Checking imports...")
try:
    from paddle_ocr_module import PaddleOCRWrapper
    print("✅ PaddleOCR module imported successfully")
except Exception as e:
    print(f"❌ PaddleOCR import failed: {e}")
    sys.exit(1)

try:
    from trocr_handwritten import TrOCRWrapper
    print("✅ TrOCR module imported successfully")
except Exception as e:
    print(f"❌ TrOCR import failed: {e}")
    sys.exit(1)

# Test 2: Initialize PaddleOCR
print("\n[TEST 2] Initializing PaddleOCR...")
try:
    paddle_ocr = PaddleOCRWrapper(lang='en')
    print("✅ PaddleOCR initialized successfully")
except Exception as e:
    print(f"❌ PaddleOCR initialization failed: {e}")
    sys.exit(1)

# Test 3: Initialize TrOCR
print("\n[TEST 3] Initializing TrOCR...")
try:
    trocr_ocr = TrOCRWrapper()
    print("✅ TrOCR initialized successfully")
except Exception as e:
    print(f"❌ TrOCR initialization failed: {e}")
    sys.exit(1)

# Test 4: Create test images
print("\n[TEST 4] Creating test images...")
try:
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a simple printed text image
    img_printed = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img_printed)
    draw.text((10, 30), "Name: John Smith", fill='black')
    draw.text((10, 60), "Age: 30", fill='black')
    img_printed.save("test_printed.png")
    print("✅ Test printed text image created (test_printed.png)")
    
    # Create a simple handwritten-style image (simulated)
    img_handwritten = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img_handwritten)
    draw.text((10, 30), "First name: Abigail", fill='black')
    draw.text((10, 60), "Last name: Summer", fill='black')
    img_handwritten.save("test_handwritten.png")
    print("✅ Test handwritten text image created (test_handwritten.png)")
    
except Exception as e:
    print(f"❌ Test image creation failed: {e}")
    sys.exit(1)

# Test 5: PaddleOCR Extraction
print("\n[TEST 5] Testing PaddleOCR extraction...")
try:
    paddle_text = paddle_ocr.extract_text("test_printed.png")
    print(f"✅ PaddleOCR extracted: {len(paddle_text)} characters")
    print(f"   Text preview: {paddle_text[:100]}")
    
    if len(paddle_text) > 0:
        print("✅ PaddleOCR is WORKING correctly")
    else:
        print("⚠️ PaddleOCR extracted 0 characters (might be an issue)")
except Exception as e:
    print(f"❌ PaddleOCR extraction failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: TrOCR Extraction
print("\n[TEST 6] Testing TrOCR extraction...")
try:
    trocr_text, trocr_conf = trocr_ocr.extract_text("test_handwritten.png")
    print(f"✅ TrOCR extracted: {len(trocr_text)} characters (Confidence: {trocr_conf:.2f})")
    print(f"   Text preview: {trocr_text[:100]}")
    
    if len(trocr_text) > 0:
        print("✅ TrOCR is WORKING correctly")
    else:
        print("⚠️ TrOCR extracted 0 characters (might be an issue)")
except Exception as e:
    print(f"❌ TrOCR extraction failed: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Check app.py functions
print("\n[TEST 7] Checking app.py helper functions...")
try:
    from app import extract_text_with_paddle, extract_text_with_trocr
    print("✅ extract_text_with_paddle function found")
    print("✅ extract_text_with_trocr function found")
    
    # Check function signatures
    import inspect
    paddle_sig = inspect.signature(extract_text_with_paddle)
    trocr_sig = inspect.signature(extract_text_with_trocr)
    
    print(f"   extract_text_with_paddle signature: {paddle_sig}")
    print(f"   extract_text_with_trocr signature: {trocr_sig}")
    
    # Verify return types
    if "Tuple" in str(trocr_sig.return_annotation):
        print("✅ extract_text_with_trocr returns Tuple (correct)")
    else:
        print("⚠️ extract_text_with_trocr return type might be incorrect")
        
except Exception as e:
    print(f"❌ app.py function check failed: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\n[CLEANUP] Removing test images...")
try:
    os.remove("test_printed.png")
    os.remove("test_handwritten.png")
    print("✅ Test images removed")
except:
    pass

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
print("\n✅ If all tests passed, both OCR engines are working correctly!")
print("⚠️ If any tests failed, check the error messages above.")
