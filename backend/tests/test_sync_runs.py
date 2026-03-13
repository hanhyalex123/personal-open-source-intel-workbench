from pathlib import Path

from backend.storage import JsonStore
from backend.sync_runs import SyncRunRecorder, load_runs, save_runs


def test_sync_runs_round_trip(tmp_path: Path):
    store = JsonStore(tmp_path)
    save_runs(store, {"runs": []})
    assert load_runs(store)["runs"] == []


def test_sync_run_recorder_appends_and_trims(tmp_path: Path):
    store = JsonStore(tmp_path)
    recorder = SyncRunRecorder(store, retention=2)

    run1 = recorder.start_run(run_kind="manual", started_at="2026-03-13T00:00:00Z")
    run2 = recorder.start_run(run_kind="manual", started_at="2026-03-13T01:00:00Z")
    run3 = recorder.start_run(run_kind="manual", started_at="2026-03-13T02:00:00Z")

    runs = load_runs(store)["runs"]
    assert len(runs) == 2
    assert runs[0]["id"] == run3
    assert runs[1]["id"] == run2
