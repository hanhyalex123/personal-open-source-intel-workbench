from atexit import register
from dataclasses import dataclass

from apscheduler.schedulers.background import BackgroundScheduler


@dataclass(slots=True)
class SchedulerStatus:
    running: bool = False
    interval_minutes: int = 60


def start_scheduler(*, interval_minutes: int, callback):
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(callback, "interval", minutes=interval_minutes, id="dashboard-sync", replace_existing=True)
    scheduler.start()
    register(lambda: scheduler.shutdown(wait=False))
    return scheduler
