"""
Simple server startup script with error handling
"""
import sys
import os

# Fix Windows console encoding for emoji/Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

print("="*60)
print("Starting OCR Server...")
print("="*60)

try:
    import uvicorn
    from app import app
    
    print("\n✅ All imports successful!")
    print("\n🚀 Starting server at http://localhost:8000")
    print("   Press Ctrl+C to stop the server\n")
    print("="*60 + "\n")
    
    try:
        print("Attempting to start on port 8001...")
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
    except Exception as e:
        print(f"Failed to start on port 8001: {e}")
        print("Attempting to start on port 8002...")
        uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nPlease install dependencies:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

