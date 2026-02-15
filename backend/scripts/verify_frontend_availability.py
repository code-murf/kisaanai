import urllib.request
import sys

URL = "http://localhost:3000"

def verify_frontend():
    print(f"Checking {URL}...")
    try:
        with urllib.request.urlopen(URL) as response:
            if response.status == 200:
                print("✅ Frontend is reachable (200 OK)")
                content = response.read().decode('utf-8')
                if "<title>" in content:
                    print("✅ HTML content received")
                    return True
                else:
                    print("⚠️ Response received but looks like it might not be full HTML")
                    return True
            else:
                print(f"❌ Frontend returned status: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Failed to reach frontend: {e}")
        return False

if __name__ == "__main__":
    if verify_frontend():
        sys.exit(0)
    else:
        sys.exit(1)
