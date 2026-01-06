# Database Fix Applied

I've updated the database initialization to automatically add the missing columns when the app starts.

## What I Fixed:

1. Added code to automatically add `risk_tolerance` column to `ticker` table
2. Added code to automatically add `trend` column to `risksnapshot` table  
3. Created `riskforecast` table if it doesn't exist
4. Made columns nullable so existing data doesn't break

## Next Step:

**Restart Docker again:**

```bash
cd /Users/jonahortega/risklattice && docker-compose up --build
```

The database will be updated automatically when the app starts!

After restarting, you should see your tickers on the dashboard again.

