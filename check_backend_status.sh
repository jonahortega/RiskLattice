#!/bin/bash

echo "=== Backend Status Check ==="
echo ""

echo "1. Checking if backend container is running:"
docker-compose ps backend

echo ""
echo "2. Testing health endpoint:"
curl -s "http://localhost:8000/api/health" || echo "Health endpoint failed"

echo ""
echo "3. Testing stock quote endpoint (AAPL):"
curl -s "http://localhost:8000/api/market/quote/AAPL" | python3 -m json.tool 2>/dev/null || curl -s "http://localhost:8000/api/market/quote/AAPL"

echo ""
echo "4. Testing dashboard endpoint:"
curl -s "http://localhost:8000/api/dashboard" | python3 -m json.tool 2>/dev/null | head -20 || echo "Dashboard endpoint failed"

echo ""
echo "5. Checking backend logs for recent errors:"
docker-compose logs backend --tail=30 | grep -i -E "(error|exception|failed|traceback)" | tail -10

