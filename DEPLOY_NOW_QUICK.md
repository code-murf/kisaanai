# 🚀 Deploy KisaanAI to AWS EC2 - Quick Guide

## Current Status
❌ Deployment is NOT running on EC2 (13.53.186.103)
✅ All deployment files are ready

## Prerequisites Checklist
- [ ] EC2 instance is running (check AWS Console)
- [ ] Security Group allows ports: 22, 80, 443, 3000, 8000
- [ ] SSH key `kisaanai.pem` is in project root
- [ ] Docker and Docker Compose installed on EC2

## Step 1: Verify EC2 Instance is Running

1. Go to AWS Console → EC2 → Instances
2. Find instance: `i-01f435b0fbf6498d2` (Kisaanai)
3. Ensure "Instance state" is **Running**
4. If stopped, click "Instance state" → "Start instance"

## Step 2: Configure Security Group

1. In AWS Console, select your instance
2. Click "Security" tab
3. Click on the Security Group link
4. Click "Edit inbound rules"
5. Add these rules:

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH access |
| HTTP | TCP | 80 | 0.0.0.0/0 | Nginx |
| Custom TCP | TCP | 3000 | 0.0.0.0/0 | Frontend |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | Backend API |
| HTTPS | TCP | 443 | 0.0.0.0/0 | SSL (optional) |

6. Click "Save rules"

## Step 3: Create .env File

Create a `.env` file in your project root with these values:

```bash
# AWS Configuration
AWS_PUBLIC_IP=13.53.186.103

# Database
DB_PASSWORD=kisaanai_secure_2026

# Supabase
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqZG1vYnpkYWV6bnN0emVpbm9kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjIzMTksImV4cCI6MjA4NTg5ODMxOX0.OyRKsxgf2Z6nz3xi-AgxWhXoyFwctgIlHeDBWv5GJMQ

# AI APIs
GROQ_API_KEY=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
SARVAM_API_KEY=sk_g1reegfg_SGFAGFVofg8PP9bUy7dOYInv
ELEVENLABS_API_KEY=sk_6ee10e855ba6e48df0d0e9832bd623c5eb988c0fe07acbcb
ELEVENLABS_AGENT_ID=agent_4401khg909n3
HUGGINGFACE_TOKEN=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

# Security
SECRET_KEY=kisaanai_secret_key_2026_aws_hackathon
```

## Step 4: Deploy to EC2

### Option A: Automated Deployment (Recommended)

Run this PowerShell script:

```powershell
.\deploy-step-by-step.ps1
```

The script will:
1. Copy files to EC2
2. Install Docker if needed
3. Build and start containers
4. Run health checks

### Option B: Manual Deployment

1. **Copy files to EC2:**
```powershell
scp -i kisaanai.pem -r * ubuntu@13.53.186.103:/home/ubuntu/kisaanai/
```

2. **SSH into EC2:**
```powershell
ssh -i kisaanai.pem ubuntu@13.53.186.103
```

3. **Install Docker (if not installed):**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
```

4. **Deploy the application:**
```bash
cd /home/ubuntu/kisaanai
docker-compose -f docker-compose.prod.yml up -d
```

5. **Check status:**
```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs
```

## Step 5: Test Deployment

Run the test script:

```powershell
.\test-live-deployment.ps1
```

Or manually test these URLs:

- Frontend: http://13.53.186.103
- Backend Health: http://13.53.186.103:8000/health
- API Commodities: http://13.53.186.103:8000/api/v1/commodities
- API Mandis: http://13.53.186.103:8000/api/v1/mandis

## Step 6: Verify All Services

SSH into EC2 and run:

```bash
cd /home/ubuntu/kisaanai
./test-deployment.sh
```

Expected output:
- ✓ 4 containers running (postgres, backend, frontend, nginx)
- ✓ Database has 12+ tables
- ✓ Backend health check passes
- ✓ APIs return data
- ✓ Frontend is accessible

## Troubleshooting

### If deployment fails:

1. **Check Docker logs:**
```bash
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs postgres
```

2. **Restart services:**
```bash
docker-compose -f docker-compose.prod.yml restart
```

3. **Rebuild containers:**
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

4. **Check disk space:**
```bash
df -h
```

5. **Check memory:**
```bash
free -h
```

### If ports are not accessible:

1. Verify Security Group rules in AWS Console
2. Check if services are listening:
```bash
sudo netstat -tulpn | grep -E '80|3000|8000'
```

3. Check firewall:
```bash
sudo ufw status
```

## Quick Commands Reference

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart a service
docker-compose -f docker-compose.prod.yml restart backend

# Check status
docker-compose -f docker-compose.prod.yml ps

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Access database
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d kisaanai
```

## Next Steps After Deployment

1. ✅ Test all endpoints
2. ✅ Verify frontend loads correctly
3. ✅ Test API functionality
4. ✅ Check database has sample data
5. ✅ Monitor logs for errors
6. ✅ Set up SSL certificate (optional)
7. ✅ Configure domain name (optional)

## Support

If you encounter issues:
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Review `TEST_DEPLOYMENT.md` for detailed testing
3. See `DEPLOY_MANUAL.md` for step-by-step manual deployment
4. Check AWS Console for instance status and security groups

---

**Ready to deploy?** Start with Step 1 above! 🚀
