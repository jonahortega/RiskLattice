#!/bin/bash

echo "=== Testing Network and yfinance ==="
echo ""

echo "1. Testing network connectivity from Docker:"
docker-compose exec -T backend python3 << 'EOF'
import requests
try:
    response = requests.get("https://finance.yahoo.com", timeout=5)
    print(f"   ✓ Can reach yahoo.com (status: {response.status_code})")
except Exception as e:
    print(f"   ✗ Cannot reach yahoo.com: {e}")
EOF

echo ""
echo "2. Testing yfinance with different methods:"
docker-compose exec -T backend python3 << 'EOF'
import yfinance as yf
import sys

# Try method 1: Direct download
print("Method 1: yf.download()")
try:
    data = yf.download("BTC-USD", period="5d", progress=False, interval="1d")
    if not data.empty:
        print(f"   ✓ Success! Rows: {len(data)}")
        print(f"   Price: ${data['Close'].iloc[-1]:.2f}")
    else:
        print("   ✗ Empty result")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Try method 2: Ticker object
print("\nMethod 2: yf.Ticker()")
try:
    ticker = yf.Ticker("BTC-USD")
    info = ticker.info
    print(f"   Info keys: {list(info.keys())[:5]}...")
    hist = ticker.history(period="5d")
    if not hist.empty:
        print(f"   ✓ Success! Rows: {len(hist)}")
        print(f"   Price: ${hist['Close'].iloc[-1]:.2f}")
    else:
        print("   ✗ Empty result")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Try method 3: Different symbol format
print("\nMethod 3: BTC=X (alternative format)")
try:
    ticker = yf.Ticker("BTC=X")
    hist = ticker.history(period="5d")
    if not hist.empty:
        print(f"   ✓ Success! Rows: {len(hist)}")
        print(f"   Price: ${hist['Close'].iloc[-1]:.2f}")
    else:
        print("   ✗ Empty result")
except Exception as e:
    print(f"   ✗ Error: {e}")
EOF

