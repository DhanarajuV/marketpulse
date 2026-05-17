import numpy as np
import pandas as pd
from scipy.signal import argrelextrema
from src.core.universe import get_sector_for_ticker


def find_local_extrema(prices: pd.Series, order: int = 10):
    """Find local peaks and troughs."""
    peaks = argrelextrema(prices.values, np.greater, order=order)[0]
    troughs = argrelextrema(prices.values, np.less, order=order)[0]
    return peaks, troughs


def detect_head_and_shoulders(prices: pd.Series, order: int = 10) -> dict | None:
    """Detect head and shoulders pattern (bearish reversal)."""
    peaks, troughs = find_local_extrema(prices, order)

    if len(peaks) < 3 or len(troughs) < 2:
        return None

    # Check last 3 peaks
    for i in range(len(peaks) - 2):
        left, head, right = peaks[i], peaks[i + 1], peaks[i + 2]

        # Head must be highest
        if not (prices.iloc[head] > prices.iloc[left] and prices.iloc[head] > prices.iloc[right]):
            continue

        # Shoulders roughly equal (within 10%)
        shoulder_diff = abs(prices.iloc[left] - prices.iloc[right]) / prices.iloc[left]
        if shoulder_diff > 0.10:
            continue

        # Neckline (connect troughs between shoulders)
        troughs_between = [t for t in troughs if left < t < right]
        if not troughs_between:
            continue

        neckline = min(prices.iloc[t] for t in troughs_between)

        # Pattern is valid if current price is near or below neckline
        current = prices.iloc[-1]
        if current <= neckline * 1.02:
            return {
                "pattern": "head_and_shoulders",
                "direction": "bearish",
                "neckline": neckline,
                "head_price": prices.iloc[head],
                "target": neckline - (prices.iloc[head] - neckline),  # Measured move
            }

    return None


def detect_double_bottom(prices: pd.Series, order: int = 10) -> dict | None:
    """Detect double bottom pattern (bullish reversal)."""
    _, troughs = find_local_extrema(prices, order)

    if len(troughs) < 2:
        return None

    # Check last 2 troughs
    for i in range(len(troughs) - 1):
        t1, t2 = troughs[i], troughs[i + 1]

        # Must be at least 10 bars apart
        if t2 - t1 < 10:
            continue

        # Troughs at similar level (within 5%)
        level_diff = abs(prices.iloc[t1] - prices.iloc[t2]) / prices.iloc[t1]
        if level_diff > 0.05:
            continue

        # Price between troughs should rise (the "W" shape)
        peak_between = prices.iloc[t1:t2].max()
        trough_level = min(prices.iloc[t1], prices.iloc[t2])

        # Current price should be above the peak between troughs (breakout)
        current = prices.iloc[-1]
        if current > peak_between:
            return {
                "pattern": "double_bottom",
                "direction": "bullish",
                "support_level": trough_level,
                "breakout_level": peak_between,
                "target": peak_between + (peak_between - trough_level),  # Measured move
            }

    return None


def detect_cup_and_handle(prices: pd.Series, min_cup_length: int = 30) -> dict | None:
    """Detect cup and handle pattern (bullish continuation)."""
    if len(prices) < min_cup_length + 10:
        return None

    # Look at recent price action
    recent = prices.tail(min_cup_length + 20)

    # Cup: price drops, rounds, comes back to starting level
    start_price = recent.iloc[0]
    low_price = recent.min()
    current = recent.iloc[-1]

    # Cup depth should be 15-35%
    cup_depth = (start_price - low_price) / start_price
    if not (0.15 <= cup_depth <= 0.35):
        return None

    # Current price should be near the cup's rim (within 5%)
    if abs(current - start_price) / start_price > 0.05:
        return None

    # The low should be in the middle-ish of the period (rounded bottom)
    low_idx = recent.values.argmin()
    if not (min_cup_length * 0.3 < low_idx < min_cup_length * 0.7):
        return None

    return {
        "pattern": "cup_and_handle",
        "direction": "bullish",
        "rim_level": start_price,
        "cup_low": low_price,
        "target": start_price + (start_price - low_price),  # Measured move
    }


def detect_chart_patterns(all_indicators: dict, prices: dict) -> list[dict]:
    """Run all pattern detectors across all tickers."""
    signals = []

    for ticker, df in prices.items():
        sector, etf = get_sector_for_ticker(ticker)
        if sector == "unknown":
            continue

        close = df["Close"]
        if len(close) < 60:
            continue

        current_price = close.iloc[-1]

        # Double bottom (bullish)
        db = detect_double_bottom(close)
        if db:
            target_1 = round(db["target"], 2)
            if current_price < target_1:
                signals.append({
                    "ticker": ticker,
                    "signal_type": "chart_pattern",
                    "entry_price": round(current_price, 2),
                    "stop_loss": round(db["support_level"] * 0.97, 2),
                    "target_1": target_1,
                    "target_2": round(db["target"] * 1.1, 2),
                    "target_3": round(db["target"] * 1.2, 2),
                    "time_stop_days": 30,
                    "conviction": "HIGH",
                    "reasoning": [
                        f"Double bottom pattern detected",
                        f"Support at ${db['support_level']:.2f} (tested twice)",
                        f"Breakout above ${db['breakout_level']:.2f}",
                        f"Measured move target: ${db['target']:.2f}",
                    ],
                    "sector": sector,
                })

        # Cup and handle (bullish)
        ch = detect_cup_and_handle(close)
        if ch:
            target_1 = round(ch["target"] * 0.8, 2)
            if current_price < target_1:
                signals.append({
                    "ticker": ticker,
                    "signal_type": "chart_pattern",
                    "entry_price": round(current_price, 2),
                    "stop_loss": round(ch["cup_low"] * 1.05, 2),
                    "target_1": target_1,
                    "target_2": round(ch["target"], 2),
                    "target_3": round(ch["target"] * 1.15, 2),
                    "time_stop_days": 30,
                    "conviction": "MEDIUM",
                    "reasoning": [
                        f"Cup and handle pattern detected",
                        f"Rim level: ${ch['rim_level']:.2f}",
                        f"Cup depth: {((ch['rim_level'] - ch['cup_low']) / ch['rim_level'] * 100):.1f}%",
                        f"Measured move target: ${ch['target']:.2f}",
                    ],
                    "sector": sector,
                })

        # Head and shoulders (bearish — warning, not a buy signal)
        hs = detect_head_and_shoulders(close)
        if hs and ticker in all_indicators:
            # Don't generate buy signal — instead, add warning to existing signals
            # Just log it for now
            pass

    return signals
