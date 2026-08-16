import time
from src.scanner.price_scanner import fetch_all_prices, calculate_indicators
from src.agents.panic_detector import detect_panic_sells
from src.agents.squeeze_detector import detect_short_squeezes
from src.agents.technical_agent import detect_breakouts
from src.agents.news_catalyst import detect_news_catalysts
from src.agents.chart_patterns import detect_chart_patterns
from src.agents.market_regime import get_market_regime, adjust_conviction
from src.agents.position_monitor import check_active_positions
from src.agents.synthesis import synthesize_signals
from src.agents.fundamentals import filter_signals_by_fundamentals
from src.alerts.telegram import send_scan_results
from src.storage.database import save_signal, get_active_signals


def run_full_scan():
    """Execute a complete market scan."""
    start = time.time()
    print("=" * 60)
    print("MARKETPULSE SCAN")
    print("=" * 60)

    # Step 1: Fetch prices
    print("\n📊 Fetching price data...")
    prices = fetch_all_prices()

    # Step 2: Calculate indicators
    print("📈 Calculating indicators...")
    all_indicators = {}
    for ticker, df in prices.items():
        try:
            all_indicators[ticker] = calculate_indicators(df)
        except Exception as e:
            print(f"  ⚠️ Error calculating {ticker}: {e}")

    print(f"  Calculated indicators for {len(all_indicators)} tickers")

    # Step 3: Get market regime
    print("\n🌍 Assessing market regime...")
    regime = get_market_regime()
    print(f"  Regime: {regime['regime']} | VIX: {regime['vix']} | SPY: {regime['spy_change']:+.1f}%")

    # Step 4: Check active positions
    print("\n📋 Checking active positions...")
    active = get_active_signals()
    print(f"  Active positions: {len(active)}")
    sell_alerts = check_active_positions(all_indicators)
    if sell_alerts:
        print(f"  ⚡ {len(sell_alerts)} position alert(s) triggered")

    # Step 5: Detect new signals
    print("\n🔍 Scanning for new signals...")

    panic_signals = detect_panic_sells(all_indicators, prices)
    print(f"  Panic sell signals: {len(panic_signals)}")

    print("  Checking short squeezes...")
    squeeze_signals = detect_short_squeezes(all_indicators)
    print(f"  Short squeeze signals: {len(squeeze_signals)}")

    breakout_signals = detect_breakouts(all_indicators, prices)
    print(f"  Breakout signals: {len(breakout_signals)}")

    print("  Detecting chart patterns...")
    pattern_signals = detect_chart_patterns(all_indicators, prices)
    print(f"  Chart pattern signals: {len(pattern_signals)}")

    print("  Scanning news catalysts...")
    news_signals = detect_news_catalysts(all_indicators)
    print(f"  News catalyst signals: {len(news_signals)}")

    # Combine all new signals
    all_signals = panic_signals + squeeze_signals + breakout_signals + pattern_signals + news_signals

    # Step 6: Adjust conviction based on market regime
    all_signals = [adjust_conviction(s, regime) for s in all_signals]

    # Step 6b: Synthesize — deduplicate and boost multi-signal tickers
    all_signals = synthesize_signals(all_signals)

    # Step 6c: Filter by fundamentals — remove weak companies
    print("\n📊 Checking fundamentals...")
    all_signals = filter_signals_by_fundamentals(all_signals)

    # Step 7: Save to DB and output
    new_signals = []
    if all_signals:
        print(f"\n🔥 {len(all_signals)} SIGNAL(S) DETECTED:")
        for s in all_signals:
            saved = save_signal(s)
            if saved:
                new_signals.append(s)
                print(f"\n  {'='*50}")
                print(f"  {s['signal_type'].upper()} — {s['ticker']} at ${s['entry_price']}")
                print(f"  Conviction: {s['conviction']} | Sector: {s['sector']}")
                print(f"  Reasoning:")
                for r in s['reasoning']:
                    print(f"    • {r}")
                print(f"  Stop: ${s['stop_loss']} | T1: ${s['target_1']} | T2: ${s['target_2']} | T3: ${s['target_3']}")
    else:
        print("\n✅ No new actionable signals detected.")

    # Step 8: Send Telegram alerts (only for newly saved signals)
    print("\n📱 Sending alerts...")
    send_scan_results(new_signals)

    duration = time.time() - start
    print(f"\n⏱️ Scan completed in {duration:.1f} seconds")
    print(f"  Signals detected: {len(all_signals)} | New (saved): {len(new_signals)}")
    return new_signals


if __name__ == "__main__":
    run_full_scan()
