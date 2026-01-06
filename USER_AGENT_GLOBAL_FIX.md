# User Agent Global Fix

I've set the User-Agent header globally at the module level, which is the correct way to configure yfinance. This should fix the blocking issue.

## Restart Docker:

**Terminal: Press `Ctrl + C`, then:**

```bash
cd /Users/jonahortega/risklattice && docker-compose up --build
```

**Wait 2-3 minutes for it to build and start.**

## Then:

1. Open http://localhost:3000
2. **WAIT 2-3 MINUTES** (let any rate limits clear)
3. Click "Refresh All" button
4. **WATCH TERMINAL** - you should see:
   - "Fetching AAPL (attempt 1/3)..."
   - "✓ Successfully fetched X rows for AAPL"
   - "✓ Metrics calculated: Price: $XXX.XX"
5. Wait 1-2 minutes for processing
6. **Refresh browser (F5)** to see the live data!

This should work now!

