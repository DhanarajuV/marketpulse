"""Tests for market regime with mocked yFinance."""
from unittest.mock import patch, MagicMock
import pandas as pd
from src.agents.market_regime import get_market_regime


class TestGetMarketRegime:
    @patch("src.agents.market_regime.yf")
    def test_extreme_fear(self, mock_yf):
        vix_data = pd.DataFrame({"Close": [28, 30, 32, 34, 35]})
        spy_data = pd.DataFrame({"Close": [450, 448, 445, 440, 438]})
        mock_yf.Ticker.side_effect = [
            MagicMock(history=MagicMock(return_value=vix_data)),
            MagicMock(history=MagicMock(return_value=spy_data)),
        ]
        result = get_market_regime()
        assert result["regime"] == "extreme_fear"
        assert result["vix"] == 35

    @patch("src.agents.market_regime.yf")
    def test_complacency(self, mock_yf):
        vix_data = pd.DataFrame({"Close": [13, 12.5, 12, 11.5, 11]})
        spy_data = pd.DataFrame({"Close": [500, 501, 502, 503, 504]})
        mock_yf.Ticker.side_effect = [
            MagicMock(history=MagicMock(return_value=vix_data)),
            MagicMock(history=MagicMock(return_value=spy_data)),
        ]
        result = get_market_regime()
        assert result["regime"] == "complacency"

    @patch("src.agents.market_regime.yf")
    def test_normal(self, mock_yf):
        vix_data = pd.DataFrame({"Close": [15, 16, 15.5, 16, 16.5]})
        spy_data = pd.DataFrame({"Close": [500, 501, 502, 503, 504]})
        mock_yf.Ticker.side_effect = [
            MagicMock(history=MagicMock(return_value=vix_data)),
            MagicMock(history=MagicMock(return_value=spy_data)),
        ]
        result = get_market_regime()
        assert result["regime"] == "normal"

    @patch("src.agents.market_regime.yf")
    def test_handles_error(self, mock_yf):
        mock_yf.Ticker.side_effect = Exception("API error")
        result = get_market_regime()
        assert result["regime"] == "unknown"

    @patch("src.agents.market_regime.yf")
    def test_empty_data(self, mock_yf):
        mock_yf.Ticker.return_value = MagicMock(history=MagicMock(return_value=pd.DataFrame()))
        result = get_market_regime()
        assert result["regime"] == "unknown"
