import feedparser
import httpx
from datetime import datetime, timedelta
from typing import List, Dict
from sqlmodel import Session, select
from app.models.models import NewsArticle


def fetch_google_news_rss(symbol: str, days: int = 7) -> List[Dict]:
    """Fetch news from Google News RSS feed. Tries multiple search queries for better results."""
    # Detect if this is a crypto symbol
    is_crypto = '-' in symbol and any(crypto in symbol.upper() for crypto in ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA', 'MATIC', 'LTC', 'AVAX', 'UNI', 'LINK', 'ATOM', 'ETC', 'XLM', 'ALGO', 'ZEC'])
    
    # Extract base symbol for crypto (e.g., BTC-USD -> BTC)
    base_symbol = symbol.split('-')[0] if '-' in symbol else symbol
    
    # Try multiple search queries for better results (some symbols need different formats)
    if is_crypto:
        search_queries = [
            f"{base_symbol}+crypto",
            f"{base_symbol}+cryptocurrency",
            f"{symbol}+crypto",
            f"{base_symbol}+bitcoin" if base_symbol == "BTC" else f"{base_symbol}+blockchain",
            base_symbol  # Just the base symbol
        ]
    else:
        search_queries = [
            f"{symbol}+stock",
            f"{symbol}+NYSE",
            f"{symbol}+NASDAQ",
            symbol  # Just the symbol itself
        ]
    
    all_articles = []
    seen_urls = set()
    
    for query in search_queries:
        try:
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for entry in feed.entries[:20]:  # Limit to 20 most recent
                try:
                    # Skip if we've seen this URL
                    if entry.link in seen_urls:
                        continue
                    
                    published = datetime(*entry.published_parsed[:6])
                    if published >= cutoff_date:
                        # Check if article is relevant (contains symbol or relevant keywords)
                        title_lower = entry.title.lower()
                        symbol_lower = symbol.lower()
                        base_symbol_lower = base_symbol.lower() if is_crypto else symbol_lower
                        
                        # Different relevance checks for crypto vs stocks
                        if is_crypto:
                            relevant_keywords = ['crypto', 'cryptocurrency', 'bitcoin', 'ethereum', 'blockchain', 'trading', 'market', 'price']
                            is_relevant = (base_symbol_lower in title_lower or symbol_lower in title_lower or 
                                         any(kw in title_lower for kw in relevant_keywords))
                        else:
                            relevant_keywords = ['stock', 'share', 'trading', 'market', 'earnings', 'revenue']
                            is_relevant = (symbol_lower in title_lower or 
                                         any(kw in title_lower for kw in relevant_keywords))
                        
                        if is_relevant:
                            all_articles.append({
                                "title": entry.title,
                                "url": entry.link,
                                "published_at": published,
                                "source": entry.get("source", {}).get("title", "Unknown")
                            })
                            seen_urls.add(entry.link)
                except:
                    continue
            
            # If we got good results, break early
            if len(all_articles) >= 10:
                break
        except Exception as e:
            print(f"Error fetching news for {symbol} with query '{query}': {e}")
            continue
    
    # Sort by date (newest first) and return
    all_articles.sort(key=lambda x: x["published_at"], reverse=True)
    return all_articles[:20]  # Return up to 20 articles


def store_news_articles(session: Session, symbol: str, articles: List[Dict]):
    """Store news articles in database, avoiding duplicates."""
    for article in articles:
        existing = session.exec(
            select(NewsArticle).where(
                NewsArticle.symbol == symbol,
                NewsArticle.url == article["url"]
            )
        ).first()
        
        if not existing:
            news_article = NewsArticle(
                symbol=symbol,
                title=article["title"],
                url=article["url"],
                published_at=article["published_at"],
                source=article["source"]
            )
            session.add(news_article)
    
    session.commit()


def get_recent_news(session: Session, symbol: str, limit: int = 15) -> List[NewsArticle]:
    """Get recent news articles for a ticker."""
    cutoff = datetime.now() - timedelta(days=7)
    statement = select(NewsArticle).where(
        NewsArticle.symbol == symbol,
        NewsArticle.published_at >= cutoff
    ).order_by(NewsArticle.published_at.desc()).limit(limit)
    
    return list(session.exec(statement))


def refresh_ticker_news(session: Session, symbol: str) -> Dict:
    """Refresh news for a ticker."""
    try:
        articles = fetch_google_news_rss(symbol)
        store_news_articles(session, symbol, articles)
        return {
            "success": True,
            "count": len(articles)
        }
    except Exception as e:
        return {"error": str(e)}

