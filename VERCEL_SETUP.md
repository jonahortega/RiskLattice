# Vercel Deployment Fix

## Issues Fixed:
1. ✅ Replaced all hardcoded `localhost:8000` URLs with environment variable
2. ✅ Simplified `vercel.json` for proper Vercel detection
3. ✅ Added `.vercelignore` to exclude backend files

## Next Steps in Vercel Dashboard:

### 1. Set Root Directory
- Go to Vercel Dashboard → Your Project → Settings → General
- Set **Root Directory** to: `frontend`
- Save

### 2. Update Build Settings (if needed)
- Framework Preset: **Vite** (or Other)
- Build Command: `npm run build` (auto-detected)
- Output Directory: `dist` (auto-detected)
- Install Command: `npm install` (auto-detected)

### 3. Add Environment Variable
- Go to Settings → Environment Variables
- Add: `VITE_API_URL` = `https://your-backend-url.railway.app/api`
- (You'll need to deploy backend first on Railway/Render)

### 4. Redeploy
- Go to Deployments tab
- Click the 3 dots on latest deployment
- Click **Redeploy**

## Testing
After redeploy, your Vercel URL should show the RiskLattice homepage.

If you still get 404:
- Check that Root Directory is set to `frontend`
- Check build logs in Vercel for errors
- Verify `dist` folder is being generated in build

