from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select, desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_session
from app.core.auth import get_or_create_user, get_user_from_request
from app.models.models import Ticker, MetricsSnapshot, RiskSnapshot, NewsArticle, AISnapshot, PricePoint, User
from app.api.schemas import TickerCreate, DashboardRow, RiskDetail, MessageResponse, ChatRequest, ChatResponse, ChatMessage
from app.services.market_data import refresh_ticker_market_data
from app.services.news_service import refresh_ticker_news, get_recent_news
from app.services.ai_service import AIService
from app.services.risk_scoring import calculate_risk_score, get_trend
from app.services.forecasting import generate_risk_forecast, store_forecast
from app.services.recommendations import generate_smart_recommendations, format_recommendations_for_display
import json

router = APIRouter()
ai_service = AIService()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "risklattice"}


@router.get("/test/{symbol}")
async def test_fetch(symbol: str):
    """Test endpoint to check if Alpha Vantage works."""
    from app.core.config import settings
    from app.services.alphavantage_data import fetch_price_data_alphavantage
    
    try:
        # Check if API key is set
        api_key = settings.alphavantage_api_key
        if not api_key:
            return {
                "symbol": symbol,
                "error": "ALPHAVANTAGE_API_KEY not set",
                "api_key_configured": False,
                "test": "failed"
            }
        
        # Try to fetch data
        df = fetch_price_data_alphavantage(symbol, days=30)
        
        if df.empty:
            return {
                "symbol": symbol,
                "error": "No data returned",
                "api_key_configured": True,
                "test": "failed"
            }
        
        return {
            "symbol": symbol,
            "api_key_configured": True,
            "history_rows": len(df),
            "current_price": float(df['Close'].iloc[-1]) if not df.empty else None,
            "test": "success"
        }
    except Exception as e:
        import traceback
        return {
            "symbol": symbol,
            "error": str(e),
            "api_key_configured": bool(settings.alphavantage_api_key),
            "test": "failed"
        }


