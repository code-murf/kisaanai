# KisaanAI Deployment Guide 🚀

This guide covers deploying KisaanAI to production using Vercel (Frontend), Render (Backend), and Supabase (Database).

## Prerequisites

- GitHub account with repository access
- Vercel account
- Render account
- Supabase project (already configured)

## 1. Backend Deployment (Render)

### Option A: Using Render Dashboard

1. **Login to Render**: https://dashboard.render.com
2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `code-murf/kisaanai`
   - Select the repository

3. **Configure Service**:
   - **Name**: `kisaanai-backend`
   - **Region**: Singapore (or closest to your users)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**:
   ```
   PYTHON_VERSION=3.11.0
   DATABASE_URL=postgresql://postgres:[PASSWORD]@db.yjdmobzdaeznstzeinod.supabase.co:5432/postgres
   SUPABASE_URL=https://yjdmobzdaeznstzeinod.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqZG1vYnpkYWV6bnN0emVpbm9kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjIzMTksImV4cCI6MjA4NTg5ODMxOX0.OyRKsxgf2Z6nz3xi-AgxWhXoyFwctgIlHeDBWv5GJMQ
   DEBUG=False
   GROQ_API_KEY=[YOUR_GROQ_API_KEY]
   GROQ_MODEL=llama-3.3-70b-versatile
   SARVAM_API_KEY=[YOUR_SARVAM_API_KEY]
   ELEVENLABS_API_KEY=[YOUR_ELEVENLABS_API_KEY]
   ELEVENLABS_AGENT_ID=[YOUR_ELEVENLABS_AGENT_ID]
   HUGGINGFACE_TOKEN=[YOUR_HUGGINGFACE_TOKEN]
   CORS_ORIGINS=https://kisaanai.vercel.app,http://localhost:3000
   SECRET_KEY=[GENERATE_RANDOM_SECRET]
   ```

5. **Deploy**: Click "Create Web Service"

### Option B: Using render.yaml (Automatic)

The `backend/render.yaml` file is already configured. Render will automatically detect and use it.

### Get Backend URL
After deployment, your backend will be available at:
```
https://kisaanai-backend.onrender.com
```

## 2. Frontend Deployment (Vercel)

### Option A: Using Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from root directory
vercel --prod

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? kisaanai
# - Directory? frontend
# - Override settings? No
```

### Option B: Using Vercel Dashboard

1. **Login to Vercel**: https://vercel.com/dashboard
2. **Import Project**:
   - Click "Add New..." → "Project"
   - Import from GitHub: `code-murf/kisaanai`
   - Click "Import"

3. **Configure Project**:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

4. **Add Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://kisaanai-backend.onrender.com
   NEXT_PUBLIC_SUPABASE_URL=https://yjdmobzdaeznstzeinod.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqZG1vYnpkYWV6bnN0emVpbm9kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAzMjIzMTksImV4cCI6MjA4NTg5ODMxOX0.OyRKsxgf2Z6nz3xi-AgxWhXoyFwctgIlHeDBWv5GJMQ
   ```

5. **Deploy**: Click "Deploy"

### Get Frontend URL
After deployment, your frontend will be available at:
```
https://kisaanai.vercel.app
```

## 3. Database Setup (Supabase)

Your Supabase database is already configured:
- **URL**: https://yjdmobzdaeznstzeinod.supabase.co
- **Connection String**: Available in Supabase dashboard

### Initialize Database Schema

1. Go to Supabase Dashboard → SQL Editor
2. Run the schema initialization scripts from `backend/app/models/`
3. Or connect via psql and run migrations

## 4. Post-Deployment Configuration

### Update CORS in Backend
After getting your Vercel URL, update the backend CORS settings:

1. Go to Render Dashboard → kisaanai-backend → Environment
2. Update `CORS_ORIGINS` to include your Vercel URL:
   ```
   CORS_ORIGINS=https://kisaanai.vercel.app,https://kisaanai-*.vercel.app
   ```
3. Save and redeploy

### Update Frontend API URL
If your backend URL is different, update in Vercel:

1. Go to Vercel Dashboard → kisaanai → Settings → Environment Variables
2. Update `NEXT_PUBLIC_API_URL` to your Render backend URL
3. Redeploy

## 5. Verify Deployment

### Backend Health Check
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

### Frontend Check
Visit: https://kisaanai.vercel.app

