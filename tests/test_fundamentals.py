"""Tests for fundamentals filter."""
from unittest.mock import patch, MagicMock
from src.agents.fundamentals import is_fundamentally_sound, filter_signals_by_fundamentals


class TestFundamentals:
    @patch("src.agents.fundamentals.get_fundamentals")
    def test_sound_company_passes(self, mock_fund):
        mock_fund.return_value = {
            "pe_ratio": 25, "forward_pe": 20, "peg_ratio": 1.5,
            "revenue_growth": 0.15, "earnings_growth": 0.10,
            "debt_to_equity": 50, "profit_margin": 0.20,
            "free_cash_flow": 5000000000, "return_on_equity": 0.25,
        }
        is_sound, reasons = is_fundamentally_sound("AAPL")
        assert is_sound is True

    @patch("src.agents.fundamentals.get_fundamentals")
    def test_high_pe_flagged(self, mock_fund):
        mock_fund.return_value = {
            "pe_ratio": 150, "forward_pe": None, "peg_ratio": None,
            "revenue_growth": 0.05, "earnings_growth": None,
            "debt_to_equity": 50, "profit_margin": 0.10,
            "free_cash_flow": 1000000, "return_on_equity": None,
        }
        is_sound, reasons = is_fundamentally_sound("XYZ")
        assert any("P/E very high" in r for r in reasons)

    @patch("src.agents.fundamentals.get_fundamentals")
    def test_declining_revenue_flagged(self, mock_fund):
        mock_fund.return_value = {
            "pe_ratio": 20, "forward_pe": None, "peg_ratio": None,
            "revenue_growth": -0.15, "earnings_growth": None,
            "debt_to_equity": 50, "profit_margin": 0.10,
            "free_cash_flow": 1000000, "return_on_equity": None,
        }
        is_sound, reasons = is_fundamentally_sound("XYZ")
        assert any("Revenue declining" in r for r in reasons)

    @patch("src.agents.fundamentals.get_fundamentals")
    def test_high_debt_flagged(self, mock_fund):
        mock_fund.return_value = {
            "pe_ratio": 20, "forward_pe": None, "peg_ratio": None,
            "revenue_growth": 0.05, "earnings_growth": None,
            "debt_to_equity": 400, "profit_margin": 0.10,
            "free_cash_flow": 1000000, "return_on_equity": None,
        }
        is_sound, reasons = is_fundamentally_sound("XYZ")
        assert any("High debt" in r for r in reasons)

    @patch("src.agents.fundamentals.get_fundamentals")
    def test_multiple_issues_fails(self, mock_fund):
        mock_fund.return_value = {
            "pe_ratio": 150, "forward_pe": None, "peg_ratio": None,
            "revenue_growth": -0.20, "earnings_growth": None,
            "debt_to_equity": 400, "profit_margin": -0.05,
            "free_cash_flow": -1000000, "return_on_equity": None,
        }
        is_sound, reasons = is_fundamentally_sound("XYZ")
        assert is_sound is False

    @patch("src.agents.fundamentals.get_fundamentals")
    def test_unavailable_fundamentals_passes(self, mock_fund):
        mock_fund.return_value = None
        is_sound, reasons = is_fundamentally_sound("XYZ")
        assert is_sound is True

    def test_squeeze_signals_bypass_filter(self):
        signals = [
            {"ticker": "GME", "signal_type": "short_squeeze", "reasoning": ["squeeze"]},
        ]
        result = filter_signals_by_fundamentals(signals)
        assert len(result) == 1
