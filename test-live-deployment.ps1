# KisaanAI Live Deployment Test Script
# Tests the live deployment on AWS EC2

$EC2_IP = "13.53.186.103"
$FRONTEND_URL = "http://$EC2_IP"
$BACKEND_URL = "http://$EC2_IP:8000"
$NGINX_URL = "http://$EC2_IP"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "KisaanAI Live Deployment Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Check if EC2 instance is reachable
Write-Host "[1/8] Testing EC2 Instance Connectivity..." -ForegroundColor Yellow
try {
    $ping = Test-Connection -ComputerName $EC2_IP -Count 2 -Quiet
    if ($ping) {
        Write-Host "✓ EC2 instance is reachable" -ForegroundColor Green
    } else {
        Write-Host "✗ EC2 instance is NOT reachable" -ForegroundColor Red
        Write-Host "  Check if instance is running in AWS Console" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Cannot ping EC2 instance" -ForegroundColor Red
}
Write-Host ""

# Test 2: Check Nginx (Port 80)
Write-Host "[2/8] Testing Nginx (Port 80)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $NGINX_URL -TimeoutSec 10 -UseBasicParsing
    Write-Host "✓ Nginx is responding (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ Nginx is NOT responding on port 80" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Test 3: Check Frontend (Port 3000)
Write-Host "[3/8] Testing Frontend (Port 3000)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$FRONTEND_URL`:3000" -TimeoutSec 10 -UseBasicParsing
    Write-Host "✓ Frontend is responding (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ Frontend is NOT responding on port 3000" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Test 4: Check Backend Health (Port 8000)
Write-Host "[4/8] Testing Backend Health Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BACKEND_URL/health" -TimeoutSec 10
    Write-Host "✓ Backend health check passed" -ForegroundColor Green
    Write-Host "  Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Backend health check failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Test 5: Check Backend API - Commodities
Write-Host "[5/8] Testing Backend API - Commodities..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BACKEND_URL/api/v1/commodities" -TimeoutSec 10
    if ($response.Count -gt 0) {
        Write-Host "✓ Commodities API working ($($response.Count) items)" -ForegroundColor Green
    } else {
        Write-Host "⚠ Commodities API responding but no data" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Commodities API failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Test 6: Check Backend API - Mandis
Write-Host "[6/8] Testing Backend API - Mandis..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BACKEND_URL/api/v1/mandis" -TimeoutSec 10
    if ($response.Count -gt 0) {
        Write-Host "✓ Mandis API working ($($response.Count) items)" -ForegroundColor Green
    } else {
        Write-Host "⚠ Mandis API responding but no data" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Mandis API failed" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Test 7: Check Database Connection (via Backend)
Write-Host "[7/8] Testing Database Connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BACKEND_URL/api/v1/commodities" -TimeoutSec 10
    Write-Host "✓ Database connection working (data retrieved)" -ForegroundColor Green
} catch {
    Write-Host "✗ Database connection issue" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
}
Write-Host ""

# Test 8: Check Security Group Settings
Write-Host "[8/8] Security Group Recommendations..." -ForegroundColor Yellow
Write-Host "  Ensure these ports are open in AWS Security Group:" -ForegroundColor Gray
Write-Host "  - Port 80 (HTTP) - for Nginx" -ForegroundColor Gray
Write-Host "  - Port 443 (HTTPS) - for SSL (optional)" -ForegroundColor Gray
Write-Host "  - Port 3000 (Frontend) - for direct access" -ForegroundColor Gray
Write-Host "  - Port 8000 (Backend) - for API access" -ForegroundColor Gray
Write-Host "  - Port 22 (SSH) - for deployment" -ForegroundColor Gray
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "If all tests failed, the deployment may not be running yet." -ForegroundColor Yellow
Write-Host "Follow these steps:" -ForegroundColor Yellow
Write-Host "1. SSH into EC2: ssh -i kisaanai.pem ubuntu@$EC2_IP" -ForegroundColor White
Write-Host "2. Run deployment: cd /home/ubuntu/kisaanai && docker-compose -f docker-compose.prod.yml up -d" -ForegroundColor White
Write-Host "3. Check logs: docker-compose -f docker-compose.prod.yml logs" -ForegroundColor White
Write-Host "4. Verify security group allows inbound traffic on ports 80, 3000, 8000" -ForegroundColor White
Write-Host ""
Write-Host "For detailed deployment instructions, see: DEPLOY_MANUAL.md" -ForegroundColor Cyan
Write-Host ""
