# Fixed: Market News Not Showing Multiple Articles

## What I Changed:

1. **Increased time range**: Changed from 1 day to 7 days (so more articles show up)
2. **Increased default limit**: Changed from 20 to 30 articles
3. **Auto-fetch if needed**: If there aren't enough articles, automatically fetches fresh news for major stocks

## Result:

- Shows more articles (up to 30)
- Shows articles from last 7 days (not just today)
- Automatically fetches fresh news if database is empty
- All articles are clickable and link to the source

## To See It:

1. **Restart Docker**: Press `Ctrl+C`, then `docker-compose up`
2. **Refresh browser**: http://localhost:3000
3. **Market News section** should now show multiple articles with clickable links!

The news should now show multiple articles from recent days!

