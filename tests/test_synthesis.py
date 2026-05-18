"""Tests for synthesis agent."""
from src.agents.synthesis import synthesize_signals


class TestSynthesis:
    def test_single_signal_passes_through(self):
        signals = [{"ticker": "AAPL", "signal_type": "breakout", "target_1": 110, "entry_price": 100, "reasoning": ["test"]}]
        result = synthesize_signals(signals)
        assert len(result) == 1
        assert result[0]["ticker"] == "AAPL"

    def test_deduplicates_same_ticker(self):
        signals = [
            {"ticker": "AAPL", "signal_type": "breakout", "target_1": 110, "entry_price": 100, "reasoning": ["breakout reason"]},
            {"ticker": "AAPL", "signal_type": "chart_pattern", "target_1": 115, "entry_price": 100, "reasoning": ["pattern reason"]},
        ]
        result = synthesize_signals(signals)
        assert len(result) == 1

    def test_merged_signal_has_high_conviction(self):
        signals = [
            {"ticker": "AAPL", "signal_type": "breakout", "target_1": 110, "entry_price": 100, "reasoning": ["r1"]},
            {"ticker": "AAPL", "signal_type": "chart_pattern", "target_1": 115, "entry_price": 100, "reasoning": ["r2"]},
        ]
        result = synthesize_signals(signals)
        assert result[0]["conviction"] == "HIGH"

    def test_merged_signal_combines_reasoning(self):
        signals = [
            {"ticker": "AAPL", "signal_type": "breakout", "target_1": 110, "entry_price": 100, "reasoning": ["reason A"]},
            {"ticker": "AAPL", "signal_type": "news_catalyst", "target_1": 108, "entry_price": 100, "reasoning": ["reason B"]},
        ]
        result = synthesize_signals(signals)
        assert "reason A" in result[0]["reasoning"]
        assert "reason B" in result[0]["reasoning"]
        assert "Multiple signals" in result[0]["reasoning"][0]

    def test_different_tickers_not_merged(self):
        signals = [
            {"ticker": "AAPL", "signal_type": "breakout", "target_1": 110, "entry_price": 100, "reasoning": ["r1"]},
            {"ticker": "NVDA", "signal_type": "breakout", "target_1": 150, "entry_price": 130, "reasoning": ["r2"]},
        ]
        result = synthesize_signals(signals)
        assert len(result) == 2

    def test_uses_best_risk_reward_as_base(self):
        signals = [
            {"ticker": "AAPL", "signal_type": "a", "target_1": 105, "entry_price": 100, "reasoning": ["low target"]},
            {"ticker": "AAPL", "signal_type": "b", "target_1": 120, "entry_price": 100, "reasoning": ["high target"]},
        ]
        result = synthesize_signals(signals)
        assert result[0]["target_1"] == 120  # Picks the better target
