# Fix Vercel 404 Error

## Problem
Getting 404 error even though deployment succeeded.

## Solution

### Option 1: Set Root Directory in Vercel Dashboard (Easiest)

1. Go to your Vercel project: https://vercel.com/dashboard
2. Click on your project → **Settings** → **General**
3. Under **Root Directory**, click **Edit**
4. Set it to: `frontend`
5. Save
6. Redeploy (Settings → Deployments → Redeploy latest)

### Option 2: Deploy from Frontend Directory

If you want to deploy just the frontend:

1. Go to your project settings in Vercel
2. Go to **Settings** → **General**
3. Set **Root Directory** to `frontend`
4. Or create a new project and point it to the `frontend` folder

### Option 3: Use vercel.json in Root

The `vercel.json` in the root should work, but you need to tell Vercel the root directory.

## After Fixing

1. **Add Environment Variable in Vercel:**
   - Go to Project → Settings → Environment Variables
   - Add: `VITE_API_URL` = `https://your-backend-url.railway.app/api`
   - (You'll need to deploy your backend first)

2. **Redeploy:**
   - Go to Deployments tab
   - Click the 3 dots on latest deployment → Redeploy

3. **Test:**
   - Visit your Vercel URL
   - Should see the RiskLattice homepage

## Quick Check

After fixing, your Vercel project settings should have:
- **Framework Preset:** Vite (or Other)
- **Root Directory:** `frontend`
- **Build Command:** `npm run build` (or leave empty, Vercel auto-detects)
- **Output Directory:** `dist`
- **Install Command:** `npm install`

