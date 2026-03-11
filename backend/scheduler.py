from atexit import register
from dataclasses import dataclass

from apscheduler.schedulers.background import BackgroundScheduler


@dataclass(slots=True)
class SchedulerStatus:
    running: bool = False
    interval_minutes: int = 60


def start_scheduler(*, interval_minutes: int, incremental_callback, daily_digest_callback, timezone: str = "Asia/Shanghai", daily_digest_hour: int = 8, daily_digest_minute: int = 0):
    scheduler = BackgroundScheduler(timezone=timezone)
    scheduler.add_job(incremental_callback, "interval", minutes=interval_minutes, id="dashboard-sync", replace_existing=True)
    scheduler.add_job(
        daily_digest_callback,
        "cron",
        hour=daily_digest_hour,
        minute=daily_digest_minute,
        id="daily-digest",
        replace_existing=True,
    )
    scheduler.start()
    register(lambda: scheduler.shutdown(wait=False))
    return scheduler
