# Quick test script to verify yfinance works
import yfinance as yf
import time

print("Testing yfinance...")
ticker = yf.Ticker("AAPL")
print(f"Fetching history with period='3mo'...")
try:
    hist = ticker.history(period="3mo", timeout=30)
    print(f"Success! Got {len(hist)} rows")
    if not hist.empty:
        print(f"Latest price: ${hist['Close'].iloc[-1]:.2f}")
        print(f"Date range: {hist.index[0]} to {hist.index[-1]}")
    else:
        print("ERROR: History is empty!")
except Exception as e:
    print(f"ERROR: {e}")

