# 🧪 KisaanAI Deployment Testing Guide

Complete step-by-step guide to deploy and test your application.

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] AWS EC2 instance running (13.53.186.103)
- [ ] SSH key file (kisaanai.pem) in project directory
- [ ] Security group allows ports: 22, 80, 443, 8000, 3000, 5432
- [ ] Your API keys from SECRETS.md file

## Step 1: Test SSH Connection (2 minutes)

Open PowerShell in your project directory:

```powershell
# Set key permissions
icacls kisaanai.pem /inheritance:r
icacls kisaanai.pem /grant:r "%username%:R"

# Test connection
ssh -i kisaanai.pem ubuntu@13.53.186.103 "echo 'Connection successful!'"
```

**Expected Output**: `Connection successful!`

**If it fails**:
- Check instance is running in AWS Console
- Verify security group allows SSH (port 22) from your IP
- Ensure key file is correct

---

## Step 2: Install Dependencies (5 minutes)

Connect to EC2:
```powershell
ssh -i kisaanai.pem ubuntu@13.53.186.103
```

Run installation script:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git
sudo apt install git -y

# Verify installations
echo "=== Checking installations ==="
docker --version
docker-compose --version
git --version
echo "=== All dependencies installed! ==="
```

**Expected Output**:
```
Docker version 24.x.x
Docker Compose version v2.x.x
git version 2.x.x
```

**Logout and reconnect**:
```bash
exit
```

```powershell
ssh -i kisaanai.pem ubuntu@13.53.186.103
```

---

## Step 3: Clone Repository (2 minutes)

```bash
# Clone repository
git clone https://github.com/code-murf/kisaanai.git
cd kisaanai

# Verify files
ls -la

# Check important files exist
echo "=== Checking files ==="
[ -f docker-compose.prod.yml ] && echo "✓ docker-compose.prod.yml found" || echo "✗ docker-compose.prod.yml missing"
[ -f init.sql ] && echo "✓ init.sql found" || echo "✗ init.sql missing"
[ -f deploy-aws.sh ] && echo "✓ deploy-aws.sh found" || echo "✗ deploy-aws.sh missing"
[ -f .env.production ] && echo "✓ .env.production found" || echo "✗ .env.production missing"
```

**Expected Output**: All files should show ✓

---

## Step 4: Configure Environment (3 minutes)

```bash
# Copy environment template
cp .env.production .env

# Edit environment file
nano .env
```

**Update these values in nano**:

```bash
# Your EC2 IP (already correct)
AWS_PUBLIC_IP=13.53.186.103

# Create a secure database password
DB_PASSWORD=KisaanAI2026SecurePass!

# Add your API keys (from SECRETS.md)
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
SARVAM_API_KEY=YOUR_SARVAM_API_KEY_HERE
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY_HERE
ELEVENLABS_AGENT_ID=YOUR_ELEVENLABS_AGENT_ID_HERE
HUGGINGFACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE

# Generate secret key (run this command first)
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

**To save in nano**:
1. Press `Ctrl+X`
2. Press `Y`
3. Press `Enter`

**Verify configuration**:
```bash
# Check .env file (without showing secrets)
echo "=== Environment Configuration ==="
grep "AWS_PUBLIC_IP" .env
grep "DB_PASSWORD" .env | sed 's/=.*/=***HIDDEN***/'
echo "✓ Environment configured"
```

---

## Step 5: Deploy Application (10-15 minutes)

```bash
# Make deploy script executable
chmod +x deploy-aws.sh

# Run deployment
./deploy-aws.sh
```

**What to expect**:
1. ✓ Checking environment...
2. ✓ Setting up environment variables...
3. ✓ Building Docker images... (this takes longest, 5-10 min)
4. ✓ Starting containers...
5. ✓ Checking health...

**Monitor deployment**:
```bash
# In another terminal, watch logs
ssh -i kisaanai.pem ubuntu@13.53.186.103
cd kisaanai
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Step 6: Verify Deployment (5 minutes)

### 6.1 Check Container Status

```bash
docker-compose -f docker-compose.prod.yml ps
```

**Expected Output**:
```
NAME                  STATUS              PORTS
kisaanai-postgres     Up X minutes        0.0.0.0:5432->5432/tcp
kisaanai-backend      Up X minutes        0.0.0.0:8000->8000/tcp
kisaanai-frontend     Up X minutes        0.0.0.0:3000->3000/tcp
kisaanai-nginx        Up X minutes        0.0.0.0:80->80/tcp
```

All should show "Up" status.

### 6.2 Test Database

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT version();"

# Check tables
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "\dt"

# Check sample data
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT count(*) FROM commodities;"
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT count(*) FROM mandis;"
```

**Expected Output**:
- PostgreSQL version info
- List of tables (users, commodities, mandis, etc.)
- Commodities count: 10
- Mandis count: 5

### 6.3 Test Backend

```bash
# Health check
curl http://localhost:8000/health

# API test
curl http://localhost:8000/api/v1/commodities

# Check logs
docker-compose -f docker-compose.prod.yml logs backend --tail=50
```

**Expected Output**:
- Health: `{"status":"healthy"}`
- Commodities: JSON array with commodity data
- Logs: No errors

### 6.4 Test Frontend

```bash
# Frontend check
curl -I http://localhost:3000

# Check logs
docker-compose -f docker-compose.prod.yml logs frontend --tail=50
```

