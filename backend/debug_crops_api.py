
import requests
import json

def test_crop_recommendation():
    url = "http://localhost:8000/api/v1/crops/recommend"
    params = {
        "n": 150,
        "p": 60,
        "k": 50,
        "ph": 6.5,
        "location": "Delhi"
    }
    
    try:
        response = requests.get(url, params=params)
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
    test_crop_recommendation()
