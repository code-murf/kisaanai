
import requests
import json
from datetime import datetime

def test_weather_forecast():
    url = "http://localhost:8000/api/v1/weather/forecast"
    params = {
        "lat": 28.7041,
        "lon": 77.1025,
        "days": 5
    }
    
    print(f"Fetching weather for: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Received {len(data)} days of forecast.")
            if len(data) > 0:
                print("First day forecast:")
                print(json.dumps(data[0], indent=2))
        else:
            print("Error Response:")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_weather_forecast()
