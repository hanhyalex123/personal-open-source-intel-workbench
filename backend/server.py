from datetime import UTC, datetime
from threading import Thread
from zoneinfo import ZoneInfo

from .app import create_app
from .config import DATA_DIR, load_environment
from .runtime import build_daily_digest_runner, build_incremental_sync_runner
from .scheduler import start_scheduler
from .storage import JsonStore


def main():
    load_environment()
    store = JsonStore(DATA_DIR)
    sync_runner = build_incremental_sync_runner(store)
    daily_digest_runner = build_daily_digest_runner(store)
    app = create_app(store=store, sync_runner=sync_runner, daily_digest_runner=daily_digest_runner)
    coordinator = app.config["SYNC_COORDINATOR"]
    snapshot = store.load_all()
    interval_minutes = snapshot["config"].get("sync_interval_minutes", 60)
    state = snapshot.get("state") or {}
    digest_timezone, digest_hour, digest_minute = resolve_daily_digest_schedule(state=state)
    should_run_digest_catchup = should_run_startup_digest_catchup(
        state=state,
        now_iso=now_iso(),
        timezone=digest_timezone,
        daily_digest_hour=digest_hour,
        daily_digest_minute=digest_minute,
    )

    scheduler = start_scheduler(
        interval_minutes=interval_minutes,
        incremental_callback=coordinator.run_scheduled_incremental,
        daily_digest_callback=coordinator.run_scheduled_digest,
        timezone=digest_timezone,
        daily_digest_hour=digest_hour,
        daily_digest_minute=digest_minute,
    )
    state = store.load_all()["state"]
    state["scheduler"] = {
        "running": True,
        "interval_minutes": interval_minutes,
        "timezone": digest_timezone,
        "jobs": {
            "incremental": {"enabled": True},
            "daily_digest": {"enabled": True, "hour": digest_hour, "minute": digest_minute},
        },
    }
    store.save_state(state)

    app.config["SCHEDULER"] = scheduler

    def run_initial_sync():
        try:
            coordinator.run_scheduled_incremental()
        except Exception as error:  # pragma: no cover
            print(f"initial sync failed: {error}")
        if should_run_digest_catchup:
            try:
                coordinator.run_scheduled_digest()
            except Exception as error:  # pragma: no cover
                print(f"startup digest catch-up failed: {error}")

    Thread(target=run_initial_sync, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=False)


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_daily_digest_schedule(*, state: dict) -> tuple[str, int, int]:
    scheduler_state = (state or {}).get("scheduler") or {}
    jobs = scheduler_state.get("jobs") or {}
    digest_job = jobs.get("daily_digest") or {}
    timezone = scheduler_state.get("timezone") or "Asia/Shanghai"
    hour = _clamp_int(digest_job.get("hour"), minimum=0, maximum=23, default=8)
    minute = _clamp_int(digest_job.get("minute"), minimum=0, maximum=59, default=0)
    return timezone, hour, minute


def should_run_startup_digest_catchup(
    *,
    state: dict,
    now_iso: str,
    timezone: str,
    daily_digest_hour: int,
    daily_digest_minute: int,
) -> bool:
    try:
        local_timezone = ZoneInfo(timezone)
    except Exception:  # pragma: no cover
        local_timezone = ZoneInfo("Asia/Shanghai")

    now_local = datetime.fromisoformat(now_iso.replace("Z", "+00:00")).astimezone(local_timezone)
    scheduled_local = now_local.replace(hour=daily_digest_hour, minute=daily_digest_minute, second=0, microsecond=0)
    if now_local < scheduled_local:
        return False

    last_digest_iso = (state or {}).get("last_daily_digest_at")
    if not last_digest_iso:
        return True

    try:
        last_digest_local = datetime.fromisoformat(last_digest_iso.replace("Z", "+00:00")).astimezone(local_timezone)
    except ValueError:
        return True
    return last_digest_local.date() < now_local.date()


def _clamp_int(value, *, minimum: int, maximum: int, default: int) -> int:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, resolved))


if __name__ == "__main__":
    main()
