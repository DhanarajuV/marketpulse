import argparse
import pandas as pd
from src.scanner.run_scan import run_full_scan
from src.scanner.price_scanner import fetch_all_prices, calculate_indicators
from src.agents.panic_detector import detect_panic_sells
from src.agents.squeeze_detector import detect_short_squeezes
from src.agents.technical_agent import detect_breakouts
from src.agents.chart_patterns import detect_chart_patterns
from src.storage.database import get_active_signals, get_signal_stats
from src.core.universe import SECTORS
import yfinance as yf


def check_ticker(ticker: str):
    """Check a specific ticker for all signals."""
    print(f"\n🔍 Checking {ticker.upper()}...")

    data = yf.download(ticker.upper(), period="6mo", progress=False)
    if data.empty:
        print(f"  ❌ No data found for {ticker}")
        return

    # Flatten multi-level columns for single ticker download
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    from src.scanner.price_scanner import calculate_indicators
    indicators = calculate_indicators(data)

    print(f"\n  📊 {ticker.upper()} at ${indicators['price']:.2f}")
    print(f"  RSI: {indicators['rsi']:.1f} | Daily: {indicators['daily_change_pct']:+.1f}%")
    print(f"  MA50: ${indicators['ma_50']:.2f} | MA200: ${indicators['ma_200']:.2f}")
    print(f"  Volume: {indicators['volume_ratio']:.1f}x average")
    print(f"  52W Range: ${indicators['low_52w']:.2f} - ${indicators['high_52w']:.2f}")

    # Check short interest
    try:
        info = yf.Ticker(ticker.upper()).info
        short_pct = info.get("shortPercentOfFloat", 0) * 100
        short_ratio = info.get("shortRatio", 0)
        print(f"  Short Interest: {short_pct:.1f}% | Days to Cover: {short_ratio:.1f}")
    except Exception:
        pass


def check_sector(sector_name: str):
    """Check all stocks in a sector."""
    sector_name = sector_name.lower()
    if sector_name not in SECTORS:
        print(f"  ❌ Unknown sector: {sector_name}")
        print(f"  Available: {', '.join(SECTORS.keys())}")
        return

    sector = SECTORS[sector_name]
    print(f"\n🔍 Scanning sector: {sector_name} (ETF: {sector['etf']})")

    tickers = [sector["etf"]] + sector["stocks"]
    data = yf.download(tickers, period="6mo", group_by="ticker", progress=False)

    for ticker in tickers:
        try:
            df = data[ticker].dropna()
            if df.empty:
                continue
            ind = calculate_indicators(df)
            flag = ""
            if ind["rsi"] < 30:
                flag = "⚠️ OVERSOLD"
            elif ind["rsi"] > 70:
                flag = "🔥 OVERBOUGHT"
            print(f"  {ticker:6s} ${ind['price']:8.2f} | {ind['daily_change_pct']:+5.1f}% | RSI {ind['rsi']:5.1f} {flag}")
        except Exception:
            continue


def show_history():
    """Show active signals and stats."""
    active = get_active_signals()
    stats = get_signal_stats()

    print(f"\n📋 Active Positions: {len(active)}")
    for s in active:
        print(f"  {s['ticker']:6s} | {s['signal_type']:15s} | Entry: ${s['entry_price']:.2f} | {s['conviction']}")

    print(f"\n📊 Stats:")
    print(f"  Total closed: {stats['total_closed']}")
    print(f"  Wins: {stats['wins']} | Losses: {stats['losses']}")
    print(f"  Win rate: {stats['win_rate']:.0%}")


def main():
    parser = argparse.ArgumentParser(description="MarketPulse CLI")
    parser.add_argument("command", choices=["scan", "check", "sector", "history"])
    parser.add_argument("--ticker", "-t", help="Ticker to check")
    parser.add_argument("--sector", "-s", help="Sector to scan")
    args = parser.parse_args()

    if args.command == "scan":
        run_full_scan()
    elif args.command == "check":
        if not args.ticker:
            print("Usage: python cli.py check --ticker NVDA")
            return
        check_ticker(args.ticker)
    elif args.command == "sector":
        if not args.sector:
            print("Usage: python cli.py sector --sector semiconductors")
            print(f"Available: {', '.join(SECTORS.keys())}")
            return
        check_sector(args.sector)
    elif args.command == "history":
        show_history()


if __name__ == "__main__":
    main()
