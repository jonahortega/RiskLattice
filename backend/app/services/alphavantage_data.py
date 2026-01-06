import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict
from app.core.config import settings


def is_crypto_symbol(symbol: str) -> bool:
    """Check if symbol is a cryptocurrency."""
    symbol_upper = symbol.upper()
    # Check for crypto indicators
    crypto_indicators = ['-USD', '-EUR', '-BTC', '-ETH']
    if any(indicator in symbol_upper for indicator in crypto_indicators):
        return True
    
    # Common crypto symbols
    common_crypto = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'DOT', 'DOGE', 'MATIC', 
                     'LTC', 'AVAX', 'UNI', 'ATOM', 'LINK', 'ETC', 'XLM', 'ALGO', 'VET',
                     'FIL', 'TRX', 'EOS', 'AAVE', 'AXS', 'SAND', 'MANA', 'ENJ', 'CHZ',
                     'BAT', 'ZEC', 'XTZ', 'THETA', 'HOT', 'ZEC', 'DASH']
    
    # Extract base symbol (remove currency pair suffix)
    base_symbol = symbol_upper.split('-')[0] if '-' in symbol_upper else symbol_upper
    return base_symbol in common_crypto


def fetch_price_data_with_yfinance(symbol: str, days: int = 90) -> pd.DataFrame:
    """Fetch price data using yfinance (works for both stocks and crypto)."""
    try:
        import yfinance as yf
        from datetime import datetime, timedelta
        import time
        
        print(f"Fetching {symbol} using yfinance...")
        
        # Try different symbol formats for crypto if needed
        symbol_variants = [symbol]
        if '-' in symbol and symbol.endswith('-USD'):
            # Try without -USD suffix and with =X suffix (Yahoo Finance format)
            base = symbol.replace('-USD', '')
            symbol_variants.append(f"{base}-USD")
            symbol_variants.append(f"{base}=X")
        
        hist = None
        used_symbol = None
        
        for variant in symbol_variants:
            try:
                print(f"  Trying symbol format: {variant}")
                ticker = yf.Ticker(variant)
                
                # Try with a small delay to avoid rate limits
                time.sleep(0.5)
                
                # Try multiple periods - start with shorter ones
                for period in ["5d", "1mo", "3mo", "6mo", "1y"]:
                    try:
                        print(f"    Trying period: {period}")
                        hist = ticker.history(period=period, interval='1d')
                        if not hist.empty:
                            used_symbol = variant
                            print(f"    ✓ Got data with {variant} using period {period}")
                            break
                        time.sleep(0.3)  # Small delay between attempts
                    except Exception as period_error:
                        print(f"    ✗ Period {period} failed: {period_error}")
                        continue
                
                if hist is not None and not hist.empty:
                    break
                    
            except Exception as variant_error:
                print(f"  ✗ Symbol format {variant} failed: {variant_error}")
                continue
        
        if hist is None or hist.empty:
            print(f"✗ No data returned from yfinance for {symbol} (tried variants: {symbol_variants})")
            return pd.DataFrame()
        
        # yfinance returns a DataFrame with DatetimeIndex and columns: Open, High, Low, Close, Volume, etc.
        # Just use the columns we need directly - the index is already a DatetimeIndex
        df = hist[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        
        # Ensure index is DatetimeIndex (it should be already, but just in case)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Filter to last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df.index >= cutoff_date]
        
        if df.empty:
            print(f"⚠ No data after filtering to last {days} days for {symbol}")
            return pd.DataFrame()
        
        print(f"✓ Successfully fetched {len(df)} rows for {symbol} using yfinance (symbol: {used_symbol})")
        print(f"  Latest price: ${df['Close'].iloc[-1]:.2f}")
        print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")
        
        return df
        
    except ImportError:
        print("✗ yfinance not installed. Install with: pip install yfinance")
        raise
    except Exception as e:
        print(f"✗ Error fetching {symbol} with yfinance: {e}")
        import traceback
        traceback.print_exc()
        raise


def fetch_price_data_alphavantage(symbol: str, days: int = 90) -> pd.DataFrame:
    """Fetch price history using Alpha Vantage API. Handles both stocks and crypto."""
    
    api_key = settings.alphavantage_api_key
    if not api_key:
        raise ValueError("ALPHAVANTAGE_API_KEY not set in environment variables")
    
    # Alpha Vantage API endpoint
    url = "https://www.alphavantage.co/query"
    
    # Determine if this is crypto
    is_crypto = is_crypto_symbol(symbol)
    
    if is_crypto:
        # For crypto, use DIGITAL_CURRENCY_DAILY
        # Format: BTC, ETH, etc. (extract base symbol)
        base_symbol = symbol.upper().split('-')[0] if '-' in symbol.upper() else symbol.upper()
        market = 'USD'  # Default market
        
        # Extract market from symbol if present (e.g., BTC-USD -> BTC, USD)
        if '-' in symbol.upper():
            parts = symbol.upper().split('-')
            if len(parts) == 2:
                base_symbol = parts[0]
                market = parts[1]
        
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": base_symbol,
            "market": market,
            "apikey": api_key
        }
        time_series_key = f"Time Series (Digital Currency Daily)"
        print(f"Fetching crypto {base_symbol} in {market} from Alpha Vantage...")
    else:
        # For stocks, use TIME_SERIES_DAILY
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol.upper(),
            "apikey": api_key,
            "outputsize": "compact"  # Free tier: last 100 data points
        }
        time_series_key = "Time Series (Daily)"
        print(f"Fetching stock {symbol} from Alpha Vantage...")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Debug: print response keys to see what we got
        print(f"Response keys: {list(data.keys())}")
        
        # Check for API errors
        if "Error Message" in data:
            error_msg = data["Error Message"]
            print(f"✗ Alpha Vantage API error: {error_msg}")
            raise ValueError(f"Alpha Vantage API error: {error_msg}")
        
        if "Note" in data:
            # Rate limit message
            note_msg = data["Note"]
            print(f"⚠ Alpha Vantage note: {note_msg}")
            raise ValueError(f"Alpha Vantage rate limit reached: {note_msg}")
        
        if "Information" in data:
            # Sometimes API returns information messages
            info_msg = data["Information"]
            print(f"⚠ Alpha Vantage info: {info_msg}")
            if "API call frequency" in info_msg or "rate" in info_msg.lower():
                raise ValueError(f"Rate limit: {info_msg}")
        
        # Extract time series data
        if time_series_key not in data:
            # Print what we actually got for debugging
            print(f"✗ No time series data in response for {symbol}")
            print(f"   Response contains: {list(data.keys())}")
            if "Meta Data" in data:
                print(f"   Meta Data: {data['Meta Data']}")
            return pd.DataFrame()
        
        time_series = data[time_series_key]
        
        # Convert to DataFrame
        df_data = []
        if is_crypto:
            # DIGITAL_CURRENCY_DAILY has: 1a. open (USD), 1b. open (crypto), 2a. high (USD), etc.
            # Note: Field names might vary, try different formats
            for date_str, values in time_series.items():
                try:
                    # Try different field name formats
                    open_key = f"1a. open ({market})"
                    high_key = f"2a. high ({market})"
                    low_key = f"3a. low ({market})"
                    close_key = f"4a. close ({market})"
                    
                    # If those don't work, try without market suffix
                    if open_key not in values:
                        open_key = "1a. open (USD)"
                        high_key = "2a. high (USD)"
                        low_key = "3a. low (USD)"
                        close_key = "4a. close (USD)"
                    
                    df_data.append({
                        "Date": pd.to_datetime(date_str),
                        "Open": float(values[open_key]),
                        "High": float(values[high_key]),
                        "Low": float(values[low_key]),
                        "Close": float(values[close_key]),
                        "Volume": int(float(values.get("5. volume", 0)))  # Volume is usually in crypto units
                    })
                except KeyError as e:
                    print(f"⚠ Warning: Missing field {e} in crypto data, skipping date {date_str}")
                    continue
        else:
            # TIME_SERIES_DAILY has: 1. open, 2. high, 3. low, 4. close, 5. volume
            for date_str, values in time_series.items():
                df_data.append({
                    "Date": pd.to_datetime(date_str),
                    "Open": float(values["1. open"]),
                    "High": float(values["2. high"]),
                    "Low": float(values["3. low"]),
                    "Close": float(values["4. close"]),
                    "Volume": int(values["5. volume"])
                })
        
        df = pd.DataFrame(df_data)
        df = df.sort_values("Date")
        df = df.set_index("Date")
        
        # Filter to last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        df = df[df.index >= cutoff_date]
        
        print(f"✓ Successfully fetched {len(df)} rows for {symbol}")
        print(f"  Latest price: ${df['Close'].iloc[-1]:.2f}")
        print(f"  Date range: {df.index[0].date()} to {df.index[-1].date()}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Network error fetching {symbol}: {e}")
        raise
    except Exception as e:
        print(f"✗ Error fetching {symbol}: {e}")
        raise

