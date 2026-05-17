SECTORS = {
    "tech": {"etf": "QQQ", "stocks": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "CRM"]},
    "semiconductors": {"etf": "SMH", "stocks": ["NVDA", "AMD", "AVGO", "TSM", "INTC", "MU", "QCOM"]},
    "energy": {"etf": "XLE", "stocks": ["XOM", "CVX", "SLB", "OXY", "COP"]},
    "defense": {"etf": "ITA", "stocks": ["LMT", "RTX", "NOC", "GD", "BA", "PLTR"]},
    "healthcare": {"etf": "XLV", "stocks": ["UNH", "JNJ", "LLY", "PFE", "ABBV", "TMO"]},
    "financials": {"etf": "XLF", "stocks": ["JPM", "BAC", "GS", "V", "MA"]},
    "consumer": {"etf": "XLY", "stocks": ["AMZN", "TSLA", "HD", "NKE", "COST"]},
    "industrials": {"etf": "XLI", "stocks": ["CAT", "HON", "UPS", "DE", "GE"]},
}

def get_all_tickers() -> list[str]:
    """Get all unique tickers (stocks + ETFs)."""
    tickers = set()
    for sector in SECTORS.values():
        tickers.add(sector["etf"])
        tickers.update(sector["stocks"])
    return sorted(tickers)

def get_sector_for_ticker(ticker: str) -> tuple[str, str]:
    """Return (sector_name, etf) for a ticker."""
    for name, data in SECTORS.items():
        if ticker in data["stocks"]:
            return name, data["etf"]
    return "unknown", "SPY"
