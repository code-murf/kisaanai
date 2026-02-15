#!/bin/bash

# KisaanAI Deployment Script
# This script helps deploy the application to production

set -e

echo "🚀 KisaanAI Deployment Script"
echo "=============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if required tools are installed
check_requirements() {
    print_info "Checking requirements..."
    
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    print_success "All requirements met"
}

# Deploy backend to Render
deploy_backend() {
    print_info "Deploying backend to Render..."
    echo ""
    echo "Please follow these steps:"
    echo "1. Go to https://dashboard.render.com"
    echo "2. Click 'New +' → 'Web Service'"
    echo "3. Connect GitHub repository: code-murf/kisaanai"
    echo "4. Configure:"
    echo "   - Name: kisaanai-backend"
    echo "   - Root Directory: backend"
    echo "   - Build Command: pip install -r requirements.txt"
    echo "   - Start Command: uvicorn app.main:app --host 0.0.0.0 --port \$PORT"
    echo "5. Add environment variables from SECRETS.md"
    echo "6. Click 'Create Web Service'"
    echo ""
    read -p "Press Enter when backend is deployed..."
    print_success "Backend deployment initiated"
}

# Deploy frontend to Vercel
deploy_frontend() {
    print_info "Deploying frontend to Vercel..."
    
    if ! command -v vercel &> /dev/null; then
        print_info "Installing Vercel CLI..."
        npm i -g vercel
    fi
    
    print_info "Logging into Vercel..."
    vercel login
    
    print_info "Deploying to production..."
    cd frontend
    vercel --prod
    cd ..
    
    print_success "Frontend deployed successfully"
}

# Update environment variables
update_env() {
    print_info "Updating environment variables..."
    
    read -p "Enter your backend URL (e.g., https://kisaanai-backend.onrender.com): " BACKEND_URL
    
    # Update frontend .env.production
    cat > frontend/.env.production << EOF
NEXT_PUBLIC_API_URL=$BACKEND_URL
NEXT_PUBLIC_SUPABASE_URL=https://yjdmobzdaeznstzeinod.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqZG1vYnpkYWV6bnN0emVpbm9kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjIzMTksImV4cCI6MjA4NTg5ODMxOX0.OyRKsxgf2Z6nz3xi-AgxWhXoyFwctgIlHeDBWv5GJMQ
EOF
    
    print_success "Environment variables updated"
}

# Main deployment flow
main() {
    echo "Select deployment option:"
    echo "1. Deploy Backend (Render)"
    echo "2. Deploy Frontend (Vercel)"
    echo "3. Deploy Both"
    echo "4. Update Environment Variables"
    echo "5. Exit"
    echo ""
    read -p "Enter your choice (1-5): " choice
    
    case $choice in
        1)
            check_requirements
            deploy_backend
            ;;
        2)
            check_requirements
            deploy_frontend
            ;;
        3)
            check_requirements
            deploy_backend
            deploy_frontend
            ;;
        4)
            update_env
            ;;
        5)
            echo "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    echo ""
    print_success "Deployment complete! 🎉"
    echo ""
    echo "Next steps:"
    echo "1. Verify backend: curl https://your-backend-url.onrender.com/health"
    echo "2. Visit frontend: https://kisaanai.vercel.app"
    echo "3. Check logs in respective dashboards"
}

# Run main function
main
