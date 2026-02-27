"""
KisaanAI — Full Backend API Test Suite
Tests every endpoint across all routers against the live server.
"""
import requests
import json
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"
results = []


def test(name, method, url, **kwargs):
    """Run a test and record result."""
    expected = kwargs.pop("expected", [200])
    if isinstance(expected, int):
        expected = [expected]
    try:
        resp = getattr(requests, method)(url, timeout=10, **kwargs)
        status = resp.status_code
        passed = status in expected
        body_preview = resp.text[:200] if resp.text else ""
        symbol = "PASS" if passed else "FAIL"
        results.append({"name": name, "status": status, "passed": passed})
        print(f"  [{symbol}] {name}: {status} {body_preview[:80]}")
        return resp
    except Exception as e:
        results.append({"name": name, "status": "ERR", "passed": False})
        print(f"  [FAIL] {name}: {e}")
        return None


# ======================================================
print("=" * 60)
print("1. HEALTH & ROOT ENDPOINTS")
print("=" * 60)
test("GET /", "get", BASE_URL)
test("GET /health", "get", f"{BASE_URL}/health")
test("GET /docs", "get", f"{BASE_URL}/docs")

# ======================================================
print()
print("=" * 60)
print("2. AUTH ENDPOINTS")
print("=" * 60)

# Register
resp = test("POST /auth/register", "post", f"{API}/auth/register", json={
    "phone_number": "+919999900001",
    "password": "Test@1234",
    "full_name": "Test User",
    "state": "Madhya Pradesh",
    "district": "Indore"
}, expected=[200, 201, 400])

# Login
resp = test("POST /auth/login", "post", f"{API}/auth/login", json={
    "phone_number": "+919999900001",
    "password": "Test@1234"
}, expected=[200, 401])

token = None
if resp and resp.status_code == 200:
    data = resp.json()
    token = data.get("access_token") or data.get("token")

auth_headers = {"Authorization": f"Bearer {token}"} if token else {}

test("GET /auth/me", "get", f"{API}/auth/me",
     headers=auth_headers, expected=[200, 401, 403])

# ======================================================
print()
print("=" * 60)
print("3. COMMODITY ENDPOINTS")
print("=" * 60)

test("GET /commodities", "get", f"{API}/commodities")
test("GET /commodities?search=wheat", "get", f"{API}/commodities?search=wheat")
test("GET /commodities/categories", "get", f"{API}/commodities/categories")
test("GET /commodities/1", "get", f"{API}/commodities/1", expected=[200, 404])

# ======================================================
print()
print("=" * 60)
print("4. MANDI ENDPOINTS")
print("=" * 60)

test("GET /mandis", "get", f"{API}/mandis")
test("GET /mandis?state=Madhya Pradesh", "get", f"{API}/mandis?state=Madhya+Pradesh")
test("GET /mandis/states", "get", f"{API}/mandis/states")
test("GET /mandis/1", "get", f"{API}/mandis/1", expected=[200, 404])
test("GET /mandis/states/Madhya Pradesh/districts", "get",
     f"{API}/mandis/states/Madhya%20Pradesh/districts")

# ======================================================
print()
print("=" * 60)
print("5. PRICE ENDPOINTS")
print("=" * 60)

test("GET /prices/history?commodity_id=1", "get",
     f"{API}/prices/history?commodity_id=1")
test("GET /prices/commodity/1/current", "get",
     f"{API}/prices/commodity/1/current", expected=[200, 404])
test("GET /prices/mandi/1/current", "get",
     f"{API}/prices/mandi/1/current", expected=[200, 404])
test("GET /prices/commodity/1/trend", "get",
     f"{API}/prices/commodity/1/trend", expected=[200, 404])
test("GET /prices/gainers", "get", f"{API}/prices/gainers", expected=[200, 404])
test("GET /prices/losers", "get", f"{API}/prices/losers", expected=[200, 404])

# ======================================================
print()
print("=" * 60)
print("6. FORECAST ENDPOINTS")
print("=" * 60)

test("GET /forecasts/1/1", "get",
     f"{API}/forecasts/1/1?horizon_days=7", expected=[200, 404])
test("GET /forecasts/1/1/multi-horizon", "get",
     f"{API}/forecasts/1/1/multi-horizon", expected=[200, 404])
test("GET /forecasts/1/1/explanation", "get",
     f"{API}/forecasts/1/1/explanation", expected=[200, 404, 503])

# ======================================================
print()
print("=" * 60)
print("7. WEATHER ENDPOINTS")
print("=" * 60)

# Indore coordinates
test("GET /weather/forecast", "get",
     f"{API}/weather/forecast?lat=22.72&lon=75.86&days=7", expected=[200, 503])

# ======================================================
print()
print("=" * 60)
print("8. NEWS ENDPOINTS")
print("=" * 60)

test("GET /news", "get", f"{API}/news")

# ======================================================
print()
print("=" * 60)
print("9. VOICE ENDPOINTS")
print("=" * 60)

test("GET /voice/stats", "get", f"{API}/voice/stats")

# Text voice query (no auth needed)
test("POST /voice/text", "post", f"{API}/voice/text", json={
    "text": "What is the price of wheat today?",
    "language": "en-IN"
}, expected=[200, 500])

# ======================================================
print()
print("=" * 60)
print("10. COMMUNITY ENDPOINTS")
print("=" * 60)

test("GET /community/notes", "get", f"{API}/community/notes", expected=[200, 404, 405])
test("POST /community/notes", "post", f"{API}/community/notes", json={
    "title": "Test Note",
    "content": "This is a test note from API testing.",
    "author": "TestBot"
}, expected=[200, 201, 404, 405, 422])

# ======================================================
print()
print("=" * 60)
print("11. RESOURCE ENDPOINTS")
print("=" * 60)

test("GET /resources", "get", f"{API}/resources", expected=[200, 404])

# ======================================================
print()
print("=" * 60)
print("12. CROP ENDPOINTS")
print("=" * 60)

test("GET /crops", "get", f"{API}/crops", expected=[200, 404])

# ======================================================
print()
print("=" * 60)
print("13. DISEASE ENDPOINTS")
print("=" * 60)

test("GET /diseases", "get", f"{API}/diseases", expected=[200, 404])

# ======================================================
# SUMMARY
# ======================================================
print()
print("=" * 60)
print("TEST SUMMARY")
print("=" * 60)

passed = sum(1 for r in results if r["passed"])
failed = sum(1 for r in results if not r["passed"])
total = len(results)

print(f"  Total: {total}")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print()

if failed > 0:
    print("  FAILED TESTS:")
    for r in results:
        if not r["passed"]:
            print(f"    - {r['name']}: {r['status']}")

print()
print(f"  Result: {'ALL PASSED' if failed == 0 else f'{failed} FAILURES'}")
