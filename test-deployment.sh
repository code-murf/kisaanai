#!/bin/bash

# KisaanAI Deployment Test Script
# Run this on EC2 after deployment

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧪 KisaanAI Deployment Test"
echo "============================"
echo ""

# Test 1: Container Status
echo "Test 1: Checking containers..."
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Containers are running${NC}"
else
    echo -e "${RED}✗ Containers are not running${NC}"
    exit 1
fi
echo ""

# Test 2: Database
echo "Test 2: Testing database..."
TABLE_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d kisaanai -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" | tr -d ' ')
if [ "$TABLE_COUNT" -gt 10 ]; then
    echo -e "${GREEN}✓ Database initialized ($TABLE_COUNT tables)${NC}"
else
    echo -e "${RED}✗ Database not properly initialized${NC}"
    exit 1
fi
echo ""

# Test 3: Backend Health
echo "Test 3: Testing backend health..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    exit 1
fi
echo ""

# Test 4: API Endpoints
echo "Test 4: Testing API endpoints..."
COMMODITIES=$(curl -s http://localhost:8000/api/v1/commodities)
if echo "$COMMODITIES" | grep -q "Wheat"; then
    echo -e "${GREEN}✓ API returning data${NC}"
else
    echo -e "${RED}✗ API not returning expected data${NC}"
    exit 1
fi
echo ""

# Test 5: Frontend
echo "Test 5: Testing frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Frontend is accessible${NC}"
else
    echo -e "${RED}✗ Frontend not accessible (HTTP $FRONTEND_STATUS)${NC}"
    exit 1
fi
echo ""

# Test 6: Nginx
echo "Test 6: Testing Nginx..."
NGINX_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost)
if [ "$NGINX_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Nginx is working${NC}"
else
    echo -e "${RED}✗ Nginx not working (HTTP $NGINX_STATUS)${NC}"
    exit 1
fi
echo ""

# Test 7: Database Data
echo "Test 7: Checking sample data..."
COMMODITY_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d kisaanai -t -c "SELECT count(*) FROM commodities;" | tr -d ' ')
MANDI_COUNT=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d kisaanai -t -c "SELECT count(*) FROM mandis;" | tr -d ' ')
if [ "$COMMODITY_COUNT" -gt 0 ] && [ "$MANDI_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Sample data loaded ($COMMODITY_COUNT commodities, $MANDI_COUNT mandis)${NC}"
else
    echo -e "${RED}✗ Sample data not loaded${NC}"
    exit 1
fi
echo ""

# Test 8: Resource Usage
echo "Test 8: Checking resource usage..."
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
echo "Memory usage: ${MEMORY_USAGE}%"
echo "Disk usage: ${DISK_USAGE}%"
if [ "$MEMORY_USAGE" -lt 90 ] && [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✓ Resource usage is healthy${NC}"
else
    echo -e "${YELLOW}⚠ High resource usage detected${NC}"
fi
echo ""

# Test 9: Check for errors in logs
echo "Test 9: Checking logs for errors..."
ERROR_COUNT=$(docker-compose -f docker-compose.prod.yml logs --tail=100 | grep -i "error" | wc -l)
if [ "$ERROR_COUNT" -lt 5 ]; then
    echo -e "${GREEN}✓ No critical errors in logs${NC}"
else
    echo -e "${YELLOW}⚠ Found $ERROR_COUNT errors in logs (check with: docker-compose logs)${NC}"
fi
echo ""

# Summary
echo "================================"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "Your application is running at:"
echo "  Frontend: http://$(curl -s http://checkip.amazonaws.com)"
echo "  Backend API: http://$(curl -s http://checkip.amazonaws.com)/api"
echo "  API Docs: http://$(curl -s http://checkip.amazonaws.com)/docs"
echo ""
echo "Useful commands:"
echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  Restart: docker-compose -f docker-compose.prod.yml restart"
echo "  Stop: docker-compose -f docker-compose.prod.yml down"
echo ""
