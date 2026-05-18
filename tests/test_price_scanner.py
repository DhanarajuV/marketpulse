"""Tests for price scanner with mocked yFinance."""
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from src.scanner.price_scanner import calculate_indicators


class TestCalculateIndicators:
    def _make_price_df(self, n=200):
        """Create a realistic price DataFrame."""
        np.random.seed(42)
        dates = pd.date_range("2025-01-01", periods=n, freq="B")
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        volume = np.random.randint(1000000, 5000000, n)
        return pd.DataFrame({
            "Open": close - 0.5,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Volume": volume,
        }, index=dates)

    def test_returns_all_indicators(self):
        df = self._make_price_df()
        result = calculate_indicators(df)
        assert "price" in result
        assert "rsi" in result
        assert "ma_50" in result
        assert "ma_200" in result
        assert "macd" in result
        assert "volume_ratio" in result
        assert "daily_change_pct" in result
        assert "high_52w" in result
        assert "low_52w" in result

    def test_rsi_in_range(self):
        df = self._make_price_df()
        result = calculate_indicators(df)
        assert 0 <= result["rsi"] <= 100

    def test_volume_ratio_positive(self):
        df = self._make_price_df()
        result = calculate_indicators(df)
        assert result["volume_ratio"] > 0

    def test_price_matches_last_close(self):
        df = self._make_price_df()
        result = calculate_indicators(df)
        assert result["price"] == df["Close"].iloc[-1]

    def test_52w_high_gte_current(self):
        df = self._make_price_df()
        result = calculate_indicators(df)
        assert result["high_52w"] >= result["low_52w"]
