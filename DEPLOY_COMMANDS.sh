#!/bin/bash
# KisaanAI Deployment Script for EC2
# Run these commands on your EC2 instance

set -e  # Exit on error

echo "=========================================="
echo "KisaanAI Deployment Script"
echo "=========================================="
echo ""

# 1. Install Docker and Docker Compose
echo "Step 1: Installing Docker and dependencies..."
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
echo "✓ Docker installed"
echo ""

# 2. Create project directory
echo "Step 2: Creating project directory..."
mkdir -p kisaanai
cd kisaanai
echo "✓ Directory created"
echo ""

# 3. Clone repository
echo "Step 3: Cloning repository..."
git clone https://github.com/code-murf/kisaanai.git .
echo "✓ Repository cloned"
echo ""

# 4. Create .env file
echo "Step 4: Creating .env file..."
cat > .env << 'EOF'
AWS_PUBLIC_IP=13.53.186.103
DB_PASSWORD=kisaanai_secure_2026
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqZG1vYnpkYWV6bnN0emVpbm9kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjIzMTksImV4cCI6MjA4NTg5ODMxOX0.OyRKsxgf2Z6nz3xi-AgxWhXoyFwctgIlHeDBWv5GJMQ
GROQ_API_KEY=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
SARVAM_API_KEY=sk_g1reegfg_SGFAGFVofg8PP9bUy7dOYInv
ELEVENLABS_API_KEY=sk_6ee10e855ba6e48df0d0e9832bd623c5eb988c0fe07acbcb
ELEVENLABS_AGENT_ID=agent_4401khg909n3
HUGGINGFACE_TOKEN=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
SECRET_KEY=kisaanai_secret_key_2026_aws_hackathon
EOF
echo "✓ .env file created"
echo ""

# 5. Deploy with Docker Compose
echo "Step 5: Deploying with Docker Compose..."
echo "This will take 10-15 minutes (building images)..."
sudo docker-compose -f docker-compose.prod.yml up -d --build
echo "✓ Deployment started"
echo ""

# 6. Wait for services to start
echo "Waiting 30 seconds for services to start..."
sleep 30
echo ""

# 7. Check status
echo "Step 6: Checking container status..."
sudo docker-compose -f docker-compose.prod.yml ps
echo ""

# 8. Test endpoints
echo "Step 7: Testing endpoints..."
echo "Testing backend health..."
curl -f http://localhost:8000/health || echo "Backend not ready yet"
echo ""
echo "Testing frontend..."
curl -f http://localhost:3000 || echo "Frontend not ready yet"
echo ""

# 9. Show logs
echo "Step 8: Showing recent logs..."
sudo docker-compose -f docker-compose.prod.yml logs --tail=50
echo ""

# 10. Check ports
echo "Step 9: Checking listening ports..."
sudo netstat -tulpn | grep -E '80|3000|8000|5432'
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Your application should be accessible at:"
echo "  Frontend: http://13.53.186.103"
echo "  Backend: http://13.53.186.103:8000"
echo "  API Docs: http://13.53.186.103:8000/docs"
echo ""
echo "Useful commands:"
echo "  View logs: sudo docker-compose -f docker-compose.prod.yml logs -f"
echo "  Restart: sudo docker-compose -f docker-compose.prod.yml restart"
echo "  Stop: sudo docker-compose -f docker-compose.prod.yml down"
echo ""
