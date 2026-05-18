"""Tests for position monitor."""
from unittest.mock import patch
from datetime import datetime, timedelta
from src.agents.position_monitor import check_active_positions


class TestPositionMonitor:
    def _make_active_signal(self, ticker="AAPL", entry=100, stop=80, t1=110, t2=120, t3=130, days_left=14):
        return {
            "id": 1,
            "ticker": ticker,
            "entry_price": entry,
            "stop_loss": stop,
            "target_1": t1,
            "target_2": t2,
            "target_3": t3,
            "time_stop_date": (datetime.now() + timedelta(days=days_left)).isoformat(),
        }

    @patch("src.agents.position_monitor.send_alert")
    @patch("src.agents.position_monitor.close_signal")
    @patch("src.agents.position_monitor.get_active_signals")
    def test_stop_loss_triggered(self, mock_active, mock_close, mock_alert):
        mock_active.return_value = [self._make_active_signal(stop=80)]
        indicators = {"AAPL": {"price": 75}}  # Below stop

        alerts = check_active_positions(indicators)
        mock_close.assert_called_once()
        assert len(alerts) == 1
        assert alerts[0]["reason"] == "Stop-loss hit"

    @patch("src.agents.position_monitor.send_alert")
    @patch("src.agents.position_monitor.get_active_signals")
    def test_target_1_hit(self, mock_active, mock_alert):
        mock_active.return_value = [self._make_active_signal(t1=110, t3=130)]
        indicators = {"AAPL": {"price": 115}}  # Above T1 but below T3

        alerts = check_active_positions(indicators)
        assert len(alerts) == 1
        assert alerts[0]["reason"] == "Target 1 hit"

    @patch("src.agents.position_monitor.send_alert")
    @patch("src.agents.position_monitor.close_signal")
    @patch("src.agents.position_monitor.get_active_signals")
    def test_target_3_closes_position(self, mock_active, mock_close, mock_alert):
        mock_active.return_value = [self._make_active_signal(t1=110, t3=130)]
        indicators = {"AAPL": {"price": 135}}  # Above T3

        check_active_positions(indicators)
        mock_close.assert_called_once()

    @patch("src.agents.position_monitor.send_alert")
    @patch("src.agents.position_monitor.close_signal")
    @patch("src.agents.position_monitor.get_active_signals")
    def test_time_stop_triggered(self, mock_active, mock_close, mock_alert):
        signal = self._make_active_signal(days_left=-1)  # Expired
        mock_active.return_value = [signal]
        indicators = {"AAPL": {"price": 105}}

        alerts = check_active_positions(indicators)
        mock_close.assert_called_once()
        assert any(a["reason"] == "Time stop reached" for a in alerts)

    @patch("src.agents.position_monitor.send_alert")
    @patch("src.agents.position_monitor.get_active_signals")
    def test_no_alert_when_in_range(self, mock_active, mock_alert):
        mock_active.return_value = [self._make_active_signal(stop=80, t1=110)]
        indicators = {"AAPL": {"price": 95}}  # Between stop and T1

        alerts = check_active_positions(indicators)
        assert len(alerts) == 0
        mock_alert.assert_not_called()

    @patch("src.agents.position_monitor.send_alert")
    @patch("src.agents.position_monitor.get_active_signals")
    def test_ticker_not_in_indicators_skipped(self, mock_active, mock_alert):
        mock_active.return_value = [self._make_active_signal(ticker="XYZ")]
        indicators = {"AAPL": {"price": 100}}  # XYZ not here

        alerts = check_active_positions(indicators)
        assert len(alerts) == 0
