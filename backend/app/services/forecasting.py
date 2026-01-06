"""
Risk Forecasting Service
Predicts future risk scores based on historical patterns, trends, and news momentum.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlmodel import Session, select
from app.models.models import RiskSnapshot, MetricsSnapshot, NewsArticle, RiskForecast
from app.services.risk_scoring import calculate_market_score, calculate_news_score
import json


def analyze_risk_trends(session: Session, symbol: str, days: int = 30) -> Dict:
    """
    Analyze historical risk trends to identify patterns.
    Returns trend direction, volatility of risk, and momentum.
    """
    # Get recent risk snapshots
    cutoff = datetime.utcnow() - timedelta(days=days)
    statement = select(RiskSnapshot).where(
        RiskSnapshot.symbol == symbol,
        RiskSnapshot.ts >= cutoff
    ).order_by(RiskSnapshot.ts)
    
    snapshots = session.exec(statement).all()
    
    if len(snapshots) < 7:
        return {
            "trend": "insufficient_data",
            "momentum": 0.0,
            "volatility": 0.0,
            "average_score": 50.0
        }
    
    scores = [s.total_score for s in snapshots]
    timestamps = [s.ts for s in snapshots]
    
    # Calculate trend (simple linear regression)
    x = np.arange(len(scores))
    coeffs = np.polyfit(x, scores, 1)
    slope = coeffs[0]  # Positive = increasing risk, Negative = decreasing
    
    # Calculate momentum (rate of change)
    if len(scores) >= 3:
        recent_change = scores[-1] - scores[-3]  # Change in last 3 data points
        momentum = recent_change / 3
    else:
        momentum = 0.0
    
    # Calculate volatility of risk scores
    risk_volatility = np.std(scores)
    
    # Determine trend direction
    if slope > 0.5:
        trend = "increasing"
    elif slope < -0.5:
        trend = "decreasing"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "momentum": momentum,
        "volatility": risk_volatility,
        "average_score": np.mean(scores),
        "slope": slope,
        "recent_scores": scores[-7:]  # Last 7 scores
    }


def predict_news_momentum(session: Session, symbol: str, days: int = 7) -> Dict:
    """
    Predict news sentiment continuation based on recent news trends.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    statement = select(NewsArticle).where(
        NewsArticle.symbol == symbol,
        NewsArticle.published_at >= cutoff
    ).order_by(NewsArticle.published_at)
    
    articles = session.exec(statement).all()
    
    if len(articles) == 0:
        return {
            "momentum": "neutral",
            "trend": "stable",
            "news_count": 0
        }
    
    # Analyze news volume trend (more news = potentially higher volatility)
    news_by_day = {}
    for article in articles:
        day = article.published_at.date()
        news_by_day[day] = news_by_day.get(day, 0) + 1
    
    news_counts = list(news_by_day.values())
    
    # If news volume is increasing, sentiment momentum might continue
    if len(news_counts) >= 3:
        recent_avg = np.mean(news_counts[-3:])
        earlier_avg = np.mean(news_counts[:-3]) if len(news_counts) > 3 else recent_avg
        volume_trend = "increasing" if recent_avg > earlier_avg * 1.2 else "decreasing"
    else:
        volume_trend = "stable"
    
    return {
        "momentum": volume_trend,
        "trend": "increasing" if len(news_counts) > 5 else "stable",
        "news_count": len(articles),
        "daily_average": np.mean(news_counts) if news_counts else 0
    }


def recognize_risk_patterns(session: Session, symbol: str) -> Optional[str]:
    """
    Match current risk patterns to historical patterns.
    Returns pattern name if match found.
    """
    # Get recent risk snapshots
    cutoff = datetime.utcnow() - timedelta(days=14)
    statement = select(RiskSnapshot).where(
        RiskSnapshot.symbol == symbol,
        RiskSnapshot.ts >= cutoff
    ).order_by(RiskSnapshot.ts)
    
    snapshots = session.exec(statement).all()
    
    if len(snapshots) < 7:
        return None
    
    scores = [s.total_score for s in snapshots[-7:]]
    current_score = scores[-1]
    
    # Pattern 1: Spike Pattern (sudden increase)
    if len(scores) >= 3:
        recent_change = scores[-1] - scores[-3]
        if recent_change > 15:  # 15+ point increase in 3 days
            return "risk_spike"
    
    # Pattern 2: Volatility Surge (high volatility + high score)
    if np.std(scores) > 10 and current_score > 65:
        return "high_volatility"
    
    # Pattern 3: Stable High Risk (consistently high)
    if np.mean(scores) > 70 and np.std(scores) < 5:
        return "sustained_high_risk"
    
    # Pattern 4: Rapid Decline (risk dropping fast)
    if len(scores) >= 3:
        recent_change = scores[-1] - scores[-3]
        if recent_change < -15:  # 15+ point decrease
            return "risk_declining"
    
    return None


