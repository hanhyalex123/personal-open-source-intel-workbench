import threading
from datetime import UTC, datetime


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_runs(store) -> dict:
    return store.load_sync_runs()


def save_runs(store, payload: dict) -> None:
    store.save_sync_runs(payload)


class SyncRunRecorder:
    def __init__(self, store, retention: int = 20):
        self.store = store
        self.retention = retention
        self._lock = threading.Lock()

    def start_run(self, *, run_kind: str, started_at: str | None = None) -> str:
        run_id = f"run_{(started_at or _now_iso())}_{run_kind}"
        now = started_at or _now_iso()
        run = {
            "id": run_id,
            "run_kind": run_kind,
            "status": "running",
            "phase": "queued",
            "message": "",
            "started_at": now,
            "finished_at": None,
            "last_heartbeat_at": now,
            "metrics": {
                "total_sources": 0,
                "processed_sources": 0,
                "new_events": 0,
                "analyzed_events": 0,
                "failed_events": 0,
            },
            "sources": [],
        }
        with self._lock:
            payload = load_runs(self.store)
            runs = payload.get("runs", [])
            runs.insert(0, run)
            payload["runs"] = runs[: self.retention]
            save_runs(self.store, payload)
        return run_id

    def update_run(self, run_id: str, **updates) -> None:
        with self._lock:
            payload = load_runs(self.store)
            for run in payload.get("runs", []):
                if run.get("id") == run_id:
                    metrics_update = updates.get("metrics")
                    if metrics_update is not None:
                        metrics = run.setdefault("metrics", {})
                        metrics.update({key: value for key, value in metrics_update.items() if value is not None})
                    run.update(
                        {key: value for key, value in updates.items() if key != "metrics" and value is not None}
                    )
                    break
            save_runs(self.store, payload)

    def record_source(self, run_id: str, source: dict) -> None:
        with self._lock:
            payload = load_runs(self.store)
            for run in payload.get("runs", []):
                if run.get("id") == run_id:
                    run.setdefault("sources", []).append(source)
                    metrics = run.setdefault("metrics", {})
                    metrics["processed_sources"] = metrics.get("processed_sources", 0) + 1
                    metrics["new_events"] = metrics.get("new_events", 0) + source.get("metrics", {}).get(
                        "new_events", 0
                    )
                    metrics["analyzed_events"] = metrics.get("analyzed_events", 0) + source.get("metrics", {}).get(
                        "analyzed_events", 0
                    )
                    metrics["failed_events"] = metrics.get("failed_events", 0) + source.get("metrics", {}).get(
                        "failed_events", 0
                    )
                    break
            save_runs(self.store, payload)
