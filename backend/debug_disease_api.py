
import requests
import json
import os

def test_disease_detection():
    url = "http://localhost:8000/api/v1/diseases/diagnose"
    
    # Create a dummy image file if it doesn't exist (just text content is enough for mock logic if it only checks filename, 
    # but FastAPI UploadFile might expect valid image if I used image validation? 
    # My service only checks filename string. But UploadFile reads bytes.
    # I'll use the 'test_blight.png' I created earlier.
    
    file_path = "test_blight.png"
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Creating dummy.")
        with open(file_path, "wb") as f:
            f.write(b"fake image content")

    files = {'file': open(file_path, 'rb')}
    
    try:
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Error Response:")
            print(response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_disease_detection()
