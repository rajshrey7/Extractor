"""
Test script to verify the OCR setup is working correctly
"""
import os
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")
    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'cv2': 'OpenCV',
        'easyocr': 'EasyOCR',
        'ultralytics': 'Ultralytics',
        'numpy': 'NumPy',
        'PIL': 'Pillow'
    }
    
    missing = []
    for module, name in required_packages.items():
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - MISSING")
            missing.append(name)
    
    return len(missing) == 0

def check_model_file():
    """Check if model file exists"""
    print("\nChecking model file...")
    model_path = "Mymodel.pt"
    if os.path.exists(model_path):
        size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
        print(f"  ✅ Model file found: {model_path} ({size:.2f} MB)")
        return True
    else:
        print(f"  ❌ Model file not found: {model_path}")
        print(f"     Please download it from the link in mymodel.md")
        return False

def check_files():
    """Check if required files exist"""
    print("\nChecking required files...")
    required_files = ['app.py', 'index.html']
    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            all_exist = False
    return all_exist

def main():
    print("="*60)
    print("OCR Setup Verification")
    print("="*60)
    
    deps_ok = check_dependencies()
    model_ok = check_model_file()
    files_ok = check_files()
    
    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    
    if deps_ok and model_ok and files_ok:
        print("✅ All checks passed! You're ready to run the server.")
        print("\nTo start the server, run:")
        print("  python app.py")
        print("\nThen open your browser to: http://localhost:8000")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        if not deps_ok:
            print("\nTo install dependencies, run:")
            print("  pip install -r requirements_web.txt")
        if not model_ok:
            print("\nDownload the model file from the link in mymodel.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())

