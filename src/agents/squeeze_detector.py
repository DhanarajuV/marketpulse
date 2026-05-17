import yfinance as yf
from src.core.config import config
from src.core.universe import get_sector_for_ticker

THRESHOLDS = config["scanner"]["thresholds"]["short_squeeze"]


def detect_short_squeezes(all_indicators: dict) -> list[dict]:
    """Find stocks with high short interest and rising price (squeeze building)."""
    signals = []

    for ticker, indicators in all_indicators.items():
        sector, etf = get_sector_for_ticker(ticker)
        if sector == "unknown":
            continue

        # Fetch short interest data
        try:
            info = yf.Ticker(ticker).info
            short_pct = info.get("shortPercentOfFloat", 0) * 100
            short_ratio = info.get("shortRatio", 0)  # days to cover
        except Exception:
            continue

        if short_pct < THRESHOLDS["min_short_interest"]:
            continue
        if short_ratio < THRESHOLDS["min_days_to_cover"]:
            continue

        # Check if price is rising (momentum building)
        weekly_change = indicators["weekly_change_pct"]
        if weekly_change < THRESHOLDS["min_price_change_5d"]:
            continue

        # Check volume spike
        if indicators["volume_ratio"] < THRESHOLDS["min_volume_ratio"]:
            continue

        # Calculate exit levels
        price = indicators["price"]
        stop_loss = round(price * 0.80, 2)
        target_1 = round(price * 1.15, 2)
        target_2 = round(price * 1.25, 2)
        squeeze_mult = min(1 + (short_pct / 100) * 2, 1.50)
        target_3 = round(price * squeeze_mult, 2)

        conviction = "HIGH" if short_pct > 30 and short_ratio > 7 else "MEDIUM"

        signals.append({
            "ticker": ticker,
            "signal_type": "short_squeeze",
            "entry_price": round(price, 2),
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_2,
            "target_3": target_3,
            "time_stop_days": 14,
            "conviction": conviction,
            "reasoning": [
                f"Short interest: {short_pct:.1f}% of float",
                f"Days to cover: {short_ratio:.1f}",
                f"Price up {weekly_change:.1f}% in 5 days",
                f"Volume {indicators['volume_ratio']:.1f}x average",
                f"⚠️ RISK: Momentum play, not fundamentals. Use strict stop-loss. Can reverse fast.",
            ],
            "sector": sector,
        })

    return signals
