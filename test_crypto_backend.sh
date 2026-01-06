#!/bin/bash

echo "=== Testing Crypto Backend ==="
echo ""

echo "1. Testing if yfinance can fetch BTC-USD:"
docker-compose exec -T backend python3 << 'EOF'
try:
    import yfinance as yf
    print("✓ yfinance is installed")
    
    ticker = yf.Ticker("BTC-USD")
    hist = ticker.history(period="5d")
    
    if not hist.empty:
        print(f"✓ Successfully fetched BTC-USD")
        print(f"  Latest price: ${hist['Close'].iloc[-1]:.2f}")
        print(f"  Rows: {len(hist)}")
    else:
        print("✗ No data returned")
except ImportError:
    print("✗ yfinance not installed")
except Exception as e:
    print(f"✗ Error: {e}")
EOF

echo ""
echo "2. Testing backend crypto detection:"
docker-compose exec -T backend python3 << 'EOF'
from app.services.alphavantage_data import is_crypto_symbol
from app.services.market_data import fetch_price_data

symbols = ['BTC-USD', 'ETH-USD', 'AAPL']
for sym in symbols:
    is_crypto = is_crypto_symbol(sym)
    print(f"{sym}: is_crypto={is_crypto}")
    
    if is_crypto:
        try:
            print(f"  Attempting to fetch {sym}...")
            df = fetch_price_data(sym, days=30)
            if not df.empty:
                print(f"  ✓ Success! Price: ${df['Close'].iloc[-1]:.2f}, Rows: {len(df)}")
            else:
                print(f"  ✗ Empty DataFrame")
        except Exception as e:
            print(f"  ✗ Error: {e}")
EOF

echo ""
echo "3. Testing API endpoint:"
curl -s "http://localhost:8000/api/risk/BTC-USD" 2>&1 | head -20

