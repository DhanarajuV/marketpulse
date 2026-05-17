import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "marketpulse.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            conviction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            target_1 REAL NOT NULL,
            target_2 REAL,
            target_3 REAL,
            time_stop_date TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            close_price REAL,
            close_date TEXT,
            return_pct REAL,
            reasoning TEXT,
            sector TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_time TEXT DEFAULT CURRENT_TIMESTAMP,
            signals_found INTEGER,
            duration_seconds REAL
        );
    """)
    conn.commit()
    conn.close()


def save_signal(signal: dict):
    """Save a new signal to the database."""
    conn = get_conn()
    time_stop = (datetime.now() + timedelta(days=signal["time_stop_days"])).isoformat()
    conn.execute("""
        INSERT INTO signals (ticker, signal_type, conviction, entry_price, stop_loss,
                            target_1, target_2, target_3, time_stop_date, reasoning, sector)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signal["ticker"], signal["signal_type"], signal["conviction"],
        signal["entry_price"], signal["stop_loss"],
        signal["target_1"], signal.get("target_2"), signal.get("target_3"),
        time_stop, str(signal["reasoning"]), signal["sector"],
    ))
    conn.commit()
    conn.close()


def get_active_signals() -> list[dict]:
    """Get all active (open) signals."""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM signals WHERE status = 'active'").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def close_signal(signal_id: int, close_price: float, status: str):
    """Close a signal (win, loss, or timeout)."""
    conn = get_conn()
    row = conn.execute("SELECT entry_price FROM signals WHERE id = ?", (signal_id,)).fetchone()
    if row:
        return_pct = (close_price / row["entry_price"] - 1) * 100
        conn.execute("""
            UPDATE signals SET status = ?, close_price = ?, close_date = ?, return_pct = ?
            WHERE id = ?
        """, (status, close_price, datetime.now().isoformat(), return_pct, signal_id))
        conn.commit()
    conn.close()


def get_signal_stats() -> dict:
    """Get win/loss statistics."""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM signals WHERE status != 'active'").fetchone()[0]
    wins = conn.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed_win'").fetchone()[0]
    losses = conn.execute("SELECT COUNT(*) FROM signals WHERE status = 'closed_loss'").fetchone()[0]
    conn.close()

    return {
        "total_closed": total,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / total if total > 0 else 0,
    }


# Initialize on import
init_db()
