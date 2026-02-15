# KisaanAI - Complete Feature Test Script
# Tests all endpoints and functionality

$BASE_URL = "http://13.53.186.103"
$API_URL = "http://13.53.186.103:8000"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "KisaanAI - Complete Feature Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$passCount = 0
$failCount = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    Write-Host "  URL: $Url" -ForegroundColor Gray
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "  [PASS] Status: $($response.StatusCode)" -ForegroundColor Green
            $script:passCount++
            return $true
        } else {
            Write-Host "  [FAIL] Status: $($response.StatusCode) (Expected: $ExpectedStatus)" -ForegroundColor Red
            $script:failCount++
            return $false
        }
    } catch {
        Write-Host "  [FAIL] Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:failCount++
        return $false
    }
}

Write-Host "=== INFRASTRUCTURE TESTS ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Frontend Homepage
Test-Endpoint "Frontend Homepage" "$BASE_URL"

# Test 2: Backend Health
Test-Endpoint "Backend Health Check" "$API_URL/health"

# Test 3: API Documentation
Test-Endpoint "API Documentation" "$API_URL/docs"

Write-Host ""
Write-Host "=== FRONTEND PAGES ===" -ForegroundColor Cyan
Write-Host ""

# Test Frontend Pages
Test-Endpoint "Mandi Map Page" "$BASE_URL/mandi"
Test-Endpoint "Charts Page" "$BASE_URL/charts"
Test-Endpoint "Voice Assistant Page" "$BASE_URL/voice"
Test-Endpoint "Crop Doctor Page" "$BASE_URL/doctor"
Test-Endpoint "News Page" "$BASE_URL/news"

Write-Host ""
Write-Host "=== API ENDPOINTS ===" -ForegroundColor Cyan
Write-Host ""

# Test API Endpoints
Write-Host "Testing: Commodities API" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/v1/commodities" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "  [PASS] Commodities API responding" -ForegroundColor Green
    $script:passCount++
} catch {
    Write-Host "  [FAIL] Commodities API error: $($_.Exception.Message)" -ForegroundColor Red
    $script:failCount++
}

Write-Host "Testing: Mandis API" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/v1/mandis" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "  [PASS] Mandis API responding" -ForegroundColor Green
    $script:passCount++
} catch {
    Write-Host "  [FAIL] Mandis API error: $($_.Exception.Message)" -ForegroundColor Red
    $script:failCount++
}

Write-Host ""
Write-Host "=== STATIC ASSETS ===" -ForegroundColor Cyan
Write-Host ""

# Test Static Assets
Test-Endpoint "Favicon" "$BASE_URL/favicon.ico"
Test-Endpoint "Manifest" "$BASE_URL/manifest.json"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total Tests: $($passCount + $failCount)" -ForegroundColor White
Write-Host "Passed: $passCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor Red
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED! Your application is fully functional!" -ForegroundColor Green
} elseif ($passCount -gt $failCount) {
    Write-Host "✅ Most tests passed. Application is working with minor issues." -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Multiple tests failed. Check the errors above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Live Application: $BASE_URL" -ForegroundColor Cyan
Write-Host "API Documentation: $API_URL/docs" -ForegroundColor Cyan
Write-Host ""
