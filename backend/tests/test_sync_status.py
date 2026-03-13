from threading import Event
from time import sleep


def test_sync_status_endpoint_reports_idle_by_default(tmp_path):
    from backend.app import create_app
    from backend.storage import JsonStore

    app = create_app(store=JsonStore(tmp_path), sync_runner=lambda **_kwargs: {"status": "noop"})
    client = app.test_client()

    payload = client.get("/api/sync/status").get_json()

    assert payload["status"] == "idle"
    assert payload["phase"] == "idle"


def test_manual_sync_runs_in_background_and_updates_status(tmp_path):
    from backend.app import create_app
    from backend.storage import JsonStore

    unblock = Event()

    def fake_incremental_runner(*, progress_callback=None):
        if progress_callback is not None:
            progress_callback(
                phase="incremental",
                message="正在抓取 GitHub releases",
                current_label="cilium/cilium",
                processed_sources=1,
                total_sources=8,
                new_events=2,
                analyzed_events=1,
                failed_events=0,
            )
        unblock.wait(timeout=5)
        return {"new_events": 2, "analyzed_events": 1, "failed_events": 0}

    def fake_digest_runner(*, progress_callback=None):
        if progress_callback is not None:
            progress_callback(
                phase="daily_digest",
                message="正在生成今日日报",
                current_label="8 个项目",
                processed_sources=8,
                total_sources=8,
            )
        return {"summary_date": "2026-03-11", "summary_count": 8}

    app = create_app(store=JsonStore(tmp_path), sync_runner=fake_incremental_runner, daily_digest_runner=fake_digest_runner)
    client = app.test_client()

    response = client.post("/api/sync")
    started = response.get_json()

    assert response.status_code == 202
    assert started["status"] == "running"

    running = client.get("/api/sync/status").get_json()
    assert running["phase"] == "incremental"
    assert running["current_label"] == "cilium/cilium"
    assert running["processed_sources"] == 1

    unblock.set()
    for _ in range(20):
        payload = client.get("/api/sync/status").get_json()
        if payload["status"] == "success":
            break
        sleep(0.1)
    else:
        raise AssertionError("sync did not finish in time")

    assert payload["phase"] == "completed"
    assert payload["result"]["incremental"]["new_events"] == 2
    assert payload["result"]["daily_digest"]["summary_count"] == 8


def test_manual_sync_updates_run_id(tmp_path):
    from backend.app import create_app
    from backend.storage import JsonStore

    app = create_app(store=JsonStore(tmp_path), sync_runner=lambda **_kwargs: {"status": "noop"})
    client = app.test_client()

    response = client.post("/api/sync")

    assert response.status_code == 202
    payload = response.get_json()
    assert payload.get("run_id")
