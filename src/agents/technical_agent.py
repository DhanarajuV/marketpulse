import pandas as pd
from src.core.config import config
from src.core.universe import get_sector_for_ticker

THRESHOLDS = config["scanner"]["thresholds"]["breakout"]


def detect_breakouts(all_indicators: dict, prices: dict) -> list[dict]:
    """Find stocks breaking out above resistance on high volume."""
    signals = []

    for ticker, indicators in all_indicators.items():
        sector, etf = get_sector_for_ticker(ticker)
        if sector == "unknown":
            continue

        rsi = indicators["rsi"]
        volume_ratio = indicators["volume_ratio"]
        price = indicators["price"]
        ma_50 = indicators["ma_50"]
        ma_200 = indicators["ma_200"]

        signal_reasons = []

        # Check 1: Golden cross (50-day crosses above 200-day)
        if ticker in prices and len(prices[ticker]) >= 200:
            close = prices[ticker]["Close"]
            ma50_prev = close.rolling(50).mean().iloc[-2]
            ma200_prev = close.rolling(200).mean().iloc[-2]

            if ma50_prev < ma200_prev and ma_50 > ma_200:
                signal_reasons.append(f"Golden cross: 50-day MA crossed above 200-day MA")

        # Check 2: Price breaking above 52-week high on volume
        if price >= indicators["high_52w"] * 0.98 and volume_ratio >= THRESHOLDS["min_volume_ratio"]:
            signal_reasons.append(f"Near 52-week high (${indicators['high_52w']:.2f}) on {volume_ratio:.1f}x volume")

        # Check 3: RSI in momentum zone (not overbought)
        rsi_min, rsi_max = THRESHOLDS["rsi_range"]
        if not (rsi_min <= rsi <= rsi_max):
            # Skip if overbought or no momentum
            if not signal_reasons:
                continue

        # Need at least one breakout signal + volume confirmation
        if not signal_reasons:
            continue
        if volume_ratio < THRESHOLDS["min_volume_ratio"]:
            continue

        # Calculate exit levels
        stop_loss = round(min(ma_50, price * 0.92), 2)  # Below MA50 or -8%
        target_1 = round(price * 1.10, 2)
        target_2 = round(price * 1.20, 2)
        target_3 = round(price * 1.30, 2)

        signal_reasons.append(f"RSI: {rsi:.1f} (momentum zone)")
        signal_reasons.append(f"Volume: {volume_ratio:.1f}x average")

        signals.append({
            "ticker": ticker,
            "signal_type": "breakout",
            "entry_price": round(price, 2),
            "stop_loss": stop_loss,
            "target_1": target_1,
            "target_2": target_2,
            "target_3": target_3,
            "time_stop_days": 30,
            "conviction": "HIGH" if len(signal_reasons) >= 4 else "MEDIUM",
            "reasoning": signal_reasons,
            "sector": sector,
        })

    return signals
