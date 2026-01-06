"""
Generate historical risk scores from price data.
This allows stocks to have 90 days of risk history even if just added to watchlist.
"""
from datetime import datetime, timedelta
from sqlmodel import Session, select, desc
from typing import List, Dict
import numpy as np
import json
from app.models.models import PricePoint, MetricsSnapshot, RiskSnapshot, AISnapshot, NewsArticle
from app.services.risk_scoring import calculate_risk_score
from app.services.ai_service import AIService
from app.services.news_service import get_recent_news

ai_service = AIService()


def generate_historical_risk_scores(session: Session, symbol: str, days: int = 90):
    """Generate risk score history by processing historical price data. Creates snapshots for every trading day."""
    print(f"Generating {days}-day risk history for {symbol}...")
    
    # Get all price points for the last 90 days
    cutoff_date = datetime.now() - timedelta(days=days)
    price_stmt = select(PricePoint).where(
        PricePoint.symbol == symbol,
        PricePoint.date >= cutoff_date
    ).order_by(PricePoint.date)
    
    price_points = list(session.exec(price_stmt))
    
    if len(price_points) < 7:
        print(f"Not enough price data for {symbol} (need at least 7 days, got {len(price_points)})")
        return
    
    print(f"Found {len(price_points)} price points for {symbol}")
    
    # Get unique trading dates from price points (convert datetime to date)
    trading_dates = sorted(set([
        pp.date.date() if isinstance(pp.date, datetime) else pp.date 
        for pp in price_points
    ]))
    
    if len(trading_dates) < 7:
        print(f"Not enough trading dates for {symbol} (need at least 7)")
        return
    
    print(f"Processing {len(trading_dates)} trading dates...")
    
    risk_snapshots_created = 0
    risk_snapshots_skipped = 0
    
    # Process each trading date (oldest to newest)
    for idx, trading_date in enumerate(trading_dates):
        # Skip the first 6 days (need at least 7 days for calculations)
        if idx < 6:
            continue
        
        # Check if we already have a risk snapshot for this date (within 1 day tolerance)
        date_start = datetime.combine(trading_date, datetime.min.time())
        date_end = datetime.combine(trading_date, datetime.max.time())
        
        existing_stmt = select(RiskSnapshot).where(
            RiskSnapshot.symbol == symbol,
            RiskSnapshot.ts >= date_start - timedelta(days=1),
            RiskSnapshot.ts <= date_end + timedelta(days=1)
        ).limit(1)
        existing = session.exec(existing_stmt).first()
        
        if existing:
            risk_snapshots_skipped += 1
            continue  # Skip if we already have data for this date
        
        # Get price points up to and including this trading date
        points_up_to_date = [
            p for p in price_points 
            if (p.date.date() if isinstance(p.date, datetime) else p.date) <= trading_date
        ]
        
        if len(points_up_to_date) < 7:
            continue
        
        # Get the last 90 days of price points up to this date (or all available if less than 90)
        recent_points = points_up_to_date[-min(90, len(points_up_to_date)):]
        
        if len(recent_points) < 7:
            continue
        
        try:
            # Calculate price and metrics for this date
            current_price = float(recent_points[-1].close)
            
            # Calculate 7-day return (using the last 7 price points up to this date)
            if len(recent_points) >= 7:
                price_7d_ago = float(recent_points[-7].close)
                return_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
            else:
                return_7d = 0.0
            
            # Calculate volatility (annualized) from daily returns
            if len(recent_points) >= 2:
                returns = []
                for j in range(1, len(recent_points)):
                    ret = (float(recent_points[j].close) - float(recent_points[j-1].close)) / float(recent_points[j-1].close)
                    returns.append(ret)
                
                if returns:
                    std_dev = np.std(returns)
                    vol_ann = std_dev * np.sqrt(252) * 100  # Annualized
                else:
                    vol_ann = 0.0
            else:
                vol_ann = 0.0
            
            # Calculate max drawdown
            if len(recent_points) >= 2:
                prices = [float(p.close) for p in recent_points]
                peak = prices[0]
                max_dd = 0.0
                for price in prices:
                    if price > peak:
                        peak = price
                    dd = (peak - price) / peak * 100
                    if dd > max_dd:
                        max_dd = dd
            else:
                max_dd = 0.0
            
            # Prepare market data for AI analysis
            market_data = {
                "price": current_price,
                "return_7d": return_7d,
                "vol_ann": vol_ann,
                "max_drawdown": max_dd
            }
            
            # Get news articles available up to this date (last 7 days from this date)
            news_cutoff = date_start - timedelta(days=7)
            news_stmt = select(NewsArticle).where(
                NewsArticle.symbol == symbol,
                NewsArticle.published_at <= date_end,
                NewsArticle.published_at >= news_cutoff
            ).order_by(desc(NewsArticle.published_at)).limit(15)
            news_articles = list(session.exec(news_stmt))
            
            # Run AI analysis (even if no news, will use market data)
            ai_result = ai_service.analyze_news(news_articles, market_data)
            
            # Calculate and store risk score with the specific date
            metrics_dict = {
                "price": current_price,
                "return_7d": return_7d,
                "vol_ann": vol_ann,
                "max_drawdown": max_dd
            }
            calculate_risk_score(session, symbol, metrics_dict, ai_result, snapshot_date=date_start)
            
            risk_snapshots_created += 1
            
            # Commit every 10 snapshots to avoid long transactions
            if risk_snapshots_created % 10 == 0:
                session.commit()
                print(f"  Created {risk_snapshots_created} risk snapshots for {symbol} (skipped {risk_snapshots_skipped})...")
        
        except Exception as e:
            print(f"  Error generating risk snapshot for {symbol} on {trading_date}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    session.commit()
    print(f"✓ Generated {risk_snapshots_created} historical risk snapshots for {symbol} (skipped {risk_snapshots_skipped} that already existed)")
