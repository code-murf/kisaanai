# 🚀 Commands to Deploy KisaanAI - Step by Step

## ⚠️ IMPORTANT: Run these commands in order!

---

## STEP 1: Verify .env file exists (Already done ✅)

Your `.env` file is ready with all credentials.

---

## STEP 2: Test Current Status (Optional - to see it's not deployed yet)

```powershell
.\test-live-deployment.ps1
```

Expected: All tests will FAIL (because nothing is deployed yet)

---

## STEP 3: Deploy to AWS EC2

### Option A: Automated Deployment (RECOMMENDED - Easiest!)

Run this ONE command:

```powershell
.\deploy-step-by-step.ps1
```

This will automatically:
- Copy all files to EC2
- Install Docker if needed
- Build containers
- Start all services
- Run health checks

**Then skip to STEP 4!**

---

### Option B: Manual Deployment (If automated fails)

#### 3.1: Copy files to EC2

```powershell
scp -i kisaanai.pem -r backend frontend docker-compose.prod.yml nginx.conf init.sql .env ubuntu@13.53.186.103:/home/ubuntu/kisaanai/
```

#### 3.2: SSH into EC2

```powershell
ssh -i kisaanai.pem ubuntu@13.53.186.103
```

#### 3.3: Install Docker (Run on EC2)

```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
```

#### 3.4: Logout and login again (to apply docker group)

```bash
exit
```

Then SSH again:

```powershell
ssh -i kisaanai.pem ubuntu@13.53.186.103
```

#### 3.5: Deploy the application (Run on EC2)

```bash
cd /home/ubuntu/kisaanai
docker-compose -f docker-compose.prod.yml up -d
```

#### 3.6: Check if containers are running (Run on EC2)

```bash
docker-compose -f docker-compose.prod.yml ps
```

Expected output: 4 containers running (postgres, backend, frontend, nginx)

#### 3.7: Check logs (Run on EC2)

```bash
docker-compose -f docker-compose.prod.yml logs
```

#### 3.8: Exit SSH

```bash
exit
```

---

## STEP 4: Test Deployment (Run on your Windows machine)

```powershell
.\test-live-deployment.ps1
```

Expected: All tests should PASS ✅

---

## STEP 5: Open in Browser

Visit these URLs:

1. **Frontend:** http://13.53.186.103
2. **Backend Health:** http://13.53.186.103:8000/health
3. **API Commodities:** http://13.53.186.103:8000/api/v1/commodities
4. **API Mandis:** http://13.53.186.103:8000/api/v1/mandis

---

## 🔧 Troubleshooting Commands

### If deployment fails, SSH into EC2 and run:

```bash
# Check container status
docker ps -a

# Check logs for specific service
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs postgres
docker-compose -f docker-compose.prod.yml logs nginx

# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Rebuild and start
docker-compose -f docker-compose.prod.yml up -d --build

# Check disk space
df -h

# Check memory
free -h

# Check if ports are listening
sudo netstat -tulpn | grep -E '80|3000|8000|5432'
```

---

## 📋 Quick Reference

### Start services:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Stop services:
```bash
docker-compose -f docker-compose.prod.yml down
```

### View logs (follow mode):
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Check status:
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Restart a specific service:
```bash
docker-compose -f docker-compose.prod.yml restart backend
```

---

## ⚡ FASTEST WAY TO DEPLOY

Just run this ONE command on your Windows machine:

```powershell
.\deploy-step-by-step.ps1
```

Wait 10-15 minutes, then test:

```powershell
.\test-live-deployment.ps1
```

Done! 🎉

---

## 🆘 If Something Goes Wrong

1. Check AWS Security Group allows ports: 22, 80, 3000, 8000
2. Check EC2 instance is running
3. SSH into EC2 and check logs:
   ```bash
   ssh -i kisaanai.pem ubuntu@13.53.186.103
   cd /home/ubuntu/kisaanai
   docker-compose -f docker-compose.prod.yml logs
   ```

---

**Ready?** Start with STEP 3 Option A (automated deployment)! 🚀
