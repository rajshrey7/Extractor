import requests
import os
import cv2
import numpy as np

def create_dummy_image():
    # Create a simple image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img, (20, 20), (80, 80), (255, 255, 255), -1)
    success, encoded_img = cv2.imencode('.jpg', img)
    return encoded_img.tobytes()

def verify_api():
    url = "http://localhost:8001/api/camera_upload"
    # Fallback port
    try:
        requests.get("http://localhost:8001")
    except:
        url = "http://localhost:8002/api/camera_upload"
        print("Using port 8002")

    print(f"Testing URL: {url}")
    
    img_bytes = create_dummy_image()
    files = {'image': ('test.jpg', img_bytes, 'image/jpeg')}
    
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response keys:", data.keys())
            if 'quality' in data:
                print("✅ 'quality' field found in response!")
                print("Quality Data:", data['quality'])
            else:
                print("❌ 'quality' field NOT found in response.")
                print("Server code might not be updated. Restart required.")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Server might not be running.")

if __name__ == "__main__":
    verify_api()
