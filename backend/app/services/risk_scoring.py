import json
from typing import Dict, List
from sqlmodel import Session, select, desc
from app.models.models import MetricsSnapshot, RiskSnapshot, AISnapshot
from app.core.config import settings


def calculate_market_score(metrics: Dict) -> float:
    """Calculate market risk score (0-100, higher = more risk)."""
    # Normalize metrics to 0-100 scale
    # Higher volatility = higher risk
    vol_score = min(100, max(0, metrics.get("vol_ann", 0) / 50 * 100))  # 50% vol = 100 score
    
    # More negative drawdown = higher risk
    drawdown_score = min(100, max(0, abs(metrics.get("max_drawdown", 0)) / 30 * 100))  # -30% = 100 score
    
    # Negative returns = higher risk
    return_score = 0
    return_7d = metrics.get("return_7d", 0)
    if return_7d < 0:
        return_score = min(100, abs(return_7d) / 10 * 100)  # -10% = 100 score
    
    # Weighted average
    market_score = (vol_score * 0.4 + drawdown_score * 0.4 + return_score * 0.2)
    return round(market_score, 2)


def calculate_news_score(ai_data: Dict) -> float:
    """Calculate news risk score (0-100, higher = more risk)."""
    sentiment = ai_data.get("sentiment", 0)
    # Negative sentiment = higher risk
    # Convert -1 to 1 scale to 0-100 (inverted: -1 = 100, 1 = 0)
    base_score = ((1 - sentiment) / 2) * 100
    
    # Add penalty for risk themes
    themes = ai_data.get("themes", [])
    theme_penalty = len(themes) * 5  # 5 points per risk theme
    
    news_score = min(100, base_score + theme_penalty)
    return round(news_score, 2)


def calculate_total_score(market_score: float, news_score: float) -> float:
    """Calculate total risk score using configured weights."""
    total = (market_score * settings.market_weight) + (news_score * settings.news_weight)
    return round(total, 2)


def generate_reasons(metrics: Dict, ai_data: Dict, market_score: float, news_score: float) -> List[str]:
    """Generate explainability reasons for the risk score."""
    reasons = []
    
    # Market reasons
    if metrics.get("vol_ann", 0) > 30:
        reasons.append(f"Volatility elevated at {metrics.get('vol_ann', 0):.1f}% (annualized)")
    if metrics.get("max_drawdown", 0) < -15:
        reasons.append(f"Significant drawdown: {metrics.get('max_drawdown', 0):.1f}%")
    if metrics.get("return_7d", 0) < -5:
        reasons.append(f"7-day return negative: {metrics.get('return_7d', 0):.1f}%")
    
    # News reasons
    sentiment = ai_data.get("sentiment", 0)
    if sentiment < -0.3:
        reasons.append("News sentiment strongly negative")
    elif sentiment < 0:
        reasons.append("News sentiment negative")
    
    themes = ai_data.get("themes", [])
    if themes:
        reasons.append(f"Risk themes identified: {', '.join(themes[:3])}")
    
    # Add market outlook from AI analysis
    market_outlook = ai_data.get("market_outlook", "NEUTRAL")
    if market_outlook == "NEGATIVE":
        reasons.append("Market outlook: NEGATIVE (news + price movement indicate bearish conditions)")
    elif market_outlook == "POSITIVE":
        reasons.append("Market outlook: POSITIVE (news + price movement indicate bullish conditions)")
    
    if not reasons:
        reasons.append("Risk levels within normal range")
    
    return reasons


def get_trend(session: Session, symbol: str, current_score: float) -> str:
    """Compare current score to previous to determine trend."""
    statement = select(RiskSnapshot).where(
        RiskSnapshot.symbol == symbol
    ).order_by(desc(RiskSnapshot.ts)).limit(2)
    
    snapshots = list(session.exec(statement))
    
    if len(snapshots) < 2:
        return "new"
    
    previous_score = snapshots[1].total_score
    diff = current_score - previous_score
    
    if diff > 5:
        return "up"
    elif diff < -5:
        return "down"
    else:
        return "flat"


def calculate_risk_score(session: Session, symbol: str, metrics: Dict, ai_data: Dict, snapshot_date=None) -> Dict:
    """Calculate and store risk score for a ticker."""
    from datetime import datetime
    market_score = calculate_market_score(metrics)
    news_score = calculate_news_score(ai_data)
    total_score = calculate_total_score(market_score, news_score)
    reasons = generate_reasons(metrics, ai_data, market_score, news_score)
    trend = get_trend(session, symbol, total_score)
    
    # Store risk snapshot
    risk_snapshot = RiskSnapshot(
        symbol=symbol,
        market_score=market_score,
        news_score=news_score,
        total_score=total_score,
        reasons_json=json.dumps(reasons),
        trend=trend,
        ts=snapshot_date if snapshot_date else datetime.utcnow()
    )
    session.add(risk_snapshot)
    session.commit()
    
    return {
        "market_score": market_score,
        "news_score": news_score,
        "total_score": total_score,
        "reasons": reasons,
        "trend": trend,
        "snapshot": risk_snapshot
    }

