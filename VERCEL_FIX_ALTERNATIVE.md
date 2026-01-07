# Alternative Fix: If Root Directory Setting Not Visible

## Option 1: Create vercel.json in Root (Done ✅)
I've created a `vercel.json` in the root that tells Vercel to:
- Install dependencies in `frontend/`
- Build from `frontend/`
- Serve from `frontend/dist/`

## Option 2: Reconfigure Project in Vercel

1. **Delete current Vercel project** (or create a new one):
   - Go to your project → Settings → Danger Zone → Delete Project

2. **Import again from GitHub:**
   - Click "Add New..." → Project
   - Import your GitHub repository
   - In the configuration screen, you'll see "Root Directory" option
   - Set it to: `frontend`
   - Framework: Vite (or Other)
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Click Deploy

## Option 3: Move Frontend to Root (Not Recommended)

If the above doesn't work, we could move frontend files to root, but this is messy.

## Check Current Setup

After I push the updated `vercel.json`, try redeploying. The root `vercel.json` should tell Vercel where to build from.

