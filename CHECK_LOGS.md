# Check Backend Logs for Errors

The data isn't fetching. Let's see what errors are happening:

## Step 1: Check Terminal Logs

Look at your Terminal where Docker is running. Scroll up and look for error messages in RED or lines that say "Error" or "Exception".

Look for things like:
- "Error refreshing AAPL"
- "failed to resolve"
- "timeout"
- "connection error"

## Step 2: Try Manual Refresh

In a new Terminal window (keep Docker running), try:

```bash
curl -X POST http://localhost:8000/api/refresh/AAPL
```

This will show you the exact error message.

## Common Issues:

1. **Network timeout** - yfinance can't reach Yahoo Finance API
2. **No internet in Docker** - Docker container can't access the web
3. **yfinance error** - Library issue

**Tell me what errors you see in the Terminal logs or from the curl command!**

