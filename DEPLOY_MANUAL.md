# 🚀 Manual Deployment Guide - Copy & Paste Commands

Follow these steps exactly. Each command is ready to copy and paste.

## Your Instance Details
- **IP**: 13.53.186.103
- **Key**: kisaanai.pem (in project root)

---

## Step 1: Connect to EC2

Open PowerShell in your project directory and run:

```powershell
# Set key permissions
icacls kisaanai.pem /inheritance:r
icacls kisaanai.pem /grant:r "%username%:R"

# Connect
ssh -i kisaanai.pem ubuntu@13.53.186.103
```

Type `yes` if asked about host authenticity.

---

## Step 2: Install Docker (on EC2)

Once connected, copy and paste this entire block:

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
docker --version
docker-compose --version
git --version

echo "✅ All dependencies installed!"
```

**Then logout and reconnect:**

```bash
exit
```

```powershell
ssh -i kisaanai.pem ubuntu@13.53.186.103
```

---

## Step 3: Clone Repository (on EC2)

```bash
# Clone repo
git clone https://github.com/code-murf/kisaanai.git
cd kisaanai

# Verify
ls -la
```

You should see all project files.

---

## Step 4: Configure Environment (on EC2)

```bash
# Copy template
cp .env.production .env

# Edit environment file
nano .env
```

**Update these lines in nano:**

1. Find `DB_PASSWORD=YOUR_SUPABASE_PASSWORD`
2. Replace with your actual Supabase password
3. All other values are already filled

**To save in nano:**
- Press `Ctrl+X`
- Press `Y`
- Press `Enter`

---

## Step 5: Deploy! (on EC2)

```bash
# Make script executable
chmod +x deploy-aws.sh

# Run deployment
./deploy-aws.sh
```

**This will take 10-15 minutes.** You'll see:
- ✓ Checking environment
- ✓ Setting up environment variables
- ✓ Building Docker images (this takes longest)
- ✓ Starting containers
- ✓ Checking health

---

## Step 6: Verify Deployment (on EC2)

```bash
# Check containers are running
docker-compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                STATUS              PORTS
kisaanai-backend    Up X minutes        0.0.0.0:8000->8000/tcp
kisaanai-frontend   Up X minutes        0.0.0.0:3000->3000/tcp
kisaanai-nginx      Up X minutes        0.0.0.0:80->80/tcp
```

```bash
# Test backend
curl http://localhost:8000/health
```

Expected: `{"status":"healthy"}`

```bash
# Test frontend
curl http://localhost:3000
```

Expected: HTML content

---

## Step 7: Access Your App! 🎉

Open in your browser:

```
http://13.53.186.103
```

You should see the KisaanAI dashboard!

---

## Troubleshooting

### Can't connect via SSH?

**Check security group:**
1. Go to AWS Console → EC2 → Instances
2. Select your instance
3. Click "Security" tab
4. Click security group link
5. Edit inbound rules
6. Ensure SSH (22) is allowed from your IP

### Can't access website?

**Check security group allows HTTP:**
1. Edit inbound rules
2. Add: HTTP (80) from 0.0.0.0/0
3. Add: HTTPS (443) from 0.0.0.0/0

### Deployment failed?

**View logs:**
```bash
docker-compose -f docker-compose.prod.yml logs
```

**Restart deployment:**
```bash
docker-compose -f docker-compose.prod.yml down
./deploy-aws.sh
```

### Backend won't start?

**Check database password:**
```bash
nano .env
# Verify DB_PASSWORD is correct
```

**Check logs:**
```bash
docker-compose -f docker-compose.prod.yml logs backend
```

### Out of memory?

**Check memory:**
```bash
free -h
```

If low, upgrade instance:
1. Stop instance in AWS Console
2. Actions → Instance Settings → Change Instance Type
3. Select t3.medium or t3.large
4. Start instance
5. Reconnect and redeploy

---

## Useful Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Backend only
docker-compose -f docker-compose.prod.yml logs -f backend

# Frontend only
docker-compose -f docker-compose.prod.yml logs -f frontend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100
```

### Restart Services
```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Check Status
```bash
# Container status
docker-compose -f docker-compose.prod.yml ps

# Resource usage
docker stats

# Disk usage
df -h
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

---

## Your Application URLs

- **Frontend**: http://13.53.186.103
- **Backend API**: http://13.53.186.103/api
- **API Docs**: http://13.53.186.103/docs
- **Health Check**: http://13.53.186.103/health

---

## Next Steps

1. ✅ Test all features
2. ✅ Setup custom domain (optional)
3. ✅ Configure SSL certificate
4. ✅ Setup monitoring

---

**Need Help?**
- Check logs for errors
- See AWS_DEPLOYMENT.md for detailed guide
- Ensure all ports are open in security group

**Estimated Time**: 30 minutes
**Status**: Ready to Deploy! 🚀
