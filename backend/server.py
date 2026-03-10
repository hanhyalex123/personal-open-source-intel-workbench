from threading import Thread

from .app import create_app
from .config import DATA_DIR, load_environment
from .runtime import build_sync_runner
from .scheduler import start_scheduler
from .storage import JsonStore


def main():
    load_environment()
    store = JsonStore(DATA_DIR)
    sync_runner = build_sync_runner(store)
    snapshot = store.load_all()
    interval_minutes = snapshot["config"].get("sync_interval_minutes", 60)

    scheduler = start_scheduler(interval_minutes=interval_minutes, callback=sync_runner)
    state = store.load_all()["state"]
    state["scheduler"] = {"running": True, "interval_minutes": interval_minutes}
    store.save_state(state)

    app = create_app(store=store, sync_runner=sync_runner)
    app.config["SCHEDULER"] = scheduler

    def run_initial_sync():
        try:
            sync_runner()
        except Exception as error:  # pragma: no cover
            print(f"initial sync failed: {error}")

    Thread(target=run_initial_sync, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=False)


if __name__ == "__main__":
    main()
