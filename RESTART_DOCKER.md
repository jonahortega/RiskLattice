# Restart Docker to See Changes

The frontend code changes need Docker to restart to be picked up.

## Steps:

1. **Stop Docker**: In your terminal (where Docker is running), press `Ctrl+C`

2. **Start Docker again**:
   ```bash
   docker-compose up
   ```

3. **Wait for it to start** (you'll see "VITE ready" and "Uvicorn running")

4. **Refresh browser**: http://localhost:3000

5. **Hard refresh**: Press `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows) to clear browser cache

The indices (NASDAQ, Dow Jones, S&P 500) should now appear first with their custom images!

