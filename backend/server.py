from threading import Thread

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

    scheduler = start_scheduler(
        interval_minutes=interval_minutes,
        incremental_callback=coordinator.run_scheduled_incremental,
        daily_digest_callback=coordinator.run_scheduled_digest,
    )
    state = store.load_all()["state"]
    state["scheduler"] = {
        "running": True,
        "interval_minutes": interval_minutes,
        "timezone": "Asia/Shanghai",
        "jobs": {
            "incremental": {"enabled": True},
            "daily_digest": {"enabled": True, "hour": 8, "minute": 0},
        },
    }
    store.save_state(state)

    app.config["SCHEDULER"] = scheduler

    def run_initial_sync():
        try:
            coordinator.run_scheduled_incremental()
        except Exception as error:  # pragma: no cover
            print(f"initial sync failed: {error}")

    Thread(target=run_initial_sync, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=False)


if __name__ == "__main__":
    main()
