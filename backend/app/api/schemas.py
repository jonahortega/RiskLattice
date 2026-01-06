from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class TickerCreate(BaseModel):
    symbol: str


class DashboardRow(BaseModel):
    ticker: str
    price: float
    return_7d: float
    volatility: float
    max_drawdown: float
    risk_score: float
    trend: str
    last_updated: datetime


class RiskDetail(BaseModel):
    symbol: str
    current_price: float
    market_score: float
    news_score: float
    total_score: float
    trend: str
    reasons: List[str]
    ai_summary: str
    themes: List[str]
    market_outlook: Optional[str] = None  # POSITIVE, NEGATIVE, NEUTRAL
    metrics: Dict
    price_history: List[Dict]
    risk_history: List[Dict]
    recent_news: List[Dict]


class MessageResponse(BaseModel):
    message: str


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    message: str
    conversation_history: List[ChatMessage]

