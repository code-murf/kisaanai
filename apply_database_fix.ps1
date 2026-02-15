# Apply database schema fix to production
# Run this script on Windows

$EC2_IP = "13.53.186.103"
$SSH_KEY = "kisaanai.pem"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "KisaanAI - Database Schema Fix" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Copying SQL fix file to EC2..." -ForegroundColor Yellow
scp -i $SSH_KEY fix_database_schema.sql ubuntu@${EC2_IP}:/home/ubuntu/kisaanai/

Write-Host ""
Write-Host "Step 2: Applying database fixes..." -ForegroundColor Yellow

# Create a temporary script file
$scriptContent = @'
cd /home/ubuntu/kisaanai

echo "Applying schema fixes..."
sudo docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d kisaanai < fix_database_schema.sql

echo ""
echo "Restarting backend to apply changes..."
sudo docker-compose -f docker-compose.prod.yml restart backend

echo ""
echo "Waiting for backend to start..."
sleep 5

echo ""
echo "Testing APIs..."
curl -s http://localhost:8000/health
echo ""
curl -s http://localhost:8000/api/v1/commodities
echo ""
curl -s http://localhost:8000/api/v1/mandis
'@

$scriptContent | ssh -i $SSH_KEY ubuntu@$EC2_IP

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Database fix applied successfully!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Test the APIs:" -ForegroundColor Cyan
Write-Host "  Commodities: http://13.53.186.103:8000/api/v1/commodities" -ForegroundColor White
Write-Host "  Mandis: http://13.53.186.103:8000/api/v1/mandis" -ForegroundColor White
Write-Host ""

# Test the APIs
Write-Host "Testing APIs from local machine..." -ForegroundColor Yellow
Write-Host ""

Write-Host "Testing Commodities API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://13.53.186.103:8000/api/v1/commodities" -TimeoutSec 10
    Write-Host "  [SUCCESS] Commodities API working! Found $($response.data.Count) commodities" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Commodities API error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Testing Mandis API..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://13.53.186.103:8000/api/v1/mandis" -TimeoutSec 10
    Write-Host "  [SUCCESS] Mandis API working! Found $($response.data.Count) mandis" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Mandis API error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
