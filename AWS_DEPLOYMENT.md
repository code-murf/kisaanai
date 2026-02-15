# 🚀 AWS EC2 Deployment Guide - Single Instance

Deploy both frontend and backend on a single AWS EC2 instance using Docker.

## Prerequisites

- AWS Account
- EC2 instance (t2.medium or larger recommended)
- SSH access to EC2 instance
- Domain name (optional)

## Step 1: Launch EC2 Instance (10 minutes)

### 1.1 Create EC2 Instance

1. **Go to AWS Console**: https://console.aws.amazon.com/ec2
2. **Click "Launch Instance"**
3. **Configure**:
   ```
   Name: kisaanai-server
   AMI: Ubuntu Server 22.04 LTS
   Instance Type: t2.medium (2 vCPU, 4GB RAM) - Minimum
                  t2.large (2 vCPU, 8GB RAM) - Recommended
   Key Pair: Create new or use existing
   ```

4. **Network Settings**:
   - Create security group: `kisaanai-sg`
   - Allow inbound rules:
     ```
     SSH (22) - Your IP
     HTTP (80) - 0.0.0.0/0
     HTTPS (443) - 0.0.0.0/0
     Custom TCP (8000) - 0.0.0.0/0 (for direct API access)
     Custom TCP (3000) - 0.0.0.0/0 (for direct frontend access)
     ```

5. **Storage**: 30 GB gp3 (minimum)

6. **Click "Launch Instance"**

### 1.2 Get Instance Details

After launch, note:
- **Public IP**: e.g., `54.123.45.67`
- **Public DNS**: e.g., `ec2-54-123-45-67.compute-1.amazonaws.com`

## Step 2: Connect to EC2 Instance (2 minutes)

### Using SSH

```bash
# Change key permissions
chmod 400 your-key.pem

# Connect to instance
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Using AWS Console

1. Select your instance
2. Click "Connect"
3. Choose "EC2 Instance Connect"
4. Click "Connect"

## Step 3: Setup Server (5 minutes)

Once connected to EC2, run:

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

# Logout and login again for docker group to take effect
exit
```

Reconnect to EC2:
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

## Step 4: Clone Repository (2 minutes)

```bash
# Clone your repository
git clone https://github.com/code-murf/kisaanai.git
cd kisaanai

# Make deploy script executable
chmod +x deploy-aws.sh
```

## Step 5: Configure Environment (3 minutes)

```bash
# Copy environment template
cp .env.production .env

# Edit environment variables
nano .env
```

Update these values in `.env`:

```bash
# Your EC2 Public IP (will be auto-filled by script)
AWS_PUBLIC_IP=YOUR_EC2_PUBLIC_IP

# Get from Supabase Dashboard
DB_PASSWORD=your_supabase_password

# Already filled (from SECRETS.md)
SUPABASE_ANON_KEY=eyJhbGci...
GROQ_API_KEY=gsk_...
SARVAM_API_KEY=sk_...
ELEVENLABS_API_KEY=sk_...
ELEVENLABS_AGENT_ID=agent_...
HUGGINGFACE_TOKEN=hf_...

# Generate new secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

Save and exit (Ctrl+X, Y, Enter)

## Step 6: Deploy Application (10 minutes)

```bash
# Run deployment script
./deploy-aws.sh
```

The script will:
1. ✅ Check and install dependencies
2. ✅ Setup environment variables
3. ✅ Build Docker images
4. ✅ Start all containers
5. ✅ Run health checks

## Step 7: Verify Deployment (2 minutes)

### Check Container Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                COMMAND                  STATUS              PORTS
kisaanai-backend    "uvicorn app.main:..."   Up 2 minutes        0.0.0.0:8000->8000/tcp
kisaanai-frontend   "node server.js"         Up 2 minutes        0.0.0.0:3000->3000/tcp
kisaanai-nginx      "nginx -g 'daemon ..."   Up 2 minutes        0.0.0.0:80->80/tcp
```

### Test Endpoints

```bash
# Get your public IP
PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)

# Test backend health
curl http://$PUBLIC_IP:8000/health

# Test API
curl http://$PUBLIC_IP:8000/api/v1/commodities

# Test frontend (in browser)
echo "Visit: http://$PUBLIC_IP"
```

## Step 8: Access Your Application

Your application is now live at:

- **Frontend**: `http://YOUR_EC2_PUBLIC_IP`
- **Backend API**: `http://YOUR_EC2_PUBLIC_IP/api`
- **API Docs**: `http://YOUR_EC2_PUBLIC_IP/docs`
- **Health Check**: `http://YOUR_EC2_PUBLIC_IP/health`

