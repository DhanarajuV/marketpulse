"""Tests for SQLite database operations."""
import os
import sqlite3
from src.storage.database import init_db, save_signal, get_active_signals, close_signal, get_signal_stats, DB_PATH


class TestDatabase:
    def setup_method(self):
        """Reset DB before each test."""
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()

    def test_init_creates_tables(self):
        conn = sqlite3.connect(DB_PATH)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        conn.close()
        assert "signals" in table_names
        assert "users" in table_names
        assert "scan_logs" in table_names

    def test_save_and_get_signal(self):
        signal = {
            "ticker": "AAPL", "signal_type": "panic_sell", "conviction": "HIGH",
            "entry_price": 150.0, "stop_loss": 120.0,
            "target_1": 160.0, "target_2": 170.0, "target_3": 180.0,
            "time_stop_days": 14, "reasoning": ["test"], "sector": "tech",
        }
        save_signal(signal)
        active = get_active_signals()
        assert len(active) == 1
        assert active[0]["ticker"] == "AAPL"
        assert active[0]["status"] == "active"

    def test_close_signal_win(self):
        signal = {
            "ticker": "NVDA", "signal_type": "breakout", "conviction": "MEDIUM",
            "entry_price": 100.0, "stop_loss": 80.0,
            "target_1": 110.0, "target_2": 120.0, "target_3": 130.0,
            "time_stop_days": 30, "reasoning": ["test"], "sector": "semiconductors",
        }
        save_signal(signal)
        active = get_active_signals()
        close_signal(active[0]["id"], 115.0, "closed_win")

        active_after = get_active_signals()
        assert len(active_after) == 0

    def test_signal_stats(self):
        for i in range(3):
            save_signal({
                "ticker": f"T{i}", "signal_type": "test", "conviction": "HIGH",
                "entry_price": 100, "stop_loss": 80, "target_1": 110,
                "target_2": 120, "target_3": 130, "time_stop_days": 14,
                "reasoning": [], "sector": "tech",
            })

        active = get_active_signals()
        close_signal(active[0]["id"], 115.0, "closed_win")
        close_signal(active[1]["id"], 75.0, "closed_loss")

        stats = get_signal_stats()
        assert stats["total_closed"] == 2
        assert stats["wins"] == 1
        assert stats["losses"] == 1
        assert stats["win_rate"] == 0.5

    def test_empty_stats(self):
        stats = get_signal_stats()
        assert stats["total_closed"] == 0
        assert stats["win_rate"] == 0