def generate_risk_forecast(
    session: Session, 
    symbol: str, 
    current_score: float,
    days_ahead: int = 7
) -> Dict:
    """
    Generate risk forecast for next N days.
    Returns predicted score, confidence, and reasoning.
    """
    # Analyze trends
    trends = analyze_risk_trends(session, symbol, days=30)
    news_momentum = predict_news_momentum(session, symbol, days=7)
    pattern = recognize_risk_patterns(session, symbol)
    
    # Base prediction on current score
    predicted_score = current_score
    
    # Adjust based on trend momentum
    if trends["trend"] == "increasing":
        predicted_score += trends["momentum"] * days_ahead
        trend_direction = "increasing"
    elif trends["trend"] == "decreasing":
        predicted_score += trends["momentum"] * days_ahead
        trend_direction = "decreasing"
    else:
        trend_direction = "stable"
    
    # Adjust based on news momentum
    if news_momentum["momentum"] == "increasing":
        predicted_score += 3  # Moderate increase due to news volume
    elif news_momentum["momentum"] == "decreasing":
        predicted_score -= 2  # Slight decrease
    
    # Adjust based on recognized patterns
    pattern_adjustment = 0
    if pattern == "risk_spike":
        pattern_adjustment = 5  # Spike patterns often continue
        predicted_score += 5
    elif pattern == "high_volatility":
        pattern_adjustment = 3
        predicted_score += 3
    elif pattern == "sustained_high_risk":
        pattern_adjustment = 0  # Maintains high level
    elif pattern == "risk_declining":
        pattern_adjustment = -3
        predicted_score -= 3
    
    # Clamp to valid range
    predicted_score = max(0, min(100, predicted_score))
    
    # Calculate confidence based on data quality
    confidence_factors = []
    if len(snapshots := session.exec(select(RiskSnapshot).where(RiskSnapshot.symbol == symbol)).all()) >= 7:
        confidence_factors.append(0.3)  # Good historical data
    if news_momentum["news_count"] > 0:
        confidence_factors.append(0.2)  # News data available
    if pattern:
        confidence_factors.append(0.2)  # Pattern matched
    if trends["volatility"] < 5:
        confidence_factors.append(0.3)  # Stable patterns = higher confidence
    
    confidence = sum(confidence_factors) if confidence_factors else 0.5
    
    # Generate forecast reasons
    reasons = []
    if trends["trend"] != "stable":
        reasons.append(f"Risk trend is {trends['trend']} (momentum: {trends['momentum']:.1f} points/day)")
    if news_momentum["momentum"] != "stable":
        reasons.append(f"News volume is {news_momentum['momentum']} ({news_momentum['news_count']} articles)")
    if pattern:
        reasons.append(f"Pattern detected: {pattern.replace('_', ' ').title()}")
    if trends["volatility"] > 10:
        reasons.append("High risk volatility detected")
    
    if not reasons:
        reasons.append("Based on current risk level and historical patterns")
    
    return {
        "predicted_score": round(predicted_score, 1),
        "confidence": round(confidence, 2),
        "trend_direction": trend_direction,
        "reasons": reasons,
        "pattern_match": pattern,
        "forecast_days": days_ahead,
        "current_score": current_score,
        "projected_change": round(predicted_score - current_score, 1)
    }


def store_forecast(session: Session, symbol: str, forecast: Dict) -> RiskForecast:
    """Store forecast in database."""
    forecast_obj = RiskForecast(
        symbol=symbol,
        forecast_date=datetime.utcnow(),
        days_ahead=forecast["forecast_days"],
        predicted_score=forecast["predicted_score"],
        confidence=forecast["confidence"],
        trend_direction=forecast["trend_direction"],
        forecast_reasons=json.dumps(forecast["reasons"]),
        pattern_match=forecast.get("pattern_match")
    )
    session.add(forecast_obj)
    session.commit()
    session.refresh(forecast_obj)
    return forecast_obj