### Test API Integration
```bash
curl https://kisaanai-backend.onrender.com/api/v1/commodities
```

## 6. Mobile App Deployment

### Update API URL in Mobile App
Edit `agribharat-mobile/src/constants/index.ts`:
```typescript
export const API_BASE_URL = 'https://kisaanai-backend.onrender.com';
```

### Build for Android
```bash
cd agribharat-mobile
eas build --platform android
```

### Build for iOS
```bash
eas build --platform ios
```

## 7. Monitoring & Logs

### Backend Logs (Render)
- Dashboard → kisaanai-backend → Logs
- Real-time log streaming available

### Frontend Logs (Vercel)
- Dashboard → kisaanai → Deployments → [Latest] → Logs
- Runtime logs in Functions tab

### Database Monitoring (Supabase)
- Dashboard → Database → Logs
- Performance metrics available

## 8. Custom Domain (Optional)

### Add Custom Domain to Vercel
1. Vercel Dashboard → kisaanai → Settings → Domains
2. Add your domain (e.g., kisaanai.com)
3. Configure DNS records as instructed

### Add Custom Domain to Render
1. Render Dashboard → kisaanai-backend → Settings → Custom Domain
2. Add your API domain (e.g., api.kisaanai.com)
3. Configure DNS records

## 9. Environment-Specific Configurations

### Production Checklist
- ✅ DEBUG=False in backend
- ✅ Strong SECRET_KEY generated
- ✅ CORS properly configured
- ✅ Database connection pooling enabled
- ✅ Rate limiting configured
- ✅ HTTPS enforced
- ✅ API keys secured in environment variables
- ✅ Error tracking enabled (Sentry recommended)

### Staging Environment
Create separate deployments for staging:
- Backend: `kisaanai-backend-staging` on Render
- Frontend: Preview deployments on Vercel (automatic for PRs)

## 10. Continuous Deployment

### Automatic Deployments
Both Vercel and Render support automatic deployments:

- **Vercel**: Deploys automatically on push to `main` branch
- **Render**: Deploys automatically on push to `main` branch

### Manual Deployments
- **Vercel**: `vercel --prod` from CLI
- **Render**: Click "Manual Deploy" in dashboard

## 11. Troubleshooting

### Backend Not Starting
- Check Render logs for errors
- Verify all environment variables are set
- Check database connection string
- Ensure Python version is 3.11+

### Frontend Build Failing
- Check Vercel build logs
- Verify Node.js version (18+)
- Check for TypeScript errors
- Ensure all dependencies are in package.json

### CORS Errors
- Verify CORS_ORIGINS includes your frontend URL
- Check that backend is returning proper CORS headers
- Ensure no trailing slashes in URLs

### Database Connection Issues
- Verify Supabase connection string
- Check if IP is whitelisted (Supabase allows all by default)
- Test connection with psql

## 12. Scaling Considerations

### Backend Scaling (Render)
- Upgrade to Standard plan for auto-scaling
- Configure horizontal scaling based on CPU/memory
- Add Redis for caching (Render Redis add-on)

### Frontend Scaling (Vercel)
- Vercel automatically scales
- Enable Edge Functions for better performance
- Use ISR (Incremental Static Regeneration) for dynamic pages

### Database Scaling (Supabase)
- Upgrade plan for more connections
- Enable connection pooling
- Add read replicas for read-heavy workloads

## 13. Security Best Practices

- 🔒 Never commit API keys to Git
- 🔒 Use environment variables for all secrets
- 🔒 Enable rate limiting on backend
- 🔒 Implement proper authentication
- 🔒 Use HTTPS everywhere
- 🔒 Regular security audits
- 🔒 Keep dependencies updated

## 14. Cost Optimization

### Free Tier Limits
- **Vercel**: 100GB bandwidth/month, unlimited deployments
- **Render**: 750 hours/month free (1 instance)
- **Supabase**: 500MB database, 2GB bandwidth

### Optimization Tips
- Use caching aggressively (Redis)
- Optimize images (Next.js Image component)
- Enable compression
- Use CDN for static assets
- Monitor usage in dashboards

## Support

For deployment issues:
- Vercel: https://vercel.com/support
- Render: https://render.com/docs
- Supabase: https://supabase.com/docs

---

**Deployment Status**: Ready for Production 🚀
**Last Updated**: February 15, 2026
