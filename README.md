# RiskLattice - AI Financial Risk Intelligence

A production-grade MVP for monitoring stock tickers and generating AI-powered risk scores. RiskLattice combines market data analysis with news sentiment analysis to provide comprehensive risk intelligence.

## Architecture

RiskLattice is built as a monorepo with:

- **Backend**: FastAPI + PostgreSQL + SQLModel + Alembic
- **Frontend**: React (Vite) + TypeScript + Tailwind CSS
- **Background Scheduler**: APScheduler for automatic data refresh
- **AI Layer**: OpenAI GPT-3.5 (with VADER sentiment fallback)
- **Data Sources**: yfinance (market data), Google News RSS (news)

## Features

- **Watchlist Management**: Add/remove stock tickers
- **Market Risk Analysis**: 90-day price history, volatility, drawdown, returns
- **News Sentiment Analysis**: AI-powered sentiment and risk theme extraction
- **Risk Scoring**: Composite score (0-100) combining market and news factors
- **Real-time Dashboard**: View all tickers at a glance with risk scores and trends
- **Detail Views**: Deep dive into individual tickers with charts and explanations
- **Auto-refresh**: Background scheduler updates data every 30 minutes

## Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) OpenAI API key for enhanced AI analysis

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd risklattice
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file (optional):**
   ```env
   DATABASE_URL=postgresql://risklattice:risklattice@postgres:5432/risklattice
   OPENAI_API_KEY=your_key_here  # Optional - uses fallback if not provided
   REFRESH_INTERVAL_MINUTES=30
   MARKET_WEIGHT=0.6
   NEWS_WEIGHT=0.4
   ```

4. **Start all services:**
   ```bash
   docker-compose up --build
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## How Risk Scoring Works

### Market Score (0-100)
Calculated from:
- **Volatility** (40% weight): Annualized volatility from daily returns
- **Max Drawdown** (40% weight): Largest peak-to-trough decline
- **7-Day Return** (20% weight): Recent performance indicator

Higher volatility, larger drawdowns, and negative returns increase the market risk score.

### News Score (0-100)
Calculated from:
- **Sentiment** (base score): AI-analyzed sentiment from recent headlines (-1 to 1, inverted to 0-100)
- **Risk Themes** (penalty): Additional points for identified risk themes (lawsuit, regulation, etc.)

### Total Risk Score
Weighted average: `(Market Score × MARKET_WEIGHT) + (News Score × NEWS_WEIGHT)`

Default weights: 60% market, 40% news (configurable via environment variables).

## API Endpoints

### Health & Status
- `GET /api/health` - Health check

### Ticker Management
- `GET /api/tickers` - List all tickers in watchlist
- `POST /api/tickers` - Add a ticker (body: `{"symbol": "AAPL"}`)
- `DELETE /api/tickers/{symbol}` - Remove a ticker

### Data & Analysis
- `GET /api/dashboard` - Get dashboard summary for all tickers
- `GET /api/risk/{symbol}` - Get detailed risk analysis for a ticker
- `POST /api/refresh` - Manually refresh all tickers
- `POST /api/refresh/{symbol}` - Manually refresh a specific ticker

### Example cURL Commands

```bash
# Add a ticker
curl -X POST http://localhost:8000/api/tickers \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'

# Get dashboard
curl http://localhost:8000/api/dashboard

# Get risk detail for AAPL
curl http://localhost:8000/api/risk/AAPL

# Refresh all tickers
curl -X POST http://localhost:8000/api/refresh

# Remove a ticker
curl -X DELETE http://localhost:8000/api/tickers/AAPL
```

## Configuration

### Risk Scoring Weights

Edit `.env` file or docker-compose environment variables:

- `MARKET_WEIGHT`: Weight for market risk (default: 0.6)
- `NEWS_WEIGHT`: Weight for news risk (default: 0.4)

**Note**: Weights should sum to 1.0 for proper normalization.

### AI Mode

- **LLM Mode** (default if `OPENAI_API_KEY` is set): Uses GPT-3.5-turbo for advanced sentiment analysis and theme extraction
- **Fallback Mode** (if no API key): Uses VADER sentiment analysis with keyword-based theme detection

To switch modes, simply add or remove the `OPENAI_API_KEY` from your `.env` file and restart the backend.

### Refresh Interval

Set `REFRESH_INTERVAL_MINUTES` in `.env` (default: 30 minutes). The background scheduler will automatically refresh all tickers at this interval.

## Project Structure

```
risklattice/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes and schemas
│   │   ├── core/         # Config and database
│   │   ├── models/       # SQLModel database models
│   │   └── services/     # Business logic (market, news, AI, risk)
│   ├── alembic/          # Database migrations
│   ├── main.py           # FastAPI application
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/        # Dashboard and TickerDetail pages
│   │   ├── api/          # API client
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Database Models

- **Ticker**: Watchlist tickers
- **PricePoint**: Historical price data (90 days)
- **MetricsSnapshot**: Calculated market metrics
- **NewsArticle**: Fetched news articles
- **AISnapshot**: AI analysis results
- **RiskSnapshot**: Risk scores over time

## Troubleshooting

### Docker Issues

**Port already in use:**
```bash
# Check what's using the port
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL

# Stop conflicting services or change ports in docker-compose.yml
```

**Database connection errors:**
- Ensure PostgreSQL container is healthy: `docker-compose ps`
- Check database logs: `docker-compose logs postgres`
- Verify `DATABASE_URL` in `.env` matches docker-compose settings

**Build failures:**
```bash
# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Backend Issues

**Import errors:**
- Ensure all dependencies are installed: `pip install -r backend/requirements.txt`
- Check Python version (requires 3.11+)

**Scheduler not running:**
- Check backend logs: `docker-compose logs backend`
- Verify `REFRESH_INTERVAL_MINUTES` is set correctly

### Frontend Issues

**API connection errors:**
- Verify `VITE_API_URL` in frontend environment or docker-compose
- Check CORS settings in `backend/main.py`
- Ensure backend is running: `curl http://localhost:8000/api/health`

**Build errors:**
- Clear node_modules: `rm -rf frontend/node_modules && npm install`
- Check Node version (requires 18+)

### Data Issues

**No data for ticker:**
- Verify ticker symbol is valid (e.g., "AAPL" not "apple")
- Check yfinance is working: `python -c "import yfinance; print(yfinance.Ticker('AAPL').info['symbol'])"`
- Check backend logs for fetch errors

**News not loading:**
- Google News RSS may be rate-limited
- Check network connectivity in container
- Verify news service logs: `docker-compose logs backend | grep news`

## Development

### Running Locally (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Database:**
```bash
# Requires PostgreSQL running locally
# Update DATABASE_URL in backend/.env
```

### Running Migrations

```bash
# Inside backend container
docker-compose exec backend alembic upgrade head

# Or locally
cd backend
alembic upgrade head
```

## License

MIT

## Support

For issues or questions, check the troubleshooting section above or review the logs:
```bash
docker-compose logs backend
docker-compose logs frontend
```

