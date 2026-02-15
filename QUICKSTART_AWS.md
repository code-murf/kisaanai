# 🚀 Quick Start: Deploy to AWS EC2 in 30 Minutes

Deploy both frontend and backend on a single AWS EC2 instance.

## What You'll Get

- ✅ Frontend + Backend on one server
- ✅ Nginx reverse proxy
- ✅ Docker containerized
- ✅ Auto-restart on failure
- ✅ Production-ready setup

## Step-by-Step Guide

### 1. Launch EC2 Instance (5 min)

1. Go to **AWS Console** → **EC2** → **Launch Instance**

2. **Configure**:
   ```
   Name: kisaanai-server
   AMI: Ubuntu Server 22.04 LTS
   Instance Type: t2.large (recommended)
   Key Pair: Create new or select existing
   ```

3. **Security Group** - Allow these ports:
   ```
   SSH (22) - Your IP only
   HTTP (80) - 0.0.0.0/0
   HTTPS (443) - 0.0.0.0/0
   ```

4. **Storage**: 30 GB

5. Click **Launch Instance**

6. **Note your Public IP** (e.g., `54.123.45.67`)

### 2. Connect to Server (2 min)

```bash
# Download your .pem key file
chmod 400 your-key.pem

# Connect
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### 3. Install Dependencies (5 min)

Run these commands on your EC2 instance:

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

# Logout and login again
exit
```

**Reconnect**:
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### 4. Clone and Setup (3 min)

```bash
# Clone repository
git clone https://github.com/code-murf/kisaanai.git
cd kisaanai

# Copy environment template
cp .env.production .env

# Edit environment variables
nano .env
```

**Update `.env` with your values**:
```bash
# Get your EC2 public IP
AWS_PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)

# Update these:
DB_PASSWORD=your_supabase_password
GROQ_API_KEY=gsk_...
SARVAM_API_KEY=sk_...
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_AGENT_ID=agent_...
HUGGINGFACE_TOKEN=hf_...

# Generate secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

Save (Ctrl+X, Y, Enter)

### 5. Deploy (10 min)

```bash
# Make script executable
chmod +x deploy-aws.sh

# Run deployment
./deploy-aws.sh
```

Wait for deployment to complete...

### 6. Verify (2 min)

```bash
# Check containers
docker-compose -f docker-compose.prod.yml ps

# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# Get your public URL
echo "Your app: http://$(curl -s http://checkip.amazonaws.com)"
```

### 7. Access Your App! 🎉

Open in browser:
```
http://YOUR_EC2_PUBLIC_IP
```

## Your App URLs

- **Frontend**: `http://YOUR_EC2_PUBLIC_IP`
- **Backend API**: `http://YOUR_EC2_PUBLIC_IP/api`
- **API Docs**: `http://YOUR_EC2_PUBLIC_IP/docs`
- **Health Check**: `http://YOUR_EC2_PUBLIC_IP/health`

## Useful Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Backend only
docker-compose -f docker-compose.prod.yml logs -f backend

# Frontend only
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Restart Services
```bash
# Restart all
docker-compose -f docker-compose.prod.yml restart

# Restart backend
docker-compose -f docker-compose.prod.yml restart backend
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Update Code
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Can't access the app?
```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# Check security group allows port 80
# Check if services are healthy
curl http://localhost
```

### Backend not starting?
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common fix: Check database password in .env
```

### Out of memory?
```bash
# Check memory
free -h

# If low, upgrade to t2.xlarge instance
```

## Cost Estimate

- **t2.large**: ~$70/month
- **Data Transfer**: ~$10/month
- **Total**: ~$80/month

## Next Steps

1. ✅ Setup custom domain (optional)
2. ✅ Configure SSL certificate
3. ✅ Setup monitoring
4. ✅ Configure backups

See **AWS_DEPLOYMENT.md** for detailed instructions.

---

**Deployment Time**: ~30 minutes
**Status**: Production Ready 🚀
**Support**: See AWS_DEPLOYMENT.md for troubleshooting