## Architecture

```
┌─────────────────────────────────────────────┐
│         AWS EC2 Instance (t2.medium)        │
│                                             │
│  ┌────────────────────────────────────┐    │
│  │  Nginx (Port 80)                   │    │
│  │  - Reverse Proxy                   │    │
│  │  - Load Balancer                   │    │
│  │  - Rate Limiting                   │    │
│  └──────────┬─────────────────────────┘    │
│             │                               │
│    ┌────────┴────────┐                     │
│    │                 │                     │
│  ┌─▼──────────┐  ┌──▼──────────┐          │
│  │ Backend    │  │  Frontend   │          │
│  │ (Port 8000)│  │  (Port 3000)│          │
│  │ FastAPI    │  │  Next.js    │          │
│  └────────────┘  └─────────────┘          │
│                                             │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Supabase Database  │
│  (External)         │
└─────────────────────┘
```

## Useful Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Backend only
docker-compose -f docker-compose.prod.yml logs -f backend

# Frontend only
docker-compose -f docker-compose.prod.yml logs -f frontend

# Nginx only
docker-compose -f docker-compose.prod.yml logs -f nginx
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

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Monitor Resources
```bash
# CPU and Memory usage
docker stats

# Disk usage
df -h

# Docker disk usage
docker system df
```

## Optional: Setup Custom Domain

### 1. Point Domain to EC2

In your domain registrar (GoDaddy, Namecheap, etc.):

```
Type: A Record
Name: @
Value: YOUR_EC2_PUBLIC_IP
TTL: 300

Type: A Record
Name: www
Value: YOUR_EC2_PUBLIC_IP
TTL: 300
```

### 2. Update Nginx Configuration

Edit `nginx.conf`:
```bash
nano nginx.conf
```

Change:
```nginx
server_name _;
```

To:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

### 3. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
```

### 4. Restart Nginx
```bash
docker-compose -f docker-compose.prod.yml restart nginx
```

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common issues:
# - Database connection: Check DB_PASSWORD in .env
# - Port conflict: Check if port 8000 is available
# - Memory: Upgrade to t2.large if needed
```

### Frontend Not Building
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs frontend

# Common issues:
# - Build timeout: Increase Docker memory
# - API URL: Check NEXT_PUBLIC_API_URL in docker-compose.prod.yml
```

### Cannot Access Application
```bash
# Check security group
# Ensure ports 80, 443, 8000, 3000 are open

# Check if services are running
docker-compose -f docker-compose.prod.yml ps

# Check nginx
curl http://localhost
```

### Out of Memory
```bash
# Check memory usage
free -h

# If low, upgrade instance type:
# t2.medium → t2.large → t2.xlarge
```

## Cost Estimate

### AWS EC2 Costs (Monthly)

| Instance Type | vCPU | RAM | Storage | Cost/Month |
|---------------|------|-----|---------|------------|
| t2.medium | 2 | 4 GB | 30 GB | ~$35 |
| t2.large | 2 | 8 GB | 30 GB | ~$70 |
| t2.xlarge | 4 | 16 GB | 30 GB | ~$140 |

**Recommended**: t2.large for production

### Additional Costs
- Data Transfer: ~$0.09/GB (first 10TB)
- Elastic IP: Free (if attached)
- Backups: ~$0.05/GB/month

**Total Estimated Cost**: $70-100/month

## Security Best Practices

1. **Firewall**: Only open necessary ports
2. **SSH**: Use key-based authentication only
3. **Updates**: Regular system updates
4. **Backups**: Setup automated backups
5. **Monitoring**: Use CloudWatch for monitoring
6. **SSL**: Always use HTTPS in production
7. **Secrets**: Never commit .env file

## Monitoring & Maintenance

### Setup CloudWatch Monitoring

1. Go to CloudWatch in AWS Console
2. Create alarms for:
   - CPU Utilization > 80%
   - Memory Utilization > 80%
   - Disk Space < 20%
   - HTTP 5xx errors

### Automated Backups

```bash
# Create backup script
nano backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T backend pg_dump $DATABASE_URL > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://your-backup-bucket/
```

### Log Rotation

```bash
# Configure Docker log rotation
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## Next Steps

1. ✅ Setup custom domain
2. ✅ Configure SSL certificate
3. ✅ Setup monitoring and alerts
4. ✅ Configure automated backups
5. ✅ Setup CI/CD pipeline
6. ✅ Load testing
7. ✅ Security audit

---

**Deployment Time**: ~30 minutes
**Status**: Production Ready on AWS 🚀
**Last Updated**: February 15, 2026
