import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_alert(message: str):
    """Send a Telegram message to admin."""
    if not BOT_TOKEN or not CHAT_ID:
        print(f"[TELEGRAM DISABLED] {message[:100]}...")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"  ⚠️ Telegram error: {e}")


def format_signal(signal: dict) -> str:
    """Format a signal into a Telegram message."""
    emoji = {
        "panic_sell": "🚨",
        "short_squeeze": "🔥",
        "breakout": "📈",
        "news_catalyst": "📰",
    }.get(signal["signal_type"], "🎯")

    msg = f"""{emoji} *{signal['signal_type'].upper().replace('_', ' ')}* — {signal['ticker']} at ${signal['entry_price']}

*Conviction:* {signal['conviction']}
*Sector:* {signal['sector']}

*Why:*
"""
    for r in signal["reasoning"]:
        msg += f"  • {r}\n"

    msg += f"""
*Exit Targets:*
  🟢 T1: ${signal['target_1']}
  🟡 T2: ${signal['target_2']}
  🔴 T3: ${signal['target_3']}

*Risk:*
  ⛔ Stop-loss: ${signal['stop_loss']}
  ⏰ Time stop: {signal['time_stop_days']} days"""

    return msg


def format_no_signals() -> str:
    """Format a 'no signals' summary."""
    return "✅ *Market Scan Complete*\n\nNo actionable signals detected."


def send_scan_results(signals: list[dict]):
    """Send all signals (or no-signal summary) via Telegram."""
    if signals:
        for signal in signals:
            send_alert(format_signal(signal))
    else:
        send_alert(format_no_signals())
