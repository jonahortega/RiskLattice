#!/usr/bin/env python3
"""Test yfinance connectivity"""
import sys
try:
    import yfinance as yf
    print("Testing yfinance download method...")
    
    # Test 1: Using download
    print("\n1. Testing yf.download()...")
    df = yf.download("AAPL", period="5d", progress=False)
    print(f"   Result: {len(df)} rows")
    if not df.empty:
        print(f"   Latest price: ${df['Close'].iloc[-1]:.2f}")
    
    # Test 2: Using Ticker
    print("\n2. Testing yf.Ticker()...")
    ticker = yf.Ticker("AAPL")
    hist = ticker.history(period="5d")
    print(f"   Result: {len(hist)} rows")
    if not hist.empty:
        print(f"   Latest price: ${hist['Close'].iloc[-1]:.2f}")
    
    print("\n✓ Tests completed!")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

