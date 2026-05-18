"""Tests for squeeze detector with mocked yFinance."""
from unittest.mock import patch, MagicMock
from src.agents.squeeze_detector import detect_short_squeezes


class TestSqueezeDetector:
    def _make_indicators(self, ticker, weekly_change, volume_ratio):
        return {
            ticker: {
                "price": 50.0,
                "daily_change_pct": 3.0,
                "weekly_change_pct": weekly_change,
                "rsi": 55,
                "ma_50": 48,
                "ma_200": 45,
                "volume_ratio": volume_ratio,
                "high_52w": 60,
                "low_52w": 30,
            }
        }

    @patch("src.agents.squeeze_detector.yf")
    def test_detects_squeeze(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortPercentOfFloat": 0.30, "shortRatio": 7.0}
        mock_yf.Ticker.return_value = mock_ticker

        indicators = self._make_indicators("INTC", weekly_change=5.0, volume_ratio=2.5)
        signals = detect_short_squeezes(indicators)
        assert len(signals) == 1
        assert signals[0]["signal_type"] == "short_squeeze"
        assert "RISK" in signals[0]["reasoning"][-1]

    @patch("src.agents.squeeze_detector.yf")
    def test_ignores_low_short_interest(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortPercentOfFloat": 0.05, "shortRatio": 2.0}
        mock_yf.Ticker.return_value = mock_ticker

        indicators = self._make_indicators("INTC", weekly_change=5.0, volume_ratio=2.5)
        signals = detect_short_squeezes(indicators)
        assert len(signals) == 0

    @patch("src.agents.squeeze_detector.yf")
    def test_ignores_low_volume(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortPercentOfFloat": 0.30, "shortRatio": 7.0}
        mock_yf.Ticker.return_value = mock_ticker

        indicators = self._make_indicators("INTC", weekly_change=5.0, volume_ratio=1.0)
        signals = detect_short_squeezes(indicators)
        assert len(signals) == 0

    @patch("src.agents.squeeze_detector.yf")
    def test_ignores_falling_price(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortPercentOfFloat": 0.30, "shortRatio": 7.0}
        mock_yf.Ticker.return_value = mock_ticker

        indicators = self._make_indicators("INTC", weekly_change=-2.0, volume_ratio=2.5)
        signals = detect_short_squeezes(indicators)
        assert len(signals) == 0

    @patch("src.agents.squeeze_detector.yf")
    def test_high_conviction_on_extreme(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortPercentOfFloat": 0.40, "shortRatio": 8.0}
        mock_yf.Ticker.return_value = mock_ticker

        indicators = self._make_indicators("INTC", weekly_change=5.0, volume_ratio=2.5)
        signals = detect_short_squeezes(indicators)
        assert signals[0]["conviction"] == "HIGH"

    @patch("src.agents.squeeze_detector.yf")
    def test_unknown_sector_skipped(self, mock_yf):
        indicators = {"ZZZZZ": {"weekly_change_pct": 5, "volume_ratio": 3, "price": 50}}
        signals = detect_short_squeezes(indicators)
        assert len(signals) == 0
