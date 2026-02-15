# 🚀 Quick Start Deployment Guide

Deploy KisaanAI to production in 15 minutes!

## Prerequisites

- GitHub account (already set up ✅)
- Vercel account (sign up at vercel.com)
- Render account (sign up at render.com)
- Your credentials from SECRETS.md

## Step 1: Deploy Backend to Render (5 minutes)

### Method A: Using Render Dashboard (Recommended)

1. **Go to Render**: https://dashboard.render.com

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Click "Connect GitHub"
   - Select repository: `code-murf/kisaanai`

3. **Configure Service**:
   ```
   Name: kisaanai-backend
   Region: Singapore (or closest to you)
   Branch: main
   Root Directory: backend
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Add Environment Variables** (click "Advanced" → "Add Environment Variable"):
   
   Copy these from SECRETS.md and paste:
   ```
   PYTHON_VERSION=3.11.0
   DATABASE_URL=postgresql://postgres:[GET_PASSWORD_FROM_SUPABASE]@db.yjdmobzdaeznstzeinod.supabase.co:5432/postgres
   SUPABASE_URL=https://yjdmobzdaeznstzeinod.supabase.co
   SUPABASE_ANON_KEY=[FROM_SECRETS.md]
   DEBUG=False
   GROQ_API_KEY=[FROM_SECRETS.md]
   GROQ_MODEL=llama-3.3-70b-versatile
   SARVAM_API_KEY=[FROM_SECRETS.md]
   ELEVENLABS_API_KEY=[FROM_SECRETS.md]
   ELEVENLABS_AGENT_ID=[FROM_SECRETS.md]
   HUGGINGFACE_TOKEN=[FROM_SECRETS.md]
   CORS_ORIGINS=https://kisaanai.vercel.app,https://kisaanai-*.vercel.app
   SECRET_KEY=[GENERATE_NEW_ONE]
   ```

   **Generate SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Deploy**: Click "Create Web Service"

6. **Wait for deployment** (3-5 minutes)

7. **Copy your backend URL**: `https://kisaanai-backend.onrender.com`

### Method B: Using PowerShell Script

```powershell
.\deploy.ps1
# Select option 1
```

## Step 2: Deploy Frontend to Vercel (5 minutes)

### Method A: Using Vercel Dashboard (Recommended)

1. **Go to Vercel**: https://vercel.com/dashboard

2. **Import Project**:
   - Click "Add New..." → "Project"
   - Click "Import Git Repository"
   - Select `code-murf/kisaanai`
   - Click "Import"

3. **Configure Project**:
   ```
   Framework Preset: Next.js
   Root Directory: frontend
   Build Command: npm run build (auto-detected)
   Output Directory: .next (auto-detected)
   Install Command: npm install (auto-detected)
   ```

4. **Add Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://kisaanai-backend.onrender.com
   NEXT_PUBLIC_SUPABASE_URL=https://yjdmobzdaeznstzeinod.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=[FROM_SECRETS.md]
   ```

5. **Deploy**: Click "Deploy"

6. **Wait for deployment** (2-3 minutes)

7. **Your app is live**: `https://kisaanai.vercel.app`

### Method B: Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel --prod
```

### Method C: Using PowerShell Script

```powershell
.\deploy.ps1
# Select option 2
```

## Step 3: Verify Deployment (2 minutes)

### Test Backend
```bash
curl https://kisaanai-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Test Frontend
Open in browser: https://kisaanai.vercel.app

### Test API Integration
```bash
curl https://kisaanai-backend.onrender.com/api/v1/commodities
```

## Step 4: Update CORS (1 minute)

After getting your Vercel URL:

1. Go to Render Dashboard → kisaanai-backend → Environment
2. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://kisaanai.vercel.app,https://kisaanai-*.vercel.app,http://localhost:3000
   ```
3. Click "Save Changes"
4. Service will auto-redeploy

## Step 5: Configure Custom Domain (Optional)

### For Frontend (Vercel)
1. Vercel Dashboard → kisaanai → Settings → Domains
2. Add your domain (e.g., `kisaanai.com`)
3. Follow DNS configuration instructions

### For Backend (Render)
1. Render Dashboard → kisaanai-backend → Settings
2. Click "Custom Domain"
3. Add your API domain (e.g., `api.kisaanai.com`)
4. Follow DNS configuration instructions

## Troubleshooting

### Backend not starting?
- Check Render logs: Dashboard → kisaanai-backend → Logs
- Verify all environment variables are set
- Check database connection string

### Frontend build failing?
- Check Vercel logs: Dashboard → kisaanai → Deployments → [Latest] → Logs
- Verify Node.js version (18+)
- Check for TypeScript errors

### CORS errors?
- Verify CORS_ORIGINS includes your Vercel URL
- Check backend logs for CORS-related errors
- Ensure no trailing slashes in URLs

### Can't connect to database?
- Get database password from Supabase dashboard
- Verify connection string format
- Check if database is active

## Quick Commands Reference

### Redeploy Backend
```bash
# Trigger redeploy from Render dashboard
# Or push to GitHub (auto-deploys)
git push origin main
```

### Redeploy Frontend
```bash
# From Vercel dashboard: Deployments → Redeploy
# Or using CLI:
cd frontend
vercel --prod
```

### View Logs
```bash
# Backend (Render CLI)
render logs kisaanai-backend

# Frontend (Vercel CLI)
vercel logs kisaanai
```

## Success Checklist

- ✅ Backend deployed to Render
- ✅ Frontend deployed to Vercel
- ✅ Database connected (Supabase)
- ✅ Environment variables configured
- ✅ CORS properly set up
- ✅ Health check passing
- ✅ Frontend loading correctly
- ✅ API calls working

## Next Steps

1. **Monitor**: Set up monitoring in Render and Vercel dashboards
2. **Analytics**: Add Google Analytics or Vercel Analytics
3. **Error Tracking**: Set up Sentry for error monitoring
4. **Performance**: Enable caching and CDN
5. **Security**: Review security settings
6. **Backup**: Set up automated database backups

## Support

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Supabase Docs**: https://supabase.com/docs

---

**Deployment Time**: ~15 minutes
**Status**: Production Ready 🚀
**Last Updated**: February 15, 2026
