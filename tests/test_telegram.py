"""Tests for Telegram alerts."""
from unittest.mock import patch
from src.alerts.telegram import format_signal, format_no_signals, send_scan_results


class TestTelegramFormatter:
    def test_format_signal(self):
        signal = {
            "ticker": "AAPL",
            "signal_type": "panic_sell",
            "entry_price": 150.0,
            "conviction": "HIGH",
            "sector": "tech",
            "reasoning": ["Down 6%", "RSI at 25"],
            "target_1": 160.0,
            "target_2": 170.0,
            "target_3": 180.0,
            "stop_loss": 120.0,
            "time_stop_days": 14,
        }
        msg = format_signal(signal)
        assert "AAPL" in msg
        assert "150" in msg
        assert "HIGH" in msg
        assert "Down 6%" in msg
        assert "$160" in msg
        assert "$120" in msg

    def test_format_no_signals(self):
        msg = format_no_signals()
        assert "No actionable signals" in msg

    @patch("src.alerts.telegram.send_alert")
    def test_send_scan_results_with_signals(self, mock_send):
        signals = [{"ticker": "AAPL", "signal_type": "breakout", "entry_price": 100,
                    "conviction": "HIGH", "sector": "tech", "reasoning": ["test"],
                    "target_1": 110, "target_2": 120, "target_3": 130,
                    "stop_loss": 90, "time_stop_days": 30}]
        send_scan_results(signals)
        mock_send.assert_called_once()

    @patch("src.alerts.telegram.send_alert")
    def test_send_scan_results_no_signals(self, mock_send):
        send_scan_results([])
        mock_send.assert_called_once()
        assert "No actionable" in mock_send.call_args[0][0]
