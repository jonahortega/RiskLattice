import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from sqlmodel import Session, select
from app.models.models import PricePoint, MetricsSnapshot
from app.services.alphavantage_data import fetch_price_data_alphavantage


def fetch_price_data(symbol: str, days: int = 90) -> pd.DataFrame:
    """Fetch price history for a ticker. Uses yfinance for crypto, Alpha Vantage for stocks."""
    import time
    from app.services.alphavantage_data import is_crypto_symbol, fetch_price_data_with_yfinance
    
    # Check if this is crypto - ALWAYS use yfinance (it's free and works better)
    if is_crypto_symbol(symbol):
        print(f"\n{'='*50}")
        print(f"FETCHING CRYPTO: {symbol}")
        print(f"{'='*50}")
        try:
            print(f"Using yfinance for crypto symbol: {symbol}")
            df = fetch_price_data_with_yfinance(symbol, days)
            if not df.empty:
                print(f"✓ Successfully fetched {symbol} using yfinance")
                print(f"{'='*50}\n")
                return df
            else:
                print(f"⚠ yfinance returned empty DataFrame for {symbol}")
                print(f"{'='*50}\n")
                raise ValueError(f"yfinance returned empty data for {symbol}")
        except ImportError:
            print(f"✗ yfinance not installed. Install with: pip install yfinance")
            raise
        except Exception as e:
            print(f"✗ yfinance failed for {symbol}: {e}")
            print(f"{'='*50}\n")
            # Don't fall back to Alpha Vantage for crypto - it's rate limited and unreliable
            raise ValueError(f"Failed to fetch crypto data for {symbol} using yfinance: {e}")
    
    # For stocks, use Alpha Vantage
    # Alpha Vantage has rate limits (5 calls per minute for free tier)
    # Add a small delay to be safe
    time.sleep(1)
    
    try:
        # Use Alpha Vantage API for stocks
        df = fetch_price_data_alphavantage(symbol, days)
        return df
    except ValueError as e:
        # Rate limit or API key error
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            print(f"⚠ Rate limited. Free tier allows 5 calls/minute. Please wait...")
        raise
    except Exception as e:
        print(f"✗ Error fetching {symbol}: {e}")
        raise


def calculate_metrics(df: pd.DataFrame) -> Dict:
    """Calculate market risk metrics from price data."""
    if df.empty or len(df) < 7:
        return {
            "price": 0.0,
            "return_7d": 0.0,
            "vol_ann": 0.0,
            "max_drawdown": 0.0
        }
    
    # Current price (last close)
    current_price = float(df['Close'].iloc[-1])
    
    # Daily return (change from previous day)
    if len(df) >= 2:
        previous_price = float(df['Close'].iloc[-2])
        daily_return = ((current_price - previous_price) / previous_price) * 100
    else:
        daily_return = 0.0
    
    # 7-day return (keep for other uses)
    if len(df) >= 7:
        price_7d_ago = float(df['Close'].iloc[-7])
        return_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
    else:
        return_7d = 0.0
    
    # Daily returns
    df['Returns'] = df['Close'].pct_change()
    daily_returns = df['Returns'].dropna()
    
    # Annualized volatility (252 trading days)
    if len(daily_returns) > 1:
        vol_ann = float(daily_returns.std() * np.sqrt(252) * 100)
    else:
        vol_ann = 0.0
    
    # Max drawdown
    df['Cumulative'] = (1 + daily_returns).cumprod()
    df['RunningMax'] = df['Cumulative'].expanding().max()
    df['Drawdown'] = (df['Cumulative'] - df['RunningMax']) / df['RunningMax']
    max_drawdown = float(df['Drawdown'].min() * 100)
    
    return {
        "price": current_price,
        "daily_return": daily_return,  # Daily percentage change
        "return_7d": return_7d,
        "vol_ann": vol_ann,
        "max_drawdown": max_drawdown
    }


def store_price_data(session: Session, symbol: str, df: pd.DataFrame):
    """Store price data in database."""
    for date, row in df.iterrows():
        existing = session.exec(
            select(PricePoint).where(
                PricePoint.symbol == symbol,
                PricePoint.date == date.to_pydatetime() if isinstance(date, pd.Timestamp) else date
            )
        ).first()
        
        if not existing:
            price_point = PricePoint(
                symbol=symbol,
                date=date.to_pydatetime() if isinstance(date, pd.Timestamp) else date,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=int(row['Volume']) if 'Volume' in row else 0
            )
            session.add(price_point)
    
    session.commit()


def store_metrics(session: Session, symbol: str, metrics: Dict):
    """Store calculated metrics."""
    snapshot = MetricsSnapshot(
        symbol=symbol,
        price=metrics["price"],
        return_7d=metrics["return_7d"],
        vol_ann=metrics["vol_ann"],
        max_drawdown=metrics["max_drawdown"]
    )
    session.add(snapshot)
    session.commit()
    return snapshot


def refresh_ticker_market_data(session: Session, symbol: str) -> Dict:
    """Refresh market data for a ticker."""
    import time
    try:
        print(f"\n{'='*50}")
        print(f"REFRESHING MARKET DATA FOR {symbol}")
        print(f"{'='*50}")
        
        df = fetch_price_data(symbol)
        if df.empty:
            error_msg = f"No data found for {symbol}"
            print(f"✗ ERROR: {error_msg}")
            return {"error": error_msg}
        
        print(f"Storing {len(df)} price data points for {symbol}...")
        store_price_data(session, symbol, df)
        
        print(f"Calculating metrics for {symbol}...")
        metrics = calculate_metrics(df)
        print(f"✓ Metrics calculated:")
        print(f"  Price: ${metrics['price']:.2f}")
        print(f"  7D Return: {metrics['return_7d']:.2f}%")
        print(f"  Volatility: {metrics['vol_ann']:.2f}%")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        
        snapshot = store_metrics(session, symbol, metrics)
        print(f"✓ Successfully stored metrics snapshot for {symbol}")
        print(f"{'='*50}\n")
        
        return {
            "success": True,
            "metrics": metrics,
            "snapshot": snapshot
        }
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        import traceback
        print(f"\n✗ ERROR in refresh_ticker_market_data for {symbol}: {error_msg}")
        print(f"Full traceback:")
        traceback.print_exc()
        if "429" in error_msg or "Too Many Requests" in error_msg or "rate limit" in error_msg.lower():
            return {"error": f"Rate limited. Wait 1-2 minutes and try again."}
        return {"error": error_msg if error_msg else "Unknown error occurred"}
