#!/bin/bash

echo "=== 1. Checking Backend Logs for Crypto Errors ==="
cd /Users/jonahortega/risklattice
docker-compose logs backend --tail=100 | grep -i -E "(crypto|BTC|ETH|error|exception|failed|DIGITAL_CURRENCY)" | tail -30

echo ""
echo "=== 2. Testing BTC-USD Quote Endpoint ==="
curl -s "http://localhost:8000/api/market/quote/BTC-USD" | python3 -m json.tool 2>/dev/null || echo "Failed to parse JSON or endpoint error"

echo ""
echo "=== 3. Testing BTC-USD Risk Detail (this triggers data fetch) ==="
curl -s "http://localhost:8000/api/risk/BTC-USD" 2>&1 | head -100

echo ""
echo "=== 4. Testing Alpha Vantage Crypto Detection ==="
docker-compose exec -T backend python3 << 'EOF'
from app.services.alphavantage_data import is_crypto_symbol
print("BTC-USD is crypto:", is_crypto_symbol('BTC-USD'))
print("ETH-USD is crypto:", is_crypto_symbol('ETH-USD'))
print("AAPL is crypto:", is_crypto_symbol('AAPL'))
EOF

echo ""
echo "=== 5. Checking if Alpha Vantage API Key is Set ==="
docker-compose exec -T backend python3 << 'EOF'
from app.core.config import settings
if settings.alphavantage_api_key:
    print("✓ Alpha Vantage API key is set (length:", len(settings.alphavantage_api_key), ")")
else:
    print("✗ Alpha Vantage API key is NOT set")
EOF

echo ""
echo "=== 6. Testing Direct Alpha Vantage Crypto Fetch ==="
docker-compose exec -T backend python3 << 'EOF'
from app.services.alphavantage_data import fetch_price_data_alphavantage
try:
    print("Attempting to fetch BTC-USD...")
    df = fetch_price_data_alphavantage("BTC-USD", days=30)
    if not df.empty:
        print(f"✓ Success! Got {len(df)} rows")
        print(f"  Latest price: ${df['Close'].iloc[-1]:.2f}")
    else:
        print("✗ Got empty DataFrame")
except Exception as e:
    print(f"✗ Error: {e}")
EOF

