import yfinance as yf


def get_fundamentals(ticker: str) -> dict | None:
    """Fetch fundamental data for a ticker."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "debt_to_equity": info.get("debtToEquity"),
            "profit_margin": info.get("profitMargins"),
            "free_cash_flow": info.get("freeCashflow"),
            "return_on_equity": info.get("returnOnEquity"),
        }
    except Exception:
        return None


def is_fundamentally_sound(ticker: str) -> tuple[bool, list[str]]:
    """Check if a stock has acceptable fundamentals. Returns (pass, reasons)."""
    data = get_fundamentals(ticker)
    if not data:
        return True, ["Fundamentals unavailable — skipping filter"]

    issues = []
    strengths = []

    # P/E ratio — not absurdly overvalued
    pe = data["pe_ratio"]
    if pe and pe > 100:
        issues.append(f"P/E very high ({pe:.1f})")
    elif pe and pe > 0:
        strengths.append(f"P/E: {pe:.1f}")

    # Revenue growth — should be positive or stable
    rev_growth = data["revenue_growth"]
    if rev_growth and rev_growth < -0.10:
        issues.append(f"Revenue declining ({rev_growth*100:.1f}%)")
    elif rev_growth and rev_growth > 0.05:
        strengths.append(f"Revenue growing {rev_growth*100:.1f}%")

    # Debt — not dangerously leveraged
    dte = data["debt_to_equity"]
    if dte and dte > 300:
        issues.append(f"High debt-to-equity ({dte:.0f}%)")

    # Profitability
    margin = data["profit_margin"]
    if margin and margin < 0:
        issues.append(f"Unprofitable (margin {margin*100:.1f}%)")
    elif margin and margin > 0.10:
        strengths.append(f"Profit margin {margin*100:.1f}%")

    # Free cash flow — should be positive
    fcf = data["free_cash_flow"]
    if fcf and fcf < 0:
        issues.append("Negative free cash flow")

    # Pass if no more than 1 issue
    is_sound = len(issues) <= 1

    return is_sound, strengths + issues


def filter_signals_by_fundamentals(signals: list[dict]) -> list[dict]:
    """Remove signals for fundamentally weak stocks. Skip for short squeezes."""
    filtered = []

    for signal in signals:
        # Short squeezes are momentum plays — fundamentals don't apply
        if "short_squeeze" in signal["signal_type"]:
            filtered.append(signal)
            continue

        is_sound, reasons = is_fundamentally_sound(signal["ticker"])

        if is_sound:
            for r in reasons:
                if not r.startswith("Revenue declining") and not r.startswith("High debt"):
                    signal["reasoning"].append(f"📊 {r}")
            filtered.append(signal)
        else:
            print(f"  ⛔ Filtered out {signal['ticker']}: {', '.join(reasons)}")

    return filtered
