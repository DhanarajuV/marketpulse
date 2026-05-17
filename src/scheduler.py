"""MarketPulse Scheduler — runs scans at 8AM and 1PM EST, Monday-Friday."""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.scanner.run_scan import run_full_scan
from src.alerts.telegram import send_alert


def scheduled_scan():
    """Wrapper for scheduled execution."""
    try:
        run_full_scan()
    except Exception as e:
        send_alert(f"⚠️ *Scan Error*\n\n{str(e)[:500]}")
        print(f"ERROR: {e}")


def main():
    scheduler = BlockingScheduler()

    # 8AM EST, Monday-Friday
    scheduler.add_job(
        scheduled_scan,
        CronTrigger(hour=8, minute=0, day_of_week="mon-fri", timezone="US/Eastern"),
        id="morning_scan",
    )

    # 1PM EST, Monday-Friday
    scheduler.add_job(
        scheduled_scan,
        CronTrigger(hour=13, minute=0, day_of_week="mon-fri", timezone="US/Eastern"),
        id="afternoon_scan",
    )

    print("=" * 60)
    print("MARKETPULSE SCHEDULER RUNNING")
    print("=" * 60)
    print("\nScheduled scans:")
    print("  • 8:00 AM EST (Mon-Fri)")
    print("  • 1:00 PM EST (Mon-Fri)")
    print("\nPress Ctrl+C to stop.\n")

    send_alert("🟢 *MarketPulse Started*\n\nScheduler running. Scans at 8AM & 1PM EST.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler stopped.")
        send_alert("🔴 *MarketPulse Stopped*")


if __name__ == "__main__":
    main()
