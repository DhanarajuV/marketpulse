"""Tests for technical breakout detector."""
import pandas as pd
import numpy as np
from src.agents.technical_agent import detect_breakouts


class TestBreakoutDetector:
    def _make_indicators(self, ticker, price, volume_ratio, rsi, ma_50, ma_200, high_52w):
        return {
            ticker: {
                "price": price,
                "daily_change_pct": 2.0,
                "weekly_change_pct": 5.0,
                "rsi": rsi,
                "ma_50": ma_50,
                "ma_200": ma_200,
                "volume_ratio": volume_ratio,
                "high_52w": high_52w,
                "low_52w": 50,
            }
        }

    def test_detects_52w_high_breakout(self):
        indicators = self._make_indicators("AAPL", price=100, volume_ratio=2.0, rsi=60, ma_50=95, ma_200=90, high_52w=100)
        signals = detect_breakouts(indicators, {})
        assert len(signals) >= 1
        assert signals[0]["signal_type"] == "breakout"

    def test_ignores_low_volume(self):
        indicators = self._make_indicators("AAPL", price=100, volume_ratio=0.8, rsi=60, ma_50=95, ma_200=90, high_52w=100)
        signals = detect_breakouts(indicators, {})
        assert len(signals) == 0

    def test_ignores_unknown_sector(self):
        indicators = self._make_indicators("ZZZZZ", price=100, volume_ratio=2.0, rsi=60, ma_50=95, ma_200=90, high_52w=100)
        signals = detect_breakouts(indicators, {})
        assert len(signals) == 0

    def test_exit_levels_present(self):
        indicators = self._make_indicators("AAPL", price=100, volume_ratio=2.0, rsi=60, ma_50=95, ma_200=90, high_52w=100)
        signals = detect_breakouts(indicators, {})
        if signals:
            s = signals[0]
            assert s["stop_loss"] < s["entry_price"]
            assert s["target_1"] > s["entry_price"]
            assert s["target_2"] > s["target_1"]
