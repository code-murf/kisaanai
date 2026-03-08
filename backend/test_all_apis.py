"""Comprehensive KisaanAI API test script."""
import requests
import json
import sys

BASE = "http://localhost:8000"
TIMEOUT = 10

results = []

def test(name, method, url, timeout=TIMEOUT, **kwargs):
    try:
        r = getattr(requests, method)(url, timeout=timeout, **kwargs)
        ct = r.headers.get("content-type", "")
        if "application/json" in ct:
            body = r.json()
            preview = json.dumps(body, ensure_ascii=False, default=str)[:300]
        else:
            preview = r.text[:200]
        status = "PASS" if r.status_code < 400 else "FAIL"
        print(f"  [{status}] {name}: {r.status_code} | {preview}")
        results.append((name, r.status_code))
        return r.status_code
    except Exception as e:
        print(f"  [ERR!] {name}: {e}")
        results.append((name, 0))
        return 0

print("=" * 70)
print("KisaanAI  -  Comprehensive API Test Suite")
print("=" * 70)

# ------ CORE ------
print("\n--- Core ---")
test("Health", "get", f"{BASE}/health")
test("Root", "get", f"{BASE}/")

# ------ COMMODITIES ------
print("\n--- Commodities ---")
test("List commodities", "get", f"{BASE}/api/v1/commodities")
test("Commodity categories", "get", f"{BASE}/api/v1/commodities/categories")
test("Commodity by ID (1)", "get", f"{BASE}/api/v1/commodities/1")

# ------ MANDIS ------
print("\n--- Mandis ---")
test("List mandis", "get", f"{BASE}/api/v1/mandis")
test("Mandi states", "get", f"{BASE}/api/v1/mandis/states")
test("Mandi by ID (1)", "get", f"{BASE}/api/v1/mandis/1")

# ------ PRICES ------
print("\n--- Prices ---")
test("Price history", "get", f"{BASE}/api/v1/prices?commodity_id=1")
test("Current by commodity", "get", f"{BASE}/api/v1/prices/current/commodity/1")
test("Current by mandi", "get", f"{BASE}/api/v1/prices/current/mandi/1")
test("Price trend", "get", f"{BASE}/api/v1/prices/trend/1?days=30")
test("Top gainers", "get", f"{BASE}/api/v1/prices/gainers")
test("Top losers", "get", f"{BASE}/api/v1/prices/losers")

# ------ FORECASTS ------
print("\n--- Forecasts ---")
test("Forecast (1,1)", "get", f"{BASE}/api/v1/forecasts/1/1?horizon_days=7", timeout=15)

# ------ WEATHER ------
print("\n--- Weather ---")
test("Weather forecast", "get", f"{BASE}/api/v1/weather/forecast?lat=28.6139&lon=77.209&days=3", timeout=15)

# ------ CROPS ------
print("\n--- Crops ---")
test("Crop recommend", "get", f"{BASE}/api/v1/crops/recommend?n=40&p=20&k=30&ph=6.5")

# ------ NEWS ------
print("\n--- News ---")
test("News", "get", f"{BASE}/api/v1/news")

# ------ COMMUNITY ------
print("\n--- Community ---")
test("Community notes", "get", f"{BASE}/api/v1/community/notes")

# ------ RESOURCES ------
print("\n--- Resources ---")
test("Resource optimize", "get", f"{BASE}/api/v1/resources/optimize?crop=Potato&acres=1")

# ------ ROUTING ------
print("\n--- Routing ---")
test("Transport modes", "get", f"{BASE}/api/v1/routing/transport-modes")
test("Optimization goals", "get", f"{BASE}/api/v1/routing/optimization-goals")
test("Routing recommend", "post", f"{BASE}/api/v1/routing/recommend",
     json={"commodity_id": 1, "latitude": 28.6139, "longitude": 77.209,
            "quantity_quintals": 1, "max_distance_km": 100}, timeout=15)

# ------ SUMMARY ------
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
passed = sum(1 for _, c in results if 200 <= c < 400)
failed = sum(1 for _, c in results if c >= 400 or c == 0)
for name, code in results:
    icon = "PASS" if 200 <= code < 400 else "FAIL"
    print(f"  [{icon}] {name}: {code}")
print(f"\nTotal: {passed}/{len(results)} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