**Expected Output**:
- HTTP/1.1 200 OK
- Logs: No errors

### 6.5 Test Nginx

```bash
# Nginx check
curl -I http://localhost

# Test API through Nginx
curl http://localhost/api/v1/commodities

# Check logs
docker-compose -f docker-compose.prod.yml logs nginx --tail=50
```

**Expected Output**:
- HTTP/1.1 200 OK
- Commodities data
- Logs: No errors

---

## Step 7: External Access Test (2 minutes)

**From your local machine** (not EC2), open browser:

### Test URLs:

1. **Frontend**: http://13.53.186.103
   - Should show KisaanAI dashboard
   - Check if page loads completely

2. **Backend API**: http://13.53.186.103/api/v1/commodities
   - Should show JSON data

3. **API Docs**: http://13.53.186.103/docs
   - Should show Swagger UI

4. **Health Check**: http://13.53.186.103/health
   - Should show `{"status":"healthy"}`

**Test from PowerShell**:
```powershell
# Test from your local machine
Invoke-RestMethod -Uri "http://13.53.186.103/health"
Invoke-RestMethod -Uri "http://13.53.186.103/api/v1/commodities"
```

---

## Step 8: Feature Testing (10 minutes)

### 8.1 Test Dashboard

Open http://13.53.186.103 in browser:

- [ ] Dashboard loads
- [ ] Weather widget shows data
- [ ] Price charts display
- [ ] Mandi map appears
- [ ] No console errors (F12 → Console)

### 8.2 Test API Endpoints

```bash
# On EC2
cd ~/kisaanai

# Test commodities
curl http://localhost:8000/api/v1/commodities | jq

# Test mandis
curl http://localhost:8000/api/v1/mandis | jq

# Test weather (if implemented)
curl http://localhost:8000/api/v1/weather?district=Delhi | jq

# Test forecasts (if implemented)
curl http://localhost:8000/api/v1/forecasts/wheat?days=7 | jq
```

### 8.3 Test Database Queries

```bash
# Check price history
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT * FROM commodities LIMIT 5;"

# Check mandis
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT name, district, state FROM mandis;"

# Check database size
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT pg_size_pretty(pg_database_size('kisaanai'));"
```

---

## Step 9: Performance Testing (5 minutes)

### 9.1 Check Resource Usage

```bash
# Container stats
docker stats --no-stream

# Disk usage
df -h

# Memory usage
free -h

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs --tail=100 | grep -i error
```

### 9.2 Response Time Test

```bash
# Test backend response time
time curl -s http://localhost:8000/health > /dev/null

# Test frontend response time
time curl -s http://localhost:3000 > /dev/null

# Test API response time
time curl -s http://localhost:8000/api/v1/commodities > /dev/null
```

**Expected**: All should complete in < 1 second

---

## Step 10: Security Check (3 minutes)

### 10.1 Check Exposed Ports

```bash
# Check listening ports
sudo netstat -tlnp | grep -E ':(80|443|8000|3000|5432)'
```

### 10.2 Check Security Group

**In AWS Console**:
1. Go to EC2 → Instances
2. Select your instance
3. Security tab → Security groups
4. Verify inbound rules:
   - SSH (22): Your IP only
   - HTTP (80): 0.0.0.0/0
   - HTTPS (443): 0.0.0.0/0

### 10.3 Check Environment Variables

```bash
# Ensure secrets are not exposed
docker-compose -f docker-compose.prod.yml config | grep -i "password\|key\|secret" | head -5
```

---

## Troubleshooting Guide

### Issue: Container won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs [service-name]

# Restart specific service
docker-compose -f docker-compose.prod.yml restart [service-name]

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Issue: Database connection failed

```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai -c "SELECT 1;"
```

### Issue: Frontend not loading

```bash
# Check frontend logs
docker-compose -f docker-compose.prod.yml logs frontend

# Check if port 3000 is accessible
curl http://localhost:3000

# Rebuild frontend
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

### Issue: Out of memory

```bash
# Check memory
free -h

# If low, upgrade instance type:
# AWS Console → Stop instance → Change type to t3.medium → Start
```

---

## Success Checklist

- [ ] All 4 containers running (postgres, backend, frontend, nginx)
- [ ] Database initialized with tables and sample data
- [ ] Backend health check returns healthy
- [ ] Frontend loads in browser
- [ ] API returns data
- [ ] No errors in logs
- [ ] External access works from browser
- [ ] Response times < 1 second

---

## Final Verification Commands

Run this complete test:

```bash
#!/bin/bash
echo "=== KisaanAI Deployment Test ==="
echo ""

echo "1. Container Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""

echo "2. Database Test:"
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d kisaanai -c "SELECT count(*) as tables FROM information_schema.tables WHERE table_schema='public';"
echo ""

echo "3. Backend Health:"
curl -s http://localhost:8000/health | jq
echo ""

echo "4. API Test:"
curl -s http://localhost:8000/api/v1/commodities | jq '. | length'
echo ""

echo "5. Frontend Test:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:3000
echo ""

echo "6. Nginx Test:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost
echo ""

echo "=== Test Complete ==="
echo ""
echo "Your application is live at: http://13.53.186.103"
```

---

**Estimated Total Time**: 30-40 minutes
**Status**: Ready to Deploy and Test! 🚀
