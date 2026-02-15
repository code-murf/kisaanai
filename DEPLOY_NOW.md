# 🚀 Deploy KisaanAI to Your AWS Instance NOW!

## Your Instance Details
- **Public IP**: 13.53.186.103
- **Region**: Stockholm (eu-north-1)
- **Instance Type**: t3.small
- **OS**: Ubuntu 24.04
- **Key File**: kisaanai.pem (saved in project root)

## Quick Deploy (Copy & Paste Commands)

### Step 1: Connect to Your EC2 Instance

Open PowerShell and run:

```powershell
# Set key permissions (Windows)
icacls kisaanai.pem /inheritance:r
icacls kisaanai.pem /grant:r "%username%:R"

# Connect to EC2
ssh -i kisaanai.pem ubuntu@13.53.186.103
```

If you get "Host key verification" prompt, type `yes` and press Enter.

### Step 2: Install Dependencies on EC2

Once connected, copy and paste these commands:

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

# Logout to apply docker group
exit
```

### Step 3: Reconnect and Clone Repository

```powershell
# Reconnect
ssh -i kisaanai.pem ubuntu@13.53.186.103
```

Then on EC2:

```bash
# Clone repository
git clone https://github.com/code-murf/kisaanai.git
cd kisaanai

# Copy environment template
cp .env.production .env
```

### Step 4: Configure Environment Variables

```bash
# Edit .env file
nano .env
```

**Update these values** (use your actual credentials from SECRETS.md):

```bash
# Your EC2 IP (already correct)
AWS_PUBLIC_IP=13.53.186.103

# Get from Supabase Dashboard → Settings → Database
DB_PASSWORD=YOUR_SUPABASE_PASSWORD

# Already in SECRETS.md
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqZG1vYnpkYWV6bnN0emVpbm9kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjIzMTksImV4cCI6MjA4NTg5ODMxOX0.OyRKsxgf2Z6nz3xi-AgxWhXoyFwctgIlHeDBWv5GJMQ

# From SECRETS.md (get actual values from SECRETS.md file)
GROQ_API_KEY=YOUR_GROQ_API_KEY
SARVAM_API_KEY=YOUR_SARVAM_API_KEY
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY
ELEVENLABS_AGENT_ID=YOUR_ELEVENLABS_AGENT_ID
HUGGINGFACE_TOKEN=YOUR_HUGGINGFACE_TOKEN

# Generate new secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
```

**Save**: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 5: Deploy!

```bash
# Make script executable
chmod +x deploy-aws.sh

# Run deployment
./deploy-aws.sh
```

Wait 5-10 minutes for deployment to complete...

### Step 6: Verify Deployment

```bash
# Check containers are running
docker-compose -f docker-compose.prod.yml ps

# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000
```

### Step 7: Access Your Application! 🎉

Open in your browser:

```
http://13.53.186.103
```

## Your Application URLs

- **Frontend**: http://13.53.186.103
- **Backend API**: http://13.53.186.103/api
- **API Docs**: http://13.53.186.103/docs
- **Health Check**: http://13.53.186.103/health

## Troubleshooting

### Can't connect via SSH?

Check security group allows SSH from your IP:
1. Go to EC2 Console
2. Select instance → Security → Security groups
3. Edit inbound rules
4. Add rule: SSH (22) from "My IP"

### Can't access the website?

Check security group allows HTTP:
1. Edit inbound rules
2. Add rule: HTTP (80) from "Anywhere IPv4" (0.0.0.0/0)

### Deployment failed?

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Restart deployment
docker-compose -f docker-compose.prod.yml down
./deploy-aws.sh
```

### Out of memory?

t3.small might be too small. Upgrade to t3.medium:
1. Stop instance
2. Change instance type to t3.medium
3. Start instance
4. Reconnect and redeploy

## Useful Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Backend only
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Stop Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### Update Application
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

## Next Steps

1. ✅ Test all features
2. ✅ Setup custom domain (optional)
3. ✅ Configure SSL certificate
4. ✅ Setup monitoring

## Need Help?

- Check AWS_DEPLOYMENT.md for detailed guide
- Check QUICKSTART_AWS.md for quick reference
- View logs for error messages

---

**Your Instance**: 13.53.186.103
**Status**: Ready to Deploy! 🚀
**Estimated Time**: 30 minutes