@router.get("/tickers", response_model=List[str])
async def list_tickers(
    session: Session = Depends(get_session),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """List all tickers in user's watchlist."""
    if not x_session_id:
        return []
    
    user = get_or_create_user(session, x_session_id)
    statement = select(Ticker).where(Ticker.user_id == user.id)
    tickers = session.exec(statement).all()
    return [t.symbol for t in tickers]


@router.post("/tickers", response_model=MessageResponse)
async def add_ticker(
    ticker: TickerCreate, 
    session: Session = Depends(get_session),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """Add a ticker to user's watchlist."""
    if not x_session_id:
        raise HTTPException(status_code=401, detail="Session ID required")
    
    symbol = ticker.symbol.upper().strip()
    
    # Get or create user
    user = get_or_create_user(session, x_session_id)
    
    # Check if ticker already exists for this user
    existing = session.exec(
        select(Ticker).where(Ticker.symbol == symbol, Ticker.user_id == user.id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Ticker {symbol} already in your watchlist")
    
    new_ticker = Ticker(symbol=symbol, user_id=user.id)
    session.add(new_ticker)
    session.commit()
    
    # Return immediately - processing happens via scheduler or manual refresh
    return MessageResponse(message=f"Ticker {symbol} added successfully. Click 'Refresh All' to load data.")


@router.delete("/tickers/{symbol}", response_model=MessageResponse)
async def remove_ticker(
    symbol: str, 
    session: Session = Depends(get_session),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """Remove a ticker from user's watchlist."""
    if not x_session_id:
        raise HTTPException(status_code=401, detail="Session ID required")
    
    symbol = symbol.upper().strip()
    user = get_or_create_user(session, x_session_id)
    
    ticker = session.exec(
        select(Ticker).where(Ticker.symbol == symbol, Ticker.user_id == user.id)
    ).first()
    if not ticker:
        raise HTTPException(status_code=404, detail=f"Ticker {symbol} not found in your watchlist")
    
    session.delete(ticker)
    session.commit()
    return MessageResponse(message=f"Ticker {symbol} removed successfully")


@router.get("/dashboard", response_model=List[DashboardRow])
async def get_dashboard(
    session: Session = Depends(get_session),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """Get dashboard summary for all tickers belonging to the current user."""
    rows = []
    
    # Get or create user from session
    if x_session_id:
        user = get_or_create_user(session, x_session_id)
        # Only get tickers for this user
        tickers = session.exec(select(Ticker).where(Ticker.user_id == user.id)).all()
    else:
        # If no session ID, return empty (frontend should always send session ID)
        # But for backwards compatibility, return all tickers (legacy behavior)
        tickers = session.exec(select(Ticker)).all()
    
    rows = []
    
    for ticker in tickers:
        # Get latest metrics
        metrics_stmt = select(MetricsSnapshot).where(
            MetricsSnapshot.symbol == ticker.symbol
        ).order_by(desc(MetricsSnapshot.ts)).limit(1)
        latest_metrics = session.exec(metrics_stmt).first()
        
        # Get latest risk score
        risk_stmt = select(RiskSnapshot).where(
            RiskSnapshot.symbol == ticker.symbol
        ).order_by(desc(RiskSnapshot.ts)).limit(1)
        latest_risk = session.exec(risk_stmt).first()
        
        # Always show ticker, even if still processing
        # Get trend
        risk_stmt2 = select(RiskSnapshot).where(
            RiskSnapshot.symbol == ticker.symbol
        ).order_by(desc(RiskSnapshot.ts)).limit(2)
        risk_snapshots = list(session.exec(risk_stmt2))
        
        trend = "new"
        if len(risk_snapshots) >= 2:
            diff = risk_snapshots[0].total_score - risk_snapshots[1].total_score
            if diff > 5:
                trend = "up"
            elif diff < -5:
                trend = "down"
            else:
                trend = "flat"
        elif len(risk_snapshots) == 1:
            trend = "new"
        
        rows.append(DashboardRow(
            ticker=ticker.symbol,
            price=latest_metrics.price if latest_metrics else 0.0,
            return_7d=latest_metrics.return_7d if latest_metrics else 0.0,
            volatility=latest_metrics.vol_ann if latest_metrics else 0.0,
            max_drawdown=latest_metrics.max_drawdown if latest_metrics else 0.0,
            risk_score=latest_risk.total_score if latest_risk else 0.0,
            trend=trend,
            last_updated=latest_risk.ts if latest_risk else (latest_metrics.ts if latest_metrics else datetime.utcnow())
        ))
    
    return rows


@router.get("/risk/{symbol}", response_model=RiskDetail)
async def get_risk_detail(
    symbol: str, 
    period: str = "90d", 
    session: Session = Depends(get_session),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """Get detailed risk analysis for a ticker. Fetches data if needed but does NOT add to watchlist."""
    symbol = symbol.upper().strip()
    
    # Check if ticker exists in watchlist for this user (optional - doesn't block if not found)
    ticker = None
    if x_session_id:
        user = get_or_create_user(session, x_session_id)
        ticker = session.exec(
            select(Ticker).where(Ticker.symbol == symbol, Ticker.user_id == user.id)
        ).first()
    
    # Check if we have data, if not fetch it
    metrics_stmt = select(MetricsSnapshot).where(
        MetricsSnapshot.symbol == symbol
    ).order_by(desc(MetricsSnapshot.ts)).limit(1)
    latest_metrics = session.exec(metrics_stmt).first()
    
    # Also check if we have risk scores and AI analysis
    risk_check_stmt = select(RiskSnapshot).where(
        RiskSnapshot.symbol == symbol
    ).order_by(desc(RiskSnapshot.ts)).limit(1)
    existing_risk = session.exec(risk_check_stmt).first()
    
    ai_check_stmt = select(AISnapshot).where(
        AISnapshot.symbol == symbol
    ).order_by(desc(AISnapshot.ts)).limit(1)
    existing_ai = session.exec(ai_check_stmt).first()
    
    # Fetch data if we're missing metrics, risk scores, or AI analysis
    if not latest_metrics or not existing_risk or not existing_ai:
        # No data available, trigger a refresh
        try:
            print(f"\n{'='*60}")
            print(f"AUTO-FETCHING DATA FOR {symbol} (not in watchlist or no data)")
            print(f"{'='*60}")
            
            # Refresh market data
            market_result = refresh_ticker_market_data(session, symbol)
            if market_result.get("error"):
                error_detail = market_result.get("error", "Unknown error")
                print(f"✗ Market data fetch failed: {error_detail}")
                raise HTTPException(status_code=404, detail=f"Could not fetch data for {symbol}: {error_detail}")
            
            # Commit market data
            session.commit()
            print(f"✓ Market data committed for {symbol}")
            
            # Refresh news (with better error handling)
            news_result = None
            try:
                print(f"\n{'='*60}")
                print(f"FETCHING NEWS FOR {symbol}")
                print(f"{'='*60}")
                news_result = refresh_ticker_news(session, symbol)
                session.commit()  # Make sure news is committed
                if news_result.get("error"):
                    print(f"⚠ News fetch returned error for {symbol}: {news_result['error']}")
                else:
                    count = news_result.get('count', 0)
                    print(f"✓ News fetched for {symbol}: {count} articles")
                    
                    # Verify news was stored
                    stored_news = get_recent_news(session, symbol, limit=5)
                    print(f"✓ Verified: {len(stored_news)} news articles stored in database for {symbol}")
                print(f"{'='*60}\n")
            except Exception as e:
                print(f"⚠ News refresh exception for {symbol}: {e}")
                import traceback
                traceback.print_exc()
            
            # Process AI and risk scoring (this will work even with no news, using market data)
            print(f"\n{'='*60}")
            print(f"PROCESSING AI AND RISK SCORING FOR {symbol}")
            print(f"{'='*60}")
            await process_ticker(session, symbol)
            session.commit()  # Ensure all data is committed
            
            # Verify AI snapshot was created
            ai_check = select(AISnapshot).where(
                AISnapshot.symbol == symbol
            ).order_by(desc(AISnapshot.ts)).limit(1)
            ai_created = session.exec(ai_check).first()
            if ai_created:
                print(f"✓ AI analysis created: {ai_created.summary[:100]}...")
            else:
                print(f"⚠ WARNING: No AI snapshot found for {symbol} after processing!")
            
            # Verify risk snapshot was created
            risk_check = select(RiskSnapshot).where(
                RiskSnapshot.symbol == symbol
            ).order_by(desc(RiskSnapshot.ts)).limit(1)
            risk_created = session.exec(risk_check).first()
            if risk_created:
                print(f"✓ Risk score created: {risk_created.total_score}")
            else:
                print(f"⚠ WARNING: No risk snapshot found for {symbol} after processing!")
            
            print(f"{'='*60}\n")
            
            # Generate historical risk scores (90 days of history)
            try:
                from app.services.historical_risk import generate_historical_risk_scores
                generate_historical_risk_scores(session, symbol, days=90)
            except Exception as e:
                print(f"⚠ Error generating historical risk scores for {symbol}: {e}")
                # Don't fail the request if historical generation fails
            
            # Re-fetch metrics after processing
            session.commit()  # Ensure all commits are done
            metrics_stmt = select(MetricsSnapshot).where(
                MetricsSnapshot.symbol == symbol
            ).order_by(desc(MetricsSnapshot.ts)).limit(1)
            latest_metrics = session.exec(metrics_stmt).first()
            
            if not latest_metrics:
                print(f"⚠ WARNING: Metrics still not found after refresh for {symbol}")
                raise HTTPException(status_code=404, detail=f"Could not fetch metrics for {symbol} after refresh. Please try again.")
            
            print(f"✓ Successfully fetched and processed data for {symbol}")
            print(f"{'='*60}\n")
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            error_msg = str(e)
            print(f"✗ Error auto-fetching data for {symbol}: {error_msg}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error fetching data for {symbol}: {error_msg}")
    
    # Final check - ensure we have metrics
    if not latest_metrics:
        raise HTTPException(status_code=404, detail=f"No metrics available for {symbol}. The stock may not exist or data is still loading.")
    
    # Get latest risk score
    risk_stmt = select(RiskSnapshot).where(
        RiskSnapshot.symbol == symbol
    ).order_by(desc(RiskSnapshot.ts)).limit(1)
    latest_risk = session.exec(risk_stmt).first()
    
    if not latest_risk:
        # If no risk score, try to process the ticker (shouldn't happen after auto-fetch, but just in case)
        try:
            print(f"⚠ No risk score found for {symbol} after auto-fetch, processing...")
            await process_ticker(session, symbol)
            session.commit()
            risk_stmt = select(RiskSnapshot).where(
                RiskSnapshot.symbol == symbol
            ).order_by(desc(RiskSnapshot.ts)).limit(1)
            latest_risk = session.exec(risk_stmt).first()
        except Exception as e:
            print(f"Error processing risk score for {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    if not latest_risk:
        raise HTTPException(status_code=404, detail=f"No risk score available for {symbol}. Risk analysis may still be processing. Please try again in a few seconds.")
    
    # Get latest AI snapshot
    ai_stmt = select(AISnapshot).where(
        AISnapshot.symbol == symbol
    ).order_by(desc(AISnapshot.ts)).limit(1)
    latest_ai = session.exec(ai_stmt).first()
    
    # Get price history based on period parameter
    period_days_map = {
        "1d": 1,
        "1m": 30,
        "90d": 90,
        "6m": 180,
        "1y": 365,
        "5y": 1825
    }
    days = period_days_map.get(period, 90)
    cutoff = datetime.now() - timedelta(days=days)
    price_stmt = select(PricePoint).where(
        PricePoint.symbol == symbol,
        PricePoint.date >= cutoff
    ).order_by(PricePoint.date)
    price_points = session.exec(price_stmt).all()
    
    price_history = [
        {
            "date": pp.date.isoformat(),
            "close": pp.close,
            "volume": pp.volume
        }
        for pp in price_points
    ]
    
    # Get risk history (up to 90 days)
    cutoff_risk = datetime.now() - timedelta(days=90)
    risk_history_stmt = select(RiskSnapshot).where(
        RiskSnapshot.symbol == symbol,
        RiskSnapshot.ts >= cutoff_risk
    ).order_by(RiskSnapshot.ts).limit(90)
    risk_history_points = session.exec(risk_history_stmt).all()
    
    risk_history = [
        {
            "date": rs.ts.isoformat(),
            "total_score": rs.total_score,
            "market_score": rs.market_score,
            "news_score": rs.news_score
        }
        for rs in risk_history_points
    ]
    
    # Get recent news
    news_articles = get_recent_news(session, symbol, limit=10)
    recent_news = [
        {
            "title": article.title,
            "url": article.url,
            "published_at": article.published_at.isoformat(),
            "source": article.source
        }
        for article in news_articles
    ]
    
    reasons = json.loads(latest_risk.reasons_json) if latest_risk.reasons_json else []
    themes = json.loads(latest_ai.themes_json) if latest_ai and latest_ai.themes_json else []
    ai_summary = latest_ai.summary if latest_ai else "No AI analysis available."
    
    # Get market outlook from AI result (parse from raw_json if available)
    market_outlook = None
    if latest_ai and latest_ai.raw_json:
        try:
            ai_data = json.loads(latest_ai.raw_json)
            market_outlook = ai_data.get("market_outlook", "NEUTRAL")
        except:
            pass
    
    # Get trend
    risk_stmt2 = select(RiskSnapshot).where(
        RiskSnapshot.symbol == symbol
    ).order_by(desc(RiskSnapshot.ts)).limit(2)
    risk_snapshots = list(session.exec(risk_stmt2))
    
    trend = "new"
    if len(risk_snapshots) >= 2:
        diff = risk_snapshots[0].total_score - risk_snapshots[1].total_score
        if diff > 5:
            trend = "up"
        elif diff < -5:
            trend = "down"
        else:
            trend = "flat"
    
    return RiskDetail(
        symbol=symbol,
        current_price=latest_metrics.price,
        market_score=latest_risk.market_score,
        news_score=latest_risk.news_score,
        total_score=latest_risk.total_score,
        trend=trend,
        reasons=reasons,
        ai_summary=ai_summary,
        themes=themes,
        market_outlook=market_outlook,
        metrics={
            "return_7d": latest_metrics.return_7d,
            "volatility": latest_metrics.vol_ann,
            "max_drawdown": latest_metrics.max_drawdown
        },
        price_history=price_history,
        risk_history=risk_history,
        recent_news=recent_news
    )


@router.post("/refresh", response_model=MessageResponse)
async def refresh_all(session: Session = Depends(get_session)):
    """Refresh all tickers."""
    import time
    tickers = session.exec(select(Ticker)).all()
    
    if not tickers:
        return MessageResponse(message="No tickers in watchlist")
    
    print(f"\n{'='*60}")
    print(f"REFRESH ALL: Processing {len(tickers)} ticker(s)")
    print(f"{'='*60}")
    
    count = 0
    errors = []
    
    for idx, ticker in enumerate(tickers):
        try:
            # Add delay between tickers to avoid rate limiting (except first one)
            if idx > 0:
                delay = 5  # 5 second delay between tickers
                print(f"\nWaiting {delay}s before next ticker (to avoid rate limits)...")
                time.sleep(delay)
            
            symbol = ticker.symbol
            print(f"\n[{idx+1}/{len(tickers)}] Processing {symbol}...")
            
            # Refresh market data
            market_result = refresh_ticker_market_data(session, symbol)
            if market_result.get("error"):
                error_msg = market_result['error']
                errors.append(f"{symbol}: {error_msg}")
                print(f"✗ Skipping {symbol} due to error: {error_msg}")
                continue
            
            # Refresh news (non-blocking if it fails)
            try:
                refresh_ticker_news(session, symbol)
            except Exception as e:
                print(f"⚠ News refresh failed for {symbol} (non-critical): {e}")
            
            # Process AI and risk scoring
            print(f"Processing AI and risk scores for {symbol}...")
            await process_ticker(session, symbol)
            count += 1
            print(f"✓ Successfully refreshed {symbol}")
            
        except Exception as e:
            error_msg = str(e)
            errors.append(f"{ticker.symbol}: {error_msg}")
            print(f"✗ Error refreshing {ticker.symbol}: {error_msg}")
    
    print(f"\n{'='*60}")
    print(f"REFRESH COMPLETE: {count}/{len(tickers)} tickers refreshed successfully")
    if errors:
        print(f"Errors: {len(errors)}")
        for err in errors[:5]:  # Show first 5 errors
            print(f"  - {err}")
    print(f"{'='*60}\n")
    
    msg = f"Refreshed {count} ticker(s)"
    if errors:
        msg += f". {len(errors)} error(s) - check logs"
    return MessageResponse(message=msg)


@router.post("/refresh/{symbol}", response_model=MessageResponse)
async def refresh_symbol(symbol: str, session: Session = Depends(get_session)):
    """Refresh a specific ticker."""
    symbol = symbol.upper().strip()
    
    ticker = session.get(Ticker, symbol)
    if not ticker:
        raise HTTPException(status_code=404, detail=f"Ticker {symbol} not found")
    
    try:
        print(f"Starting refresh for {symbol}...")
        # Refresh market data
        market_result = refresh_ticker_market_data(session, symbol)
        if market_result.get("error"):
            error_msg = market_result['error']
            print(f"Market data error for {symbol}: {error_msg}")
            # Don't fail completely, try to continue with news
            if "429" not in error_msg and "rate limit" not in error_msg.lower():
                raise HTTPException(status_code=500, detail=f"Market data error: {error_msg}")
        
        # Refresh news (non-blocking if it fails)
        try:
            refresh_ticker_news(session, symbol)
        except Exception as e:
            print(f"News refresh error for {symbol} (non-critical): {e}")
        
        # Process AI and risk scoring
        await process_ticker(session, symbol)
        print(f"Successfully refreshed {symbol}")
        return MessageResponse(message=f"Ticker {symbol} refreshed successfully")
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Error refreshing {symbol}: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Error refreshing {symbol}: {error_msg}")


@router.get("/forecast/{symbol}")
async def get_forecast(symbol: str, days: int = 7, session: Session = Depends(get_session)):
    """Get risk forecast and recommendations for a ticker."""
    symbol = symbol.upper().strip()
    
    # Verify ticker exists
    ticker = session.get(Ticker, symbol)
    if not ticker:
        raise HTTPException(status_code=404, detail=f"Ticker {symbol} not found")
    
    # Get latest risk score
    risk_stmt = select(RiskSnapshot).where(
        RiskSnapshot.symbol == symbol
    ).order_by(desc(RiskSnapshot.ts)).limit(1)
    latest_risk = session.exec(risk_stmt).first()
    
    if not latest_risk:
        raise HTTPException(status_code=404, detail=f"No risk score available for {symbol}")
    
    current_score = latest_risk.total_score
    
    # Generate forecast
    try:
        forecast = generate_risk_forecast(session, symbol, current_score, days_ahead=days)
        
        # Store forecast
        store_forecast(session, symbol, forecast)
        
        # Get user tolerance (default to moderate)
        user_tolerance = ticker.risk_tolerance or "moderate"
        
        # Generate recommendations
        recommendations = generate_smart_recommendations(
            session, symbol, forecast, user_tolerance
        )
        formatted_recs = format_recommendations_for_display(recommendations)
        
        return {
            "symbol": symbol,
            "current_score": current_score,
            "forecast": forecast,
            "recommendations": formatted_recs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")


async def process_ticker(session: Session, symbol: str):
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
    
    # Prepare market data for AI analysis
    market_data = {
        "price": latest_metrics.price,
        "return_7d": latest_metrics.return_7d,
        "vol_ann": latest_metrics.vol_ann,
        "max_drawdown": latest_metrics.max_drawdown
    }
    
    # Run AI analysis with market context
    ai_result = ai_service.analyze_news(news_articles, market_data)
    
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
    
    # Generate historical risk scores (90 days) - automatic for all stocks
    try:
        from app.services.historical_risk import generate_historical_risk_scores
        generate_historical_risk_scores(session, symbol, days=90)
    except Exception as e:
        # Don't fail if historical generation fails - it's non-critical
        print(f"⚠ Historical risk generation failed for {symbol} (non-critical): {e}")


@router.get("/market/overview")
async def get_market_overview(session: Session = Depends(get_session)):
    """Get market overview for major stocks (for home page)."""
    major_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'JNJ']
    stocks = []
    
    for symbol in major_symbols:
        # Check if ticker exists in watchlist
        ticker = session.get(Ticker, symbol)
        if not ticker:
            # Ticker not in watchlist, skip or return placeholder
            continue
        
        # Get latest metrics
        metrics_stmt = select(MetricsSnapshot).where(
            MetricsSnapshot.symbol == symbol
        ).order_by(desc(MetricsSnapshot.ts)).limit(1)
        latest_metrics = session.exec(metrics_stmt).first()
        
        if latest_metrics:
            stocks.append({
                "symbol": symbol,
                "price": latest_metrics.price,
                "changePercent": latest_metrics.return_7d,
                "volume": 0  # Volume not stored in metrics snapshot
            })
    
    return {"stocks": stocks}


@router.get("/market/news")
async def get_market_news(session: Session = Depends(get_session), limit: int = 30):
    """Get recent market news from all tickers."""
    # Get news from last 7 days (not just 1 day)
    cutoff = datetime.now() - timedelta(days=7)
    statement = select(NewsArticle).where(
        NewsArticle.published_at >= cutoff
    ).order_by(NewsArticle.published_at.desc()).limit(limit)
    
    articles = session.exec(statement).all()
    
    # If we don't have enough articles, try to fetch fresh news for major stocks
    if len(articles) < 10:
        # Fetch fresh news for some major stocks to populate
        major_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        from app.services.news_service import fetch_google_news_rss, store_news_articles
        
        for symbol in major_symbols[:3]:  # Just fetch for first 3 to avoid delays
            try:
                articles_list = fetch_google_news_rss(symbol, days=1)
                store_news_articles(session, symbol, articles_list)
            except:
                continue
        
        # Re-query after fetching
        articles = session.exec(statement).all()
    
    return [
        {
            "title": article.title,
            "source": article.source,
            "url": article.url,
            "published_at": article.published_at.isoformat(),
            "symbol": article.symbol
        }
        for article in articles
    ]


@router.get("/market/quote/{symbol}")
async def get_stock_quote(symbol: str, session: Session = Depends(get_session)):
    """Get current stock quote - uses cached data from database."""
    from app.models.models import PricePoint
    
    symbol = symbol.upper().strip()
    
    # First check cached data from database
    metrics_stmt = select(MetricsSnapshot).where(
        MetricsSnapshot.symbol == symbol
    ).order_by(desc(MetricsSnapshot.ts)).limit(1)
    latest_metrics = session.exec(metrics_stmt).first()
    
    # Calculate daily return from recent price points
    daily_change_percent = 0.0
    if latest_metrics and latest_metrics.price and latest_metrics.price > 0:
        # Get last two price points to calculate daily change
        price_points_stmt = select(PricePoint).where(
            PricePoint.symbol == symbol
        ).order_by(desc(PricePoint.date)).limit(2)
        price_points = session.exec(price_points_stmt).all()
        
        if len(price_points) >= 2:
            current_price = float(price_points[0].close)
            previous_price = float(price_points[1].close)
            if previous_price > 0:
                daily_change_percent = ((current_price - previous_price) / previous_price) * 100
        
        return {
            "symbol": symbol,
            "price": latest_metrics.price,
            "changePercent": daily_change_percent,  # Daily percentage change
            "timestamp": latest_metrics.ts.isoformat()
        }
    
    # No cached data available - return error
    # Note: To get data, add stock to watchlist and use "Refresh All" button
    return {
        "symbol": symbol,
        "error": "No cached data available"
    }


@router.post("/agent/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: ChatRequest, 
    session: Session = Depends(get_session),
    x_session_id: Optional[str] = Header(None, alias="X-Session-Id")
):
    """Chat with AI agent about financial and stock-related questions."""
    watchlist_data = []
    news_data = []
    forecast_data = []
    market_summary = {}
    
    try:
        # Get watchlist data with full metrics - filtered by user
        try:
            if x_session_id:
                user = get_or_create_user(session, x_session_id)
                statement = select(Ticker).where(Ticker.user_id == user.id)
            else:
                # If no session ID, return empty watchlist
                statement = select(Ticker).where(Ticker.id == -1)  # Return nothing
            all_tickers = session.exec(statement).all()
            
            for ticker in all_tickers[:15]:  # Limit to 15 for performance
                try:
                    # Get latest metrics
                    metrics_stmt = select(MetricsSnapshot).where(
                        MetricsSnapshot.symbol == ticker.symbol
                    ).order_by(desc(MetricsSnapshot.ts)).limit(1)
                    latest_metrics = session.exec(metrics_stmt).first()
                    
                    # Get latest risk score
                    risk_stmt = select(RiskSnapshot).where(
                        RiskSnapshot.symbol == ticker.symbol
                    ).order_by(desc(RiskSnapshot.ts)).limit(1)
                    latest_risk = session.exec(risk_stmt).first()
                    
                    if latest_metrics:
                        watchlist_data.append({
                            "symbol": ticker.symbol,
                            "price": latest_metrics.price,
                            "return_7d": latest_metrics.return_7d,
                            "risk_score": latest_risk.total_score if latest_risk else 0,
                            "volatility": latest_metrics.vol_ann,
                            "max_drawdown": latest_metrics.max_drawdown
                        })
                except Exception as e:
                    print(f"Error processing ticker {ticker.symbol}: {e}")
                    continue
        except Exception as e:
            print(f"Error loading watchlist: {e}")
        
        # Calculate market summary
        if watchlist_data:
            try:
                avg_risk = sum(t.get('risk_score', 0) for t in watchlist_data) / len(watchlist_data)
                market_summary = {
                    "total_tickers": len(watchlist_data),
                    "avg_risk_score": avg_risk
                }
            except Exception:
                pass
        
        # Get recent news articles for context
        try:
            cutoff = datetime.now() - timedelta(days=7)
            news_stmt = select(NewsArticle).where(
                NewsArticle.published_at >= cutoff
            ).order_by(desc(NewsArticle.published_at)).limit(20)
            recent_news = session.exec(news_stmt).all()
            
            for article in recent_news:
                try:
                    news_data.append({
                        "title": article.title,
                        "source": article.source,
                        "url": article.url,
                        "published_at": article.published_at.isoformat() if article.published_at else None,
                        "symbol": article.symbol
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"Error loading news: {e}")
        
        # Get risk forecasts (optional, don't fail if it errors)
        try:
            from app.models.models import RiskForecast
            forecasts_stmt = select(RiskForecast).order_by(desc(RiskForecast.created_at)).limit(8)
            forecasts = session.exec(forecasts_stmt).all()
            
            for forecast in forecasts:
                try:
                    forecast_data.append({
                        "symbol": forecast.symbol,
                        "forecast_date": forecast.forecast_date.isoformat() if forecast.forecast_date else None,
                        "predicted_score": forecast.predicted_score,
                        "confidence": forecast.confidence
                    })
                except Exception:
                    continue
        except Exception:
            pass  # Forecasts are optional
        
    except Exception as e:
        print(f"Error gathering context: {e}")
    
    context_data = {
        "watchlist": watchlist_data,
        "market_summary": market_summary,
        "recent_news": news_data,
        "forecasts": forecast_data
    }
    
    # Prepare conversation history
    history = []
    if request.conversation_history:
        try:
            for msg in request.conversation_history:
                history.append({"role": msg.role, "content": msg.content})
        except Exception:
            pass
    
    # Get AI response
    try:
        ai_response = ai_service.chat(request.message, context_data, history)
        if not ai_response or len(ai_response.strip()) == 0:
            ai_response = "I apologize, but I couldn't generate a response. Please try again."
    except Exception as e:
        print(f"Error getting AI response: {e}")
        ai_response = ai_service._chat_fallback(request.message, context_data, history)
    
    # Build conversation history
    try:
        new_history = request.conversation_history.copy() if request.conversation_history else []
        new_history.append(ChatMessage(role="user", content=request.message))
        new_history.append(ChatMessage(role="assistant", content=ai_response))
    except Exception:
        new_history = [
            ChatMessage(role="user", content=request.message),
            ChatMessage(role="assistant", content=ai_response)
        ]
    
    return ChatResponse(
        message=ai_response,
        conversation_history=new_history
    )

