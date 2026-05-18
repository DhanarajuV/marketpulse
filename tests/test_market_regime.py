"""Tests for market regime agent."""
from src.agents.market_regime import adjust_conviction


class TestMarketRegime:
    def test_extreme_fear_boosts_panic_sell(self):
        signal = {"signal_type": "panic_sell", "conviction": "MEDIUM", "reasoning": []}
        regime = {"regime": "extreme_fear", "vix": 35, "spy_change": -2.0}
        result = adjust_conviction(signal, regime)
        assert result["conviction"] == "HIGH"
        assert any("VIX" in r for r in result["reasoning"])

    def test_complacency_downgrades_breakout(self):
        signal = {"signal_type": "breakout", "conviction": "HIGH", "reasoning": []}
        regime = {"regime": "complacency", "vix": 12, "spy_change": 0.5}
        result = adjust_conviction(signal, regime)
        assert result["conviction"] == "MEDIUM"

    def test_normal_regime_no_change(self):
        signal = {"signal_type": "panic_sell", "conviction": "MEDIUM", "reasoning": []}
        regime = {"regime": "normal", "vix": 16, "spy_change": 0.1}
        result = adjust_conviction(signal, regime)
        assert result["conviction"] == "MEDIUM"

    def test_squeeze_unaffected_by_regime(self):
        signal = {"signal_type": "short_squeeze", "conviction": "MEDIUM", "reasoning": []}
        regime = {"regime": "complacency", "vix": 12, "spy_change": 0.5}
        result = adjust_conviction(signal, regime)
        assert result["conviction"] == "MEDIUM"
