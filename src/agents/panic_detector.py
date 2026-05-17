from src.core.config import config
from src.core.universe import get_sector_for_ticker

THRESHOLDS = config["scanner"]["thresholds"]["panic_sell"]


def detect_panic_sells(all_indicators: dict, prices: dict) -> list[dict]:
    """Find stocks that dropped significantly without sector-wide cause."""
    signals = []

    for ticker, indicators in all_indicators.items():
        # Skip ETFs
        sector, etf = get_sector_for_ticker(ticker)
        if sector == "unknown":
            continue

        # Check conditions
        drop = indicators["daily_change_pct"]
        rsi = indicators["rsi"]

        # Condition 1: Significant drop
        if drop > -THRESHOLDS["min_drop_pct"]:
            continue

        # Condition 2: Oversold
        if rsi > THRESHOLDS["max_rsi"]:
            continue

        # Condition 3: Sector NOT down proportionally
        if etf in all_indicators:
            sector_drop = all_indicators[etf]["daily_change_pct"]
            if sector_drop < -THRESHOLDS["max_sector_drop_pct"]:
                continue  # Whole sector is down, not stock-specific

        # Calculate exit levels
        price = indicators["price"]
        stop_loss = round(price * 0.80, 2)
        target_1 = round(price / (1 + drop / 100), 2)  # Recovery to pre-drop
        target_2 = round(indicators["ma_50"], 2)
        target_3 = round(indicators["high_52w"] * 0.9, 2)

        signals.append({
            "ticker": ticker,
            "signal_type": "panic_sell",
            "entry_price": round(price, 2),
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_2,
            "target_3": target_3,
            "time_stop_days": 14,
            "conviction": "HIGH" if rsi < 25 and drop < -7 else "MEDIUM",
            "reasoning": [
                f"Down {drop:.1f}% today",
                f"RSI at {rsi:.1f} (oversold)",
                f"Sector ({etf}) only down {all_indicators.get(etf, {}).get('daily_change_pct', 0):.1f}%",
            ],
            "sector": sector,
        })

    return signals
