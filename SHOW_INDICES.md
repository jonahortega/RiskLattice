# Fixed: Indices Now Show Even Without Data

## What I Changed:

Changed the code to show ALL stocks in the list, even if they don't have cached data. Now the indices (NASDAQ, Dow Jones, S&P 500) will appear even if they don't have price data yet.

## Result:

- NASDAQ, Dow Jones, and S&P 500 will appear first
- They'll show their custom images
- If they don't have data, they'll show "Loading..." or placeholder
- Once you add them to watchlist and refresh, they'll show prices

## To See It:

1. **Restart Docker**: Press `Ctrl+C`, then `docker-compose up`
2. **Refresh browser**: http://localhost:3000 (hard refresh: Cmd+Shift+R)

The indices should now appear first in the list, even if they don't have data yet!

