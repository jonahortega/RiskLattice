# RiskLattice Deployment Guide

## Deploying to Vercel (Frontend)

### Step 1: Update API URLs for Production

The frontend currently uses `http://localhost:8000` for the API. You'll need to update this to point to your production backend.

**Option A: Environment Variable (Recommended)**

1. Create `.env.production` in `frontend/`:
```
VITE_API_URL=https://your-backend-url.railway.app/api
```

2. Update `frontend/src/api/client.ts` to use the environment variable:
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
```

### Step 2: Deploy Frontend to Vercel

1. **Via Vercel Dashboard:**
   - Go to https://vercel.com
   - Import your GitHub repository
   - Root Directory: `frontend`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Add Environment Variable: `VITE_API_URL=https://your-backend-url.railway.app/api`

2. **Via CLI:**
   ```bash
   cd frontend
   vercel
   ```

## Deploying Backend (Recommended: Railway or Render)

### Option A: Railway (Easiest)

1. Go to https://railway.app
2. Connect GitHub account
3. New Project → Deploy from GitHub
4. Select your RiskLattice repo
5. Root Directory: `backend`
6. Add Environment Variables:
   - `DATABASE_URL` (Railway provides PostgreSQL)
   - `OPENAI_API_KEY=your-key`
   - `ALPHA_VANTAGE_API_KEY=your-key`
   - `CORS_ORIGINS=https://your-vercel-app.vercel.app`

7. Railway will auto-detect Docker and deploy
8. Get your backend URL (e.g., `risklattice-backend.railway.app`)

### Option B: Render

1. Go to https://render.com
2. New → Web Service
3. Connect GitHub → Select RiskLattice repo
4. Settings:
   - Root Directory: `backend`
   - Environment: Docker
   - Build Command: (leave empty, Docker handles it)
   - Start Command: (leave empty, Docker handles it)
5. Add Environment Variables (same as Railway)
6. Deploy

## Connecting Domain (risklattice.com)

### Step 1: Point Domain to Vercel

1. In Vercel dashboard → Your Project → Settings → Domains
2. Add `risklattice.com` and `www.risklattice.com`
3. Vercel will show DNS records to add

### Step 2: Update DNS at Your Registrar

Add these records:
- **A Record**: `@` → Vercel's IP (shown in dashboard)
- **CNAME**: `www` → `cname.vercel-dns.com`

### Step 3: SSL Certificate

Vercel automatically provides SSL certificates (HTTPS) - no action needed!

## Environment Variables Summary

### Frontend (Vercel):
- `VITE_API_URL` - Your backend API URL

### Backend (Railway/Render):
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key
- `ALPHA_VANTAGE_API_KEY` - Alpha Vantage API key  
- `CORS_ORIGINS` - Comma-separated list of allowed origins

## Post-Deployment Checklist

- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Railway/Render
- [ ] API URL updated in frontend
- [ ] CORS configured to allow Vercel domain
- [ ] Database migrations completed
- [ ] Domain connected and SSL active
- [ ] Test all features (search, charts, AI assistant)
- [ ] Monitor logs for errors

