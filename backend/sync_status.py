from copy import deepcopy
from datetime import UTC, datetime
from threading import Lock, Thread


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_sync_status() -> dict:
    return {
        "run_id": None,
        "status": "idle",
        "run_kind": "",
        "phase": "idle",
        "message": "",
        "started_at": None,
        "finished_at": None,
        "last_heartbeat_at": None,
        "current_label": "",
        "processed_sources": 0,
        "total_sources": 0,
        "new_events": 0,
        "analyzed_events": 0,
        "failed_events": 0,
        "error": "",
        "result": {},
    }


class SyncCoordinator:
    def __init__(self, incremental_runner, daily_digest_runner, store=None):
        self.incremental_runner = incremental_runner
        self.daily_digest_runner = daily_digest_runner
        self.store = store
        self._recorder = None
        self._lock = Lock()
        self._status = default_sync_status()

    def _ensure_recorder(self):
        if self.store is None:
            return None
        if self._recorder is None:
            from .sync_runs import SyncRunRecorder

            self._recorder = SyncRunRecorder(self.store)
        return self._recorder

    def _start_run(self, run_kind: str, *, started_at: str | None = None) -> str | None:
        recorder = self._ensure_recorder()
        if recorder is None:
            return None
        return recorder.start_run(run_kind=run_kind, started_at=started_at)

    def get_status(self) -> dict:
        with self._lock:
            return deepcopy(self._status)

    def start_manual_sync(self) -> tuple[bool, dict]:
        with self._lock:
            if self._status["status"] == "running":
                return False, deepcopy(self._status)

            started_at = now_iso()
            run_id = self._start_run("manual", started_at=started_at)
            initial_status = {
                **default_sync_status(),
                "run_id": run_id,
                "status": "running",
                "run_kind": "manual",
                "phase": "queued",
                "message": "同步任务已开始",
                "started_at": started_at,
                "last_heartbeat_at": started_at,
            }
            self._status = initial_status

        Thread(target=self._run_manual_sync, daemon=True).start()
        return True, deepcopy(initial_status)

    def run_scheduled_incremental(self) -> dict:
        self._set_status(
            status="running",
            run_kind="scheduled-incremental",
            phase="incremental",
            message="定时增量同步中",
            started_at=now_iso(),
            finished_at=None,
            error="",
        )
        return self.incremental_runner(progress_callback=self._progress_callback)

    def run_scheduled_digest(self) -> dict:
        self._set_status(
            status="running",
            run_kind="scheduled-digest",
            phase="daily_digest",
            message="定时日报生成中",
            started_at=now_iso(),
            finished_at=None,
            error="",
        )
        try:
            result = self.daily_digest_runner(progress_callback=self._progress_callback)
            self._set_status(
                status="success",
                phase="completed",
                message="定时报摘要生成完成",
                finished_at=now_iso(),
                result={"daily_digest": result},
            )
            return result
        except Exception as error:
            self._set_status(
                status="failed",
                phase="failed",
                message="定时报摘要生成失败",
                finished_at=now_iso(),
                error=str(error),
            )
            raise

    def _run_manual_sync(self) -> None:
        incremental_result = {}
        daily_digest_result = {}

        try:
            self._set_status(phase="incremental", message="正在抓取并分析项目更新")
            incremental_result = self.incremental_runner(progress_callback=self._progress_callback)
            self._set_status(
                phase="daily_digest",
                message="正在生成今日日报",
                result={"incremental": incremental_result},
            )
            daily_digest_result = self.daily_digest_runner(progress_callback=self._progress_callback)
            self._set_status(
                status="success",
                phase="completed",
                message="同步完成",
                finished_at=now_iso(),
                result={"incremental": incremental_result, "daily_digest": daily_digest_result},
            )
        except Exception as error:
            self._set_status(
                status="failed",
                phase="failed",
                message="同步失败",
                finished_at=now_iso(),
                error=str(error),
                result={"incremental": incremental_result, "daily_digest": daily_digest_result},
            )

    def _progress_callback(self, **payload) -> None:
        update = {key: value for key, value in payload.items() if value is not None}
        update["last_heartbeat_at"] = now_iso()
        self._set_status(**update)

    def _set_status(self, **updates) -> None:
        with self._lock:
            next_status = dict(self._status)
            next_status.update(updates)
            if next_status.get("status") != "running" and next_status.get("finished_at") is None:
                next_status["finished_at"] = now_iso()
            self._status = next_status
