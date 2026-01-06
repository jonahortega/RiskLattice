"""
Smart Recommendations Engine
Generates actionable recommendations based on risk forecasts and user preferences.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.models.models import RiskSnapshot, MetricsSnapshot, Ticker
from app.services.forecasting import generate_risk_forecast


def get_current_price(session: Session, symbol: str) -> Optional[float]:
    """Get current price for a ticker."""
    statement = select(MetricsSnapshot).where(
        MetricsSnapshot.symbol == symbol
    ).order_by(MetricsSnapshot.timestamp.desc())
    
    snapshot = session.exec(statement).first()
    return snapshot.price if snapshot else None


def get_latest_risk_score(session: Session, symbol: str) -> Optional[float]:
    """Get latest risk score."""
    statement = select(RiskSnapshot).where(
        RiskSnapshot.symbol == symbol
    ).order_by(RiskSnapshot.timestamp.desc())
    
    snapshot = session.exec(statement).first()
    return snapshot.total_score if snapshot else None


def calculate_position_size_recommendation(
    current_risk: float,
    forecasted_risk: float,
    user_tolerance: str = "moderate"
) -> Dict:
    """
    Recommend position size adjustments based on risk.
    Returns recommendation with reasoning.
    """
    # Risk tolerance thresholds
    tolerance_thresholds = {
        "conservative": 40,
        "moderate": 60,
        "aggressive": 75
    }
    
    threshold = tolerance_thresholds.get(user_tolerance, 60)
    
    recommendations = []
    action = "hold"
    adjustment_pct = 0
    
    # If forecasted risk exceeds tolerance
    if forecasted_risk > threshold + 10:
        action = "reduce"
        adjustment_pct = min(50, (forecasted_risk - threshold) / 2)  # 5% per point over threshold
        recommendations.append({
            "type": "position_size",
            "priority": "high",
            "action": f"Reduce position by {adjustment_pct:.0f}%",
            "reason": f"Forecasted risk ({forecasted_risk:.0f}) significantly exceeds your tolerance threshold ({threshold})"
        })
    elif forecasted_risk > threshold:
        action = "reduce"
        adjustment_pct = 20
        recommendations.append({
            "type": "position_size",
            "priority": "medium",
            "action": f"Consider reducing position by 20-30%",
            "reason": f"Forecasted risk ({forecasted_risk:.0f}) exceeds your tolerance threshold ({threshold})"
        })
    elif forecasted_risk < threshold - 15 and current_risk < threshold:
        action = "increase"
        recommendations.append({
            "type": "position_size",
            "priority": "low",
            "action": "Risk levels are well below tolerance - position size is appropriate",
            "reason": f"Current and forecasted risk are below threshold - no adjustment needed"
        })
    else:
        recommendations.append({
            "type": "position_size",
            "priority": "low",
            "action": "Hold current position size",
            "reason": f"Risk levels are within acceptable range"
        })
    
    return {
        "recommendations": recommendations,
        "action": action,
        "adjustment_percentage": adjustment_pct
    }


def calculate_stop_loss_recommendation(
    current_price: float,
    current_risk: float,
    forecasted_risk: float
) -> Optional[Dict]:
    """
    Recommend stop-loss price based on risk level.
    """
    if not current_price or current_price <= 0:
        return None
    
    # Higher risk = tighter stop loss
    # Conservative: 5% for high risk, 8% for moderate
    # Aggressive: 7% for high risk, 10% for moderate
    
    if forecasted_risk >= 70:
        stop_loss_pct = 5.0  # Tight stop for high risk
    elif forecasted_risk >= 50:
        stop_loss_pct = 7.0  # Moderate stop
    else:
        stop_loss_pct = 10.0  # Wider stop for lower risk
    
    stop_loss_price = current_price * (1 - stop_loss_pct / 100)
    downside_pct = stop_loss_pct
    
    return {
        "type": "stop_loss",
        "priority": "high" if forecasted_risk >= 70 else "medium",
        "action": f"Set stop-loss at ${stop_loss_price:.2f}",
        "reason": f"Protects {downside_pct:.1f}% downside given forecasted risk of {forecasted_risk:.0f}/100",
        "stop_loss_price": round(stop_loss_price, 2),
        "downside_protection_pct": round(downside_pct, 1)
    }


def generate_smart_recommendations(
    session: Session,
    symbol: str,
    forecast: Dict,
    user_tolerance: str = "moderate"
) -> List[Dict]:
    """
    Generate comprehensive smart recommendations.
    """
    recommendations = []
    
    current_risk = forecast.get("current_score", 50)
    predicted_risk = forecast.get("predicted_score", 50)
    trend = forecast.get("trend_direction", "stable")
    
    # 1. Position Size Recommendation
    position_rec = calculate_position_size_recommendation(
        current_risk, predicted_risk, user_tolerance
    )
    recommendations.extend(position_rec["recommendations"])
    
    # 2. Stop Loss Recommendation (if high risk)
    if predicted_risk >= 50:
        current_price = get_current_price(session, symbol)
        if current_price:
            stop_loss_rec = calculate_stop_loss_recommendation(
                current_price, current_risk, predicted_risk
            )
            if stop_loss_rec:
                recommendations.append(stop_loss_rec)
    
    # 3. Monitoring Recommendation
    if trend == "increasing" and predicted_risk > current_risk:
        risk_increase = predicted_risk - current_risk
        if risk_increase > 10:
            recommendations.append({
                "type": "monitoring",
                "priority": "high",
                "action": f"Monitor closely - risk expected to increase by {risk_increase:.0f} points",
                "reason": f"Risk forecast shows significant increase. Consider exit if risk score exceeds {current_risk + 15:.0f}"
            })
        else:
            recommendations.append({
                "type": "monitoring",
                "priority": "medium",
                "action": "Monitor risk levels over next few days",
                "reason": f"Risk trend is increasing - watch for continuation"
            })
    elif trend == "decreasing":
        recommendations.append({
            "type": "monitoring",
            "priority": "low",
            "action": "Risk levels improving - continue monitoring",
            "reason": "Risk trend is decreasing - positive development"
        })
    
    # 4. Exit Signal Recommendation
    if predicted_risk >= 75:
        recommendations.append({
            "type": "exit_signal",
            "priority": "high",
            "action": f"Consider exiting position if risk score exceeds 75",
            "reason": f"Forecasted risk ({predicted_risk:.0f}) is very high - consider protecting capital"
        })
    elif predicted_risk >= 70 and trend == "increasing":
        recommendations.append({
            "type": "exit_signal",
            "priority": "medium",
            "action": "Prepare exit strategy - risk approaching critical levels",
            "reason": f"Risk is high ({predicted_risk:.0f}) and trending up - have exit plan ready"
        })
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 2))
    
    return recommendations


def format_recommendations_for_display(recommendations: List[Dict]) -> Dict:
    """
    Format recommendations for frontend display.
    """
    return {
        "recommendations": recommendations,
        "summary": {
            "total": len(recommendations),
            "high_priority": len([r for r in recommendations if r.get("priority") == "high"]),
            "medium_priority": len([r for r in recommendations if r.get("priority") == "medium"]),
            "low_priority": len([r for r in recommendations if r.get("priority") == "low"])
        }
    }

