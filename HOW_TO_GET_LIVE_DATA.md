# How to Get Live Data

## Current Setup (What You Have Now)

Your site currently shows **cached data** (data that was fetched before). This is fast and reliable!

## To Get Fresh/Live Data:

### Option 1: Use "Refresh All" Button (Easiest)

1. Go to your site: http://localhost:3000
2. Click **"My Watchlist"** (or go to the dashboard)
3. Click the **"Refresh All Data"** button
4. This will fetch fresh data for all stocks in your watchlist

**Note:** Alpha Vantage free tier allows **25 requests per day**. So if you have 10 stocks in your watchlist, you can refresh them about 2 times per day.

---

### Option 2: Get More API Keys (Free)

You can get multiple free Alpha Vantage API keys to get more requests:

1. Go to: https://www.alphavantage.co/support/#api-key
2. Sign up for a free account (or multiple accounts with different emails)
3. Get multiple API keys
4. Add them to your `.env` file (we can set up key rotation)

This way you can get 25 requests per key per day (2 keys = 50 requests/day, etc.)

---

### Option 3: Use Your Existing Stocks

If you already have stocks in your watchlist (like AAPL, TSLA, GOOGL), they should have cached data. The home page will show that cached data instantly!

---

## Summary:

- **Home page**: Shows cached data (instant, no API calls)
- **Refresh button**: Fetches fresh live data (uses API quota)
- **Free tier**: 25 requests/day (enough for ~10 stocks refreshed 2x/day)

The current setup is actually perfect for a watchlist! You just refresh when you want fresh data.

