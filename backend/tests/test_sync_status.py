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
    assert "run_id" in payload


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


def test_heartbeat_ticker_updates_last_heartbeat():
    from backend.sync_status import SyncCoordinator

    blocker = Event()

    def slow_runner(**_kwargs):
        blocker.wait(timeout=2)
        return {}

    coordinator = SyncCoordinator(slow_runner, slow_runner, heartbeat_interval_seconds=0.1)
    ok, status = coordinator.start_manual_sync()
    assert ok
    first = status["last_heartbeat_at"]

    updated = False
    for _ in range(20):
        sleep(0.05)
        latest = coordinator.get_status()["last_heartbeat_at"]
        if latest != first:
            updated = True
            break

    blocker.set()
    assert updated
def test_manual_sync_updates_run_logs(tmp_path):
    from backend.app import create_app
    from backend.storage import JsonStore
    from backend.sync_runs import load_runs

    store = JsonStore(tmp_path)

    def fake_incremental_runner(*, progress_callback=None, run_logger=None, run_id=None):
        assert run_logger is not None
        assert run_id
        if progress_callback is not None:
            progress_callback(
                phase="incremental",
                message="正在抓取 GitHub releases",
                current_label="openclaw/openclaw",
                processed_sources=1,
                total_sources=2,
                new_events=1,
                analyzed_events=1,
                failed_events=0,
            )
        run_logger.record_source(
            run_id,
            {
                "kind": "repo",
                "label": "openclaw/openclaw",
                "url": "https://github.com/openclaw/openclaw",
                "status": "success",
                "metrics": {"new_events": 1, "analyzed_events": 1, "failed_events": 0},
                "error": None,
                "events": [],
            },
        )
        return {"new_events": 1, "analyzed_events": 1, "failed_events": 0}

    def fake_digest_runner(*, progress_callback=None, run_logger=None, run_id=None):
        if progress_callback is not None:
            progress_callback(
                phase="daily_digest",
                message="正在生成今日日报",
                current_label="2 个项目",
                processed_sources=2,
                total_sources=2,
            )
        return {"summary_date": "2026-03-13", "summary_count": 1}

    app = create_app(store=store, sync_runner=fake_incremental_runner, daily_digest_runner=fake_digest_runner)
    client = app.test_client()

    response = client.post("/api/sync")
    assert response.status_code == 202

    for _ in range(20):
        payload = client.get("/api/sync/status").get_json()
        if payload["status"] == "success":
            break
        sleep(0.1)
    else:
        raise AssertionError("sync did not finish in time")

    runs = load_runs(store)["runs"]
    assert runs
    run = runs[0]
    assert run["run_kind"] == "manual"
    assert run["status"] == "success"
    assert run["phase"] == "completed"
    assert run["metrics"]["total_sources"] == 2
    assert run["metrics"]["new_events"] == 1
    assert run["sources"][0]["label"] == "openclaw/openclaw"


def test_scheduled_incremental_marks_status_failed_on_exception(tmp_path):
    from backend.app import create_app
    from backend.storage import JsonStore

    def failing_runner(*, progress_callback=None):
        raise RuntimeError("boom")

    app = create_app(store=JsonStore(tmp_path), sync_runner=failing_runner)
    coordinator = app.config["SYNC_COORDINATOR"]

    try:
        coordinator.run_scheduled_incremental()
    except RuntimeError:
        pass

    status = coordinator.get_status()

    assert status["status"] == "failed"
    assert status["phase"] == "failed"
    assert status["error"] == "boom"


def test_sync_status_marks_running_job_stalled_when_heartbeat_too_old(tmp_path, monkeypatch):
    from backend.app import create_app
    from backend.storage import JsonStore

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
        return {"new_events": 2, "analyzed_events": 1, "failed_events": 0}

    app = create_app(store=JsonStore(tmp_path), sync_runner=fake_incremental_runner)
    coordinator = app.config["SYNC_COORDINATOR"]
    coordinator._set_status(
        status="running",
        run_kind="manual",
        phase="incremental",
        message="正在抓取 GitHub releases",
        started_at="2026-03-11T09:00:00Z",
        last_heartbeat_at="2026-03-11T09:00:00Z",
    )
    monkeypatch.setattr("backend.sync_status.now_iso", lambda: "2026-03-11T09:03:00Z")

    status = coordinator.get_status()

    assert status["is_stalled"] is True
    assert status["heartbeat_age_seconds"] == 180
