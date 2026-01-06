from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlmodel import Session, select
from app.core.database import engine
from app.core.config import settings
from app.models.models import Ticker
from app.services.market_data import refresh_ticker_market_data
from app.services.news_service import refresh_ticker_news
from app.services.ai_service import AIService
from app.services.risk_scoring import calculate_risk_score
from app.services.news_service import get_recent_news
from sqlmodel import select, desc
from app.models.models import MetricsSnapshot, AISnapshot
import json
import asyncio


scheduler = AsyncIOScheduler()


async def process_ticker_async(session: Session, symbol: str):
    """Process a ticker: get metrics, news, run AI, calculate risk."""
    # Get latest metrics
    metrics_stmt = select(MetricsSnapshot).where(
        MetricsSnapshot.symbol == symbol
    ).order_by(desc(MetricsSnapshot.ts)).limit(1)
    latest_metrics = session.exec(metrics_stmt).first()
    
    if not latest_metrics:
        return
    
    # Get recent news
    news_articles = get_recent_news(session, symbol, limit=15)
    
    # Run AI analysis
    ai_service = AIService()
    ai_result = ai_service.analyze_news(news_articles)
    
    # Store AI snapshot
    ai_snapshot = AISnapshot(
        symbol=symbol,
        sentiment=ai_result["sentiment"],
        themes_json=json.dumps(ai_result["themes"]),
        summary=ai_result["summary"],
        raw_json=ai_result["raw_json"]
    )
    session.add(ai_snapshot)
    session.commit()
    
    # Calculate risk score
    metrics_dict = {
        "price": latest_metrics.price,
        "return_7d": latest_metrics.return_7d,
        "vol_ann": latest_metrics.vol_ann,
        "max_drawdown": latest_metrics.max_drawdown
    }
    calculate_risk_score(session, symbol, metrics_dict, ai_result)


async def refresh_all_tickers():
    """Background job to refresh all tickers."""
    with Session(engine) as session:
        tickers = session.exec(select(Ticker)).all()
        
        for ticker in tickers:
            try:
                # Refresh market data
                refresh_ticker_market_data(session, ticker.symbol)
                # Refresh news
                refresh_ticker_news(session, ticker.symbol)
                # Process AI and risk scoring
                await process_ticker_async(session, ticker.symbol)
                print(f"Refreshed {ticker.symbol}")
            except Exception as e:
                print(f"Error refreshing {ticker.symbol}: {e}")


def start_scheduler():
    """Start the background scheduler."""
    interval_minutes = settings.refresh_interval_minutes
    scheduler.add_job(
        refresh_all_tickers,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="refresh_tickers",
        name="Refresh all tickers",
        replace_existing=True
    )
    scheduler.start()
    print(f"Scheduler started: refreshing every {interval_minutes} minutes")

