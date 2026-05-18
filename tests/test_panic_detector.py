"""Tests for panic sell detector."""
from src.agents.panic_detector import detect_panic_sells


class TestPanicDetector:
    def _make_indicators(self, ticker, daily_change, rsi, price=100, ma_50=105, high_52w=120):
        return {
            ticker: {
                "price": price,
                "daily_change_pct": daily_change,
                "weekly_change_pct": daily_change * 2,
                "rsi": rsi,
                "ma_50": ma_50,
                "ma_200": 95,
                "volume_ratio": 1.5,
                "high_52w": high_52w,
                "low_52w": 80,
            },
            "QQQ": {"daily_change_pct": -0.5},  # Sector ETF barely down
        }

    def test_detects_panic_sell(self):
        indicators = self._make_indicators("AAPL", daily_change=-6, rsi=25)
        signals = detect_panic_sells(indicators, {})
        assert len(signals) == 1
        assert signals[0]["ticker"] == "AAPL"
        assert signals[0]["signal_type"] == "panic_sell"

    def test_ignores_small_drop(self):
        indicators = self._make_indicators("AAPL", daily_change=-2, rsi=25)
        signals = detect_panic_sells(indicators, {})
        assert len(signals) == 0

    def test_ignores_high_rsi(self):
        indicators = self._make_indicators("AAPL", daily_change=-6, rsi=50)
        signals = detect_panic_sells(indicators, {})
        assert len(signals) == 0

    def test_ignores_sector_wide_drop(self):
        indicators = self._make_indicators("AAPL", daily_change=-6, rsi=25)
        indicators["QQQ"]["daily_change_pct"] = -5  # Sector also down big
        signals = detect_panic_sells(indicators, {})
        assert len(signals) == 0

    def test_high_conviction_on_extreme(self):
        indicators = self._make_indicators("AAPL", daily_change=-8, rsi=22)
        signals = detect_panic_sells(indicators, {})
        assert signals[0]["conviction"] == "HIGH"

    def test_medium_conviction_on_moderate(self):
        indicators = self._make_indicators("AAPL", daily_change=-5.5, rsi=28)
        signals = detect_panic_sells(indicators, {})
        assert signals[0]["conviction"] == "MEDIUM"

    def test_exit_levels_calculated(self):
        indicators = self._make_indicators("AAPL", daily_change=-6, rsi=25, price=100)
        signals = detect_panic_sells(indicators, {})
        s = signals[0]
        assert s["stop_loss"] == 80.0  # 20% below
        assert s["target_1"] > s["entry_price"]  # Recovery target above entry
        assert s["time_stop_days"] == 14

    def test_unknown_sector_skipped(self):
        indicators = {
            "ZZZZZ": {"price": 50, "daily_change_pct": -7, "rsi": 20, "ma_50": 55, "high_52w": 70},
        }
        signals = detect_panic_sells(indicators, {})
        assert len(signals) == 0
