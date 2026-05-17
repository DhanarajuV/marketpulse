def synthesize_signals(all_signals: list[dict]) -> list[dict]:
    """Deduplicate signals for same ticker and boost conviction when multiple agents agree."""
    # Group by ticker
    by_ticker = {}
    for signal in all_signals:
        ticker = signal["ticker"]
        if ticker not in by_ticker:
            by_ticker[ticker] = []
        by_ticker[ticker].append(signal)

    synthesized = []

    for ticker, signals in by_ticker.items():
        if len(signals) == 1:
            synthesized.append(signals[0])
            continue

        # Multiple signals for same ticker — merge them
        # Use the one with best risk/reward as base
        base = max(signals, key=lambda s: s["target_1"] / s["entry_price"])

        # Combine reasoning from all signals
        all_reasons = []
        signal_types = []
        for s in signals:
            signal_types.append(s["signal_type"])
            all_reasons.extend(s["reasoning"])

        # Boost conviction — multiple agents agreeing = stronger signal
        base["conviction"] = "HIGH"
        base["reasoning"] = all_reasons
        base["reasoning"].insert(0, f"⚡ Multiple signals: {', '.join(signal_types)}")
        base["signal_type"] = " + ".join(sorted(set(signal_types)))

        synthesized.append(base)

    return synthesized
