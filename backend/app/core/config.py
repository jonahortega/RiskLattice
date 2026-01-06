from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://risklattice:risklattice@postgres:5432/risklattice")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    alphavantage_api_key: Optional[str] = os.getenv("ALPHAVANTAGE_API_KEY")
    # Support multiple API keys (comma-separated) for more requests
    alphavantage_api_keys: str = os.getenv("ALPHAVANTAGE_API_KEYS", os.getenv("ALPHAVANTAGE_API_KEY", ""))
    refresh_interval_minutes: int = int(os.getenv("REFRESH_INTERVAL_MINUTES", "30"))
    market_weight: float = float(os.getenv("MARKET_WEIGHT", "0.6"))
    news_weight: float = float(os.getenv("NEWS_WEIGHT", "0.4"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

