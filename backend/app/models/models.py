from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import Text
from datetime import datetime
from typing import Optional, List


class User(SQLModel, table=True):
    """User model - uses session_id for anonymous users, can add email/password later."""
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(unique=True, index=True)  # Unique session identifier from frontend
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_guest: bool = Field(default=True)  # True for anonymous sessions, False for registered users
    email: Optional[str] = Field(default=None, unique=True, index=True)  # For future account linking
    # Relationship to tickers
    tickers: List["Ticker"] = Relationship(back_populates="user")


class Ticker(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    user_id: int = Field(foreign_key="user.id", index=True)  # Link to user
    created_at: datetime = Field(default_factory=datetime.utcnow)
    risk_tolerance: Optional[str] = Field(default="moderate")  # conservative, moderate, aggressive
    # Relationship back to user
    user: Optional[User] = Relationship(back_populates="tickers")


class PricePoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    date: datetime = Field(index=True)
    open: float
    high: float
    low: float
    close: float
    volume: int


class MetricsSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    price: float
    return_7d: float
    vol_ann: float
    max_drawdown: float


class NewsArticle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    title: str
    url: str
    published_at: datetime = Field(index=True)
    source: str


class AISnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    sentiment: float
    themes_json: str  # JSON string of themes list
    summary: str = Field(sa_column=Column(Text))  # Active market summary
    raw_json: str = Field(sa_column=Column(Text))  # Full AI response JSON


class RiskSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    market_score: float
    news_score: float
    total_score: float
    reasons_json: str = Field(sa_column=Column(Text))  # JSON string of reasons list
    trend: Optional[str] = Field(default=None, sa_column=Column(Text))  # "up", "down", "flat", "new"


class RiskForecast(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    forecast_date: datetime = Field(default_factory=datetime.utcnow, index=True)
    days_ahead: int  # 1, 3, 7 days forecast
    predicted_score: float
    confidence: float  # 0-1 confidence level
    trend_direction: str  # "increasing", "decreasing", "stable"
    forecast_reasons: str = Field(sa_column=Column(Text))  # JSON string
    pattern_match: Optional[str] = None  # Matched historical pattern

