from datetime import datetime
from src.storage.database import get_active_signals, close_signal
from src.alerts.telegram import send_alert


def check_active_positions(all_indicators: dict) -> list[dict]:
    """Check active signals for target hits, stop-losses, or time stops."""
    sell_alerts = []
    active = get_active_signals()

    for signal in active:
        ticker = signal["ticker"]
        if ticker not in all_indicators:
            continue

        current_price = all_indicators[ticker]["price"]
        entry = signal["entry_price"]
        return_pct = (current_price / entry - 1) * 100

        # Check stop-loss
        if current_price <= signal["stop_loss"]:
            close_signal(signal["signal_id"], current_price, "closed_loss")
            alert = {
                "ticker": ticker,
                "reason": "Stop-loss hit",
                "action": "EXIT ALL",
                "current_price": current_price,
                "entry_price": entry,
                "return_pct": return_pct,
            }
            sell_alerts.append(alert)
            msg = f"⛔ *STOP-LOSS* — {ticker}\n\nPrice: ${current_price:.2f} (stop was ${signal['stop_loss']})\nEntry: ${entry:.2f}\nLoss: {return_pct:.1f}%\n\n*ACTION: Exit entire position*"
            send_alert(msg)
            continue

        # Check target 1
        if current_price >= signal["target_1"] and signal["target_1"] > 0:
            alert = {
                "ticker": ticker,
                "reason": "Target 1 hit",
                "action": "Sell 1/3, move stop to breakeven",
                "current_price": current_price,
                "entry_price": entry,
                "return_pct": return_pct,
            }
            sell_alerts.append(alert)
            msg = f"🟢 *TARGET 1 HIT* — {ticker}\n\nPrice: ${current_price:.2f} (target was ${signal['target_1']})\nEntry: ${entry:.2f}\nGain: +{return_pct:.1f}%\n\n*ACTION: Sell 1/3, move stop to ${entry:.2f}*"
            send_alert(msg)

        # Check target 3 (full exit)
        if signal["target_3"] and current_price >= signal["target_3"]:
            close_signal(signal["signal_id"], current_price, "closed_win")
            msg = f"🔴 *TARGET 3 HIT* — {ticker}\n\nPrice: ${current_price:.2f}\nEntry: ${entry:.2f}\nGain: +{return_pct:.1f}%\n\n*ACTION: Exit remaining position* 🎉"
            send_alert(msg)

        # Check time stop
        if signal["time_stop_date"]:
            time_stop = datetime.fromisoformat(signal["time_stop_date"])
            if datetime.now() > time_stop:
                close_signal(signal["signal_id"], current_price, "closed_timeout")
                alert = {
                    "ticker": ticker,
                    "reason": "Time stop reached",
                    "action": "Exit at market",
                    "current_price": current_price,
                    "entry_price": entry,
                    "return_pct": return_pct,
                }
                sell_alerts.append(alert)
                msg = f"⏰ *TIME STOP* — {ticker}\n\nTime limit reached.\nPrice: ${current_price:.2f}\nEntry: ${entry:.2f}\nReturn: {return_pct:+.1f}%\n\n*ACTION: Exit at market*"
                send_alert(msg)

    return sell_alerts
