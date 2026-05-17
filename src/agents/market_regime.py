import yfinance as yf


def get_market_regime() -> dict:
    """Assess overall market conditions using VIX and SPY."""
    try:
        vix = yf.Ticker("^VIX").history(period="5d")
        spy = yf.Ticker("SPY").history(period="5d")

        if vix.empty or spy.empty:
            return {"regime": "unknown", "vix": 0, "spy_change": 0}

        vix_current = vix["Close"].iloc[-1]
        spy_change = (spy["Close"].iloc[-1] / spy["Close"].iloc[-2] - 1) * 100

        # Classify regime
        if vix_current > 30:
            regime = "extreme_fear"
        elif vix_current > 20:
            regime = "elevated_fear"
        elif vix_current < 13:
            regime = "complacency"
        else:
            regime = "normal"

        return {
            "regime": regime,
            "vix": round(vix_current, 2),
            "spy_change": round(spy_change, 2),
        }
    except Exception:
        return {"regime": "unknown", "vix": 0, "spy_change": 0}


def adjust_conviction(signal: dict, regime: dict) -> dict:
    """Adjust signal conviction based on market regime."""
    # Extreme fear = panic sells are MORE likely to recover
    if regime["regime"] == "extreme_fear" and signal["signal_type"] == "panic_sell":
        signal["conviction"] = "HIGH"
        signal["reasoning"].append(f"VIX at {regime['vix']} (extreme fear = better mean reversion odds)")

    # Complacency = breakouts are LESS reliable
    if regime["regime"] == "complacency" and signal["signal_type"] == "breakout":
        if signal["conviction"] == "HIGH":
            signal["conviction"] = "MEDIUM"
        signal["reasoning"].append(f"VIX at {regime['vix']} (low vol = breakouts less reliable)")

    return signal
