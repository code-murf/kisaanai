# KisaanAI Step-by-Step Deployment Script for Windows
# This script will guide you through deploying to AWS EC2

$ErrorActionPreference = "Stop"

$EC2_IP = "13.53.186.103"
$KEY_FILE = "kisaanai.pem"

Write-Host "🚀 KisaanAI AWS Deployment Assistant" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if key file exists
if (-not (Test-Path $KEY_FILE)) {
    Write-Host "❌ Error: $KEY_FILE not found!" -ForegroundColor Red
    Write-Host "Please ensure kisaanai.pem is in the current directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ SSH key found" -ForegroundColor Green
Write-Host ""

# Set key permissions
Write-Host "📝 Setting key file permissions..." -ForegroundColor Blue
icacls $KEY_FILE /inheritance:r | Out-Null
icacls $KEY_FILE /grant:r "$env:USERNAME`:R" | Out-Null
Write-Host "✓ Key permissions set" -ForegroundColor Green
Write-Host ""

# Test SSH connection
Write-Host "🔌 Testing SSH connection to $EC2_IP..." -ForegroundColor Blue
$testConnection = ssh -i $KEY_FILE -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$EC2_IP "echo 'Connection successful'" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ SSH connection successful!" -ForegroundColor Green
} else {
    Write-Host "❌ Cannot connect to EC2 instance" -ForegroundColor Red
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "  1. Instance is running in AWS Console" -ForegroundColor Yellow
    Write-Host "  2. Security group allows SSH (port 22) from your IP" -ForegroundColor Yellow
    Write-Host "  3. Public IP is correct: $EC2_IP" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "📦 Deployment Steps:" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install dependencies
Write-Host "Step 1: Install Docker and dependencies" -ForegroundColor Yellow
Write-Host "This will take about 5 minutes..." -ForegroundColor Gray
Write-Host ""

$installScript = @"
#!/bin/bash
set -e
echo '📦 Installing dependencies...'
sudo apt update -qq
sudo apt upgrade -y -qq

# Install Docker
if ! command -v docker &> /dev/null; then
    echo '🐳 Installing Docker...'
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    echo '✓ Docker installed'
else
    echo '✓ Docker already installed'
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo '🔧 Installing Docker Compose...'
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo '✓ Docker Compose installed'
else
    echo '✓ Docker Compose already installed'
fi

# Install Git
if ! command -v git &> /dev/null; then
    echo '📚 Installing Git...'
    sudo apt install git -y -qq
    echo '✓ Git installed'
else
    echo '✓ Git already installed'
fi

echo '✅ All dependencies installed!'
"@

$installScript | ssh -i $KEY_FILE ubuntu@$EC2_IP "cat > /tmp/install.sh && chmod +x /tmp/install.sh && bash /tmp/install.sh"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⚠️  IMPORTANT: Docker group membership requires logout/login" -ForegroundColor Yellow
Write-Host ""

# Step 2: Clone repository
Write-Host "Step 2: Clone repository" -ForegroundColor Yellow

$cloneScript = @"
#!/bin/bash
set -e
cd ~
if [ -d "kisaanai" ]; then
    echo '📂 Repository already exists, pulling latest changes...'
    cd kisaanai
    git pull origin main
else
    echo '📥 Cloning repository...'
    git clone https://github.com/code-murf/kisaanai.git
    cd kisaanai
fi
echo '✓ Repository ready'
"@

$cloneScript | ssh -i $KEY_FILE ubuntu@$EC2_IP "bash"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Repository cloned" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to clone repository" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 3: Configure environment variables" -ForegroundColor Yellow
Write-Host ""

# Create .env file with placeholders
$envContent = @"
AWS_PUBLIC_IP=$EC2_IP
DB_PASSWORD=REPLACE_WITH_SUPABASE_PASSWORD
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqZG1vYnpkYWV6bnN0emVpbm9kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjIzMTksImV4cCI6MjA4NTg5ODMxOX0.OyRKsxgf2Z6nz3xi-AgxWhXoyFwctgIlHeDBWv5GJMQ
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE
SARVAM_API_KEY=YOUR_SARVAM_API_KEY_HERE
ELEVENLABS_API_KEY=YOUR_ELEVENLABS_API_KEY_HERE
ELEVENLABS_AGENT_ID=YOUR_ELEVENLABS_AGENT_ID_HERE
HUGGINGFACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))' 2>/dev/null || openssl rand -base64 32)
"@

