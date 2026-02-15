#!/bin/bash

# KisaanAI AWS Deployment Script
# Deploys both frontend and backend on a single EC2 instance

set -e

echo "🚀 KisaanAI AWS Deployment Script"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Check if running on EC2
check_environment() {
    print_info "Checking environment..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        print_info "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        print_success "Docker installed"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        print_info "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        print_success "Docker Compose installed"
    fi
    
    print_success "Environment check complete"
}

# Setup environment variables
setup_env() {
    print_info "Setting up environment variables..."
    
    if [ ! -f .env ]; then
        cp .env.production .env
        print_warning ".env file created from template"
        print_warning "Please edit .env file with your actual values"
        read -p "Press Enter after editing .env file..."
    fi
    
    # Get public IP
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)
    print_info "Your EC2 Public IP: $PUBLIC_IP"
    
    # Update .env with public IP
    sed -i "s/YOUR_EC2_PUBLIC_IP/$PUBLIC_IP/g" .env
    
    print_success "Environment variables configured"
}

# Build and deploy
deploy() {
    print_info "Building and deploying containers..."
    
    # Stop existing containers
    print_info "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down || true
    
    # Build images
    print_info "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start containers
    print_info "Starting containers..."
    docker-compose -f docker-compose.prod.yml up -d
    
    print_success "Deployment complete!"
}

# Check health
check_health() {
    print_info "Checking application health..."
    
    sleep 10
    
    # Check backend
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_success "Backend is healthy"
    else
        print_error "Backend health check failed"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 &> /dev/null; then
        print_success "Frontend is healthy"
    else
        print_error "Frontend health check failed"
    fi
    
    # Check nginx
    if curl -f http://localhost &> /dev/null; then
        print_success "Nginx is healthy"
    else
        print_error "Nginx health check failed"
    fi
}

# Show status
show_status() {
    echo ""
    print_success "🎉 Deployment Complete!"
    echo ""
    echo "Your application is now running:"
    echo "  Frontend: http://$(curl -s http://checkip.amazonaws.com)"
    echo "  Backend API: http://$(curl -s http://checkip.amazonaws.com)/api"
    echo "  API Docs: http://$(curl -s http://checkip.amazonaws.com)/docs"
    echo ""
    echo "Useful commands:"
    echo "  View logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "  Stop: docker-compose -f docker-compose.prod.yml down"
    echo "  Restart: docker-compose -f docker-compose.prod.yml restart"
    echo ""
}

# Main execution
main() {
    check_environment
    setup_env
    deploy
    check_health
    show_status
}

# Run main function
main
