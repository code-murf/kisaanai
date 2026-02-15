# KisaanAI Deployment Script for Windows PowerShell
# This script helps deploy the application to production

$ErrorActionPreference = "Stop"

Write-Host "🚀 KisaanAI Deployment Script" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host ""

function Print-Success {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Info {
    param($Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

function Print-Error {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Check-Requirements {
    Print-Info "Checking requirements..."
    
    if (!(Get-Command git -ErrorAction SilentlyContinue)) {
        Print-Error "Git is not installed"
        exit 1
    }
    
    if (!(Get-Command node -ErrorAction SilentlyContinue)) {
        Print-Error "Node.js is not installed"
        exit 1
    }
    
    Print-Success "All requirements met"
}

function Deploy-Backend {
    Print-Info "Deploying backend to Render..."
    Write-Host ""
    Write-Host "Please follow these steps:"
    Write-Host "1. Go to https://dashboard.render.com"
    Write-Host "2. Click 'New +' → 'Web Service'"
    Write-Host "3. Connect GitHub repository: code-murf/kisaanai"
    Write-Host "4. Configure:"
    Write-Host "   - Name: kisaanai-backend"
    Write-Host "   - Root Directory: backend"
    Write-Host "   - Build Command: pip install -r requirements.txt"
    Write-Host "   - Start Command: uvicorn app.main:app --host 0.0.0.0 --port `$PORT"
    Write-Host "5. Add environment variables from SECRETS.md"
    Write-Host "6. Click 'Create Web Service'"
    Write-Host ""
    Read-Host "Press Enter when backend is deployed"
    Print-Success "Backend deployment initiated"
}

function Deploy-Frontend {
    Print-Info "Deploying frontend to Vercel..."
    
    if (!(Get-Command vercel -ErrorAction SilentlyContinue)) {
        Print-Info "Installing Vercel CLI..."
        npm i -g vercel
    }
    
    Print-Info "Logging into Vercel..."
    vercel login
    
    Print-Info "Deploying to production..."
    Set-Location frontend
    vercel --prod
    Set-Location ..
    
    Print-Success "Frontend deployed successfully"
}

function Update-Environment {
    Print-Info "Updating environment variables..."
    
    $BackendURL = Read-Host "Enter your backend URL (e.g., https://kisaanai-backend.onrender.com)"
    
    $EnvContent = @"
NEXT_PUBLIC_API_URL=$BackendURL
NEXT_PUBLIC_SUPABASE_URL=https://yjdmobzdaeznstzeinod.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqZG1vYnpkYWV6bnN0emVpbm9kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjIzMTksImV4cCI6MjA4NTg5ODMxOX0.OyRKsxgf2Z6nz3xi-AgxWhXoyFwctgIlHeDBWv5GJMQ
"@
    
    $EnvContent | Out-File -FilePath "frontend\.env.production" -Encoding UTF8
    
    Print-Success "Environment variables updated"
}

function Show-Menu {
    Write-Host "Select deployment option:"
    Write-Host "1. Deploy Backend (Render)"
    Write-Host "2. Deploy Frontend (Vercel)"
    Write-Host "3. Deploy Both"
    Write-Host "4. Update Environment Variables"
    Write-Host "5. Exit"
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (1-5)"
    
    switch ($choice) {
        "1" {
            Check-Requirements
            Deploy-Backend
        }
        "2" {
            Check-Requirements
            Deploy-Frontend
        }
        "3" {
            Check-Requirements
            Deploy-Backend
            Deploy-Frontend
        }
        "4" {
            Update-Environment
        }
        "5" {
            Write-Host "Exiting..."
            exit 0
        }
        default {
            Print-Error "Invalid choice"
            exit 1
        }
    }
    
    Write-Host ""
    Print-Success "Deployment complete! 🎉"
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "1. Verify backend: curl https://your-backend-url.onrender.com/health"
    Write-Host "2. Visit frontend: https://kisaanai.vercel.app"
    Write-Host "3. Check logs in respective dashboards"
}

# Run main function
Show-Menu
