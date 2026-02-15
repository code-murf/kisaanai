#!/bin/bash

# Apply database schema fix to production
# Run this script on your local machine

echo "========================================="
echo "KisaanAI - Database Schema Fix"
echo "========================================="
echo ""

# Configuration
EC2_IP="13.53.186.103"
SSH_KEY="kisaanai.pem"
DB_NAME="kisaanai"
DB_USER="postgres"

echo "Step 1: Copying SQL fix file to EC2..."
scp -i "$SSH_KEY" fix_database_schema.sql ubuntu@$EC2_IP:/home/ubuntu/kisaanai/

echo ""
echo "Step 2: Applying database fixes..."
ssh -i "$SSH_KEY" ubuntu@$EC2_IP << 'ENDSSH'
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
curl -s http://localhost:8000/health | jq .
echo ""
curl -s http://localhost:8000/api/v1/commodities | jq '.data | length'
echo ""
curl -s http://localhost:8000/api/v1/mandis | jq '.data | length'

ENDSSH

echo ""
echo "========================================="
echo "Database fix applied successfully!"
echo "========================================="
echo ""
echo "Test the APIs:"
echo "  Commodities: http://13.53.186.103:8000/api/v1/commodities"
echo "  Mandis: http://13.53.186.103:8000/api/v1/mandis"
echo ""
