import requests
import sys

BASE_URL = "http://localhost:8000"

def check_endpoint(name, url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"✅ {name}: OK ({url})")
            return True
        else:
            print(f"❌ {name}: Failed ({response.status_code}) - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def main():
    print("🚀 Starting System Health Check...")
    results = []
    
    results.append(check_endpoint("Root", f"{BASE_URL}/"))
    results.append(check_endpoint("Health", f"{BASE_URL}/health"))
    results.append(check_endpoint("Docs", f"{BASE_URL}/docs"))
    
    # Check Price Trends (Mock Data)
    results.append(check_endpoint("Price Trend", f"{BASE_URL}/api/v1/prices/trend/1"))
    
    # Check Forecast (Mock Data)
    results.append(check_endpoint("Forecast", f"{BASE_URL}/api/v1/forecasts/1/1"))
    
    if all(results):
        print("\n✨ All systems operational!")
        sys.exit(0)
    else:
        print("\n⚠️ Some systems failed check.")
        sys.exit(1)

if __name__ == "__main__":
    main()