$envContent | ssh -i $KEY_FILE ubuntu@$EC2_IP "cat > ~/kisaanai/.env"

Write-Host "⚠️  You need to update the Supabase password in .env file" -ForegroundColor Yellow
Write-Host ""
Write-Host "Options:" -ForegroundColor Cyan
Write-Host "  1. Edit manually: ssh -i $KEY_FILE ubuntu@$EC2_IP 'nano ~/kisaanai/.env'" -ForegroundColor Gray
Write-Host "  2. Or enter password now and I'll update it" -ForegroundColor Gray
Write-Host ""

$supabasePassword = Read-Host "Enter Supabase DB Password (or press Enter to skip and edit manually later)"

if ($supabasePassword) {
    ssh -i $KEY_FILE ubuntu@$EC2_IP "sed -i 's/REPLACE_WITH_SUPABASE_PASSWORD/$supabasePassword/g' ~/kisaanai/.env"
    Write-Host "✓ Environment configured" -ForegroundColor Green
} else {
    Write-Host "⚠️  Remember to update DB_PASSWORD before deploying!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 4: Deploy application" -ForegroundColor Yellow
Write-Host "This will take 10-15 minutes (building Docker images)..." -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Ready to deploy? (y/n)"

if ($choice -eq 'y' -or $choice -eq 'Y') {
    Write-Host "🚀 Starting deployment..." -ForegroundColor Blue
    
    $deployScript = @"
#!/bin/bash
set -e
cd ~/kisaanai

# Make deploy script executable
chmod +x deploy-aws.sh

# Run deployment
./deploy-aws.sh
"@

    $deployScript | ssh -i $KEY_FILE ubuntu@$EC2_IP "bash"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌐 Your application is now live at:" -ForegroundColor Cyan
        Write-Host "   Frontend: http://$EC2_IP" -ForegroundColor White
        Write-Host "   Backend API: http://$EC2_IP/api" -ForegroundColor White
        Write-Host "   API Docs: http://$EC2_IP/docs" -ForegroundColor White
        Write-Host ""
        
        # Test endpoints
        Write-Host "🧪 Testing endpoints..." -ForegroundColor Blue
        Start-Sleep -Seconds 5
        
        try {
            $health = Invoke-RestMethod -Uri "http://$EC2_IP/health" -TimeoutSec 10
            Write-Host "✓ Backend health check: OK" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Backend health check: Waiting for services to start..." -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "📊 View logs:" -ForegroundColor Cyan
        Write-Host "   ssh -i $KEY_FILE ubuntu@$EC2_IP 'cd kisaanai && docker-compose -f docker-compose.prod.yml logs -f'" -ForegroundColor Gray
        
    } else {
        Write-Host "❌ Deployment failed" -ForegroundColor Red
        Write-Host "Check logs: ssh -i $KEY_FILE ubuntu@$EC2_IP 'cd kisaanai && docker-compose -f docker-compose.prod.yml logs'" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Deployment cancelled. To deploy manually:" -ForegroundColor Yellow
    Write-Host "  1. ssh -i $KEY_FILE ubuntu@$EC2_IP" -ForegroundColor Gray
    Write-Host "  2. cd kisaanai" -ForegroundColor Gray
    Write-Host "  3. nano .env  # Update DB_PASSWORD" -ForegroundColor Gray
    Write-Host "  4. ./deploy-aws.sh" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done! 🎉" -ForegroundColor Green
