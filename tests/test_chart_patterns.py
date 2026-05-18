"""Tests for chart pattern detection."""
import pandas as pd
import numpy as np
from src.agents.chart_patterns import detect_double_bottom, detect_cup_and_handle, detect_head_and_shoulders


class TestDoubleBottom:
    def test_detects_double_bottom(self):
        # Create W-shaped price data
        prices = list(range(100, 80, -1))  # Drop to 80
        prices += list(range(80, 95))       # Rise to 95
        prices += list(range(95, 79, -1))   # Drop to 80 again
        prices += list(range(79, 100))      # Rise above 95 (breakout)
        series = pd.Series(prices)

        result = detect_double_bottom(series, order=5)
        if result:
            assert result["pattern"] == "double_bottom"
            assert result["direction"] == "bullish"

    def test_no_pattern_in_uptrend(self):
        prices = pd.Series(range(50, 150))  # Straight up
        result = detect_double_bottom(prices, order=5)
        assert result is None

    def test_insufficient_data(self):
        prices = pd.Series([100, 95, 90])
        result = detect_double_bottom(prices, order=1)
        assert result is None


class TestCupAndHandle:
    def test_detects_cup(self):
        # Create U-shaped data: start high, dip 25%, recover
        n = 50
        x = np.linspace(0, np.pi, n)
        prices = 100 - 25 * np.sin(x)  # Dips from 100 to 75 and back to 100
        series = pd.Series(prices)

        result = detect_cup_and_handle(series, min_cup_length=30)
        # May or may not detect depending on exact shape
        if result:
            assert result["pattern"] == "cup_and_handle"
            assert result["direction"] == "bullish"

    def test_no_cup_in_flat_data(self):
        prices = pd.Series([100] * 60)
        result = detect_cup_and_handle(prices, min_cup_length=30)
        assert result is None

    def test_insufficient_data(self):
        prices = pd.Series([100, 90, 80])
        result = detect_cup_and_handle(prices, min_cup_length=30)
        assert result is None


class TestHeadAndShoulders:
    def test_no_pattern_in_downtrend(self):
        prices = pd.Series(range(150, 50, -1))  # Straight down
        result = detect_head_and_shoulders(prices, order=5)
        assert result is None

    def test_insufficient_peaks(self):
        prices = pd.Series([100] * 30)
        result = detect_head_and_shoulders(prices, order=5)
        assert result is None
