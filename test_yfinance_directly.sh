#!/bin/bash

echo "=== Direct yfinance Test ==="
echo ""

docker-compose exec -T backend python3 << 'EOF'
import sys
import traceback

try:
    print("1. Testing yfinance import...")
    import yfinance as yf
    print("   ✓ yfinance imported successfully")
    
    print("\n2. Testing BTC-USD fetch...")
    ticker = yf.Ticker("BTC-USD")
    hist = ticker.history(period="5d")
    
    print(f"   DataFrame shape: {hist.shape}")
    print(f"   Columns: {list(hist.columns)}")
    print(f"   Index type: {type(hist.index)}")
    
    if not hist.empty:
        print(f"   ✓ Success! Rows: {len(hist)}")
        print(f"   Latest price: ${hist['Close'].iloc[-1]:.2f}")
        print(f"   First few rows:")
        print(hist.head())
    else:
        print("   ✗ Empty DataFrame returned")
        
    print("\n3. Testing our fetch_price_data function...")
    from app.services.market_data import fetch_price_data
    df = fetch_price_data("BTC-USD", days=30)
    
    if not df.empty:
        print(f"   ✓ Success! Rows: {len(df)}")
        print(f"   Latest price: ${df['Close'].iloc[-1]:.2f}")
        print(f"   Columns: {list(df.columns)}")
    else:
        print("   ✗ Empty DataFrame")
        
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
EOF

