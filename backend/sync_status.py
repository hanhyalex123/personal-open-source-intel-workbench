from copy import deepcopy
from datetime import UTC, datetime
import inspect
from threading import Event, Lock, Thread

STALL_HEARTBEAT_SECONDS = 90


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
        "skipped_events": 0,
        "error": "",
        "result": {},
    }


class SyncCoordinator:
    def __init__(self, incremental_runner, daily_digest_runner, store=None, heartbeat_interval_seconds: float = 15.0):
        self.incremental_runner = incremental_runner
        self.daily_digest_runner = daily_digest_runner
        self.store = store
        self._recorder = None
        self._lock = Lock()
        self._status = default_sync_status()
        self._first_progress_event = None
        self._heartbeat_interval_seconds = heartbeat_interval_seconds
        self._heartbeat_stop = Event()
        self._heartbeat_thread = None

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

    @staticmethod
    def _runner_supports(runner, name: str) -> bool:
        try:
            params = inspect.signature(runner).parameters
        except (TypeError, ValueError):
            return False
        for param in params.values():
            if param.kind == param.VAR_KEYWORD:
                return True
        return name in params

    def _invoke_runner(self, runner, *, progress_callback=None, run_logger=None, run_id=None):
        kwargs = {}
        if progress_callback is not None and self._runner_supports(runner, "progress_callback"):
            kwargs["progress_callback"] = progress_callback
        if run_logger is not None and run_id and self._runner_supports(runner, "run_logger"):
            kwargs["run_logger"] = run_logger
        if run_id and self._runner_supports(runner, "run_id"):
            kwargs["run_id"] = run_id
        return runner(**kwargs)

    def get_status(self) -> dict:
        with self._lock:
            status = deepcopy(self._status)
        status["heartbeat_age_seconds"] = _heartbeat_age_seconds(status.get("last_heartbeat_at"))
        status["is_stalled"] = bool(
            status.get("status") == "running"
            and status["heartbeat_age_seconds"] is not None
            and status["heartbeat_age_seconds"] >= STALL_HEARTBEAT_SECONDS
        )
        return status

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

        self._update_run_record(initial_status, initial_status)
        self._start_heartbeat_ticker()
        progress_event = Event()
        self._first_progress_event = progress_event
        Thread(target=self._run_manual_sync, daemon=True).start()
        progress_event.wait(timeout=0.1)
        self._first_progress_event = None
        return True, deepcopy(initial_status)

    def run_scheduled_incremental(self) -> dict:
        started_at = now_iso()
        run_id = self._start_run("scheduled-incremental", started_at=started_at)
        self._set_status(
            status="running",
            run_kind="scheduled-incremental",
            run_id=run_id,
            phase="incremental",
            message="定时增量同步中",
            started_at=started_at,
            finished_at=None,
            error="",
        )
        try:
            result = self._invoke_runner(
                self.incremental_runner,
                progress_callback=self._progress_callback,
                run_logger=self._ensure_recorder(),
                run_id=run_id,
            )
            self._set_status(
                status="success",
                phase="completed",
                message="定时增量同步完成",
                finished_at=now_iso(),
                result={"incremental": result},
            )
            return result
        except Exception as error:
            self._set_status(
                status="failed",
                phase="failed",
                message="定时增量同步失败",
                finished_at=now_iso(),
                error=str(error),
            )
            raise

    def run_scheduled_digest(self) -> dict:
        started_at = now_iso()
        run_id = self._start_run("scheduled-digest", started_at=started_at)
        self._set_status(
            status="running",
            run_kind="scheduled-digest",
            run_id=run_id,
            phase="daily_digest",
            message="定时日报生成中",
            started_at=started_at,
            finished_at=None,
            error="",
        )
        try:
            result = self._invoke_runner(
                self.daily_digest_runner,
                progress_callback=self._progress_callback,
                run_logger=self._ensure_recorder(),
                run_id=run_id,
            )
            self._set_status(
                status="success",
                phase="completed",
                message="定时日报生成完成",
                finished_at=now_iso(),
                result={"daily_digest": result},
            )
            return result
        except Exception as error:
            self._set_status(
                status="failed",
                phase="failed",
                message="定时日报生成失败",
                finished_at=now_iso(),
                error=str(error),
            )
            raise

    def _run_manual_sync(self) -> None:
        incremental_result = {}
        daily_digest_result = {}
        run_id = self._status.get("run_id")
        run_logger = self._ensure_recorder()

        try:
            self._set_status(phase="incremental", message="正在抓取并分析项目更新")
            incremental_result = self._invoke_runner(
                self.incremental_runner,
                progress_callback=self._progress_callback,
                run_logger=run_logger,
                run_id=run_id,
            )
            self._set_status(
                phase="daily_digest",
                message="正在生成今日日报",
                result={"incremental": incremental_result},
            )
            daily_digest_result = self._invoke_runner(
                self.daily_digest_runner,
                progress_callback=self._progress_callback,
                run_logger=run_logger,
                run_id=run_id,
            )
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
        if self._first_progress_event is not None:
            self._first_progress_event.set()

    def _set_status(self, **updates) -> None:
        with self._lock:
            next_status = dict(self._status)
            next_status.update(updates)
            if next_status.get("status") != "running" and next_status.get("finished_at") is None:
                next_status["finished_at"] = now_iso()
            self._status = next_status

        self._update_run_record(next_status, updates)
        self._refresh_heartbeat_ticker(next_status)

    def _refresh_heartbeat_ticker(self, status: dict) -> None:
        if status.get("status") == "running":
            self._start_heartbeat_ticker()
        else:
            self._stop_heartbeat_ticker()

    def _start_heartbeat_ticker(self) -> None:
        if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
            return
        self._heartbeat_stop.clear()
        self._heartbeat_thread = Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def _stop_heartbeat_ticker(self) -> None:
        self._heartbeat_stop.set()

    def _heartbeat_loop(self) -> None:
        while not self._heartbeat_stop.wait(self._heartbeat_interval_seconds):
            with self._lock:
                if self._status.get("status") != "running":
                    break
            self._set_status(last_heartbeat_at=now_iso())

    def _update_run_record(self, next_status: dict, updates: dict) -> None:
        run_id = next_status.get("run_id")
        if not run_id:
            return
        recorder = self._ensure_recorder()
        if recorder is None:
            return
        metrics = {}
        if "total_sources" in updates:
            metrics["total_sources"] = next_status.get("total_sources")
        recorder.update_run(
            run_id,
            status=next_status.get("status"),
            run_kind=next_status.get("run_kind"),
            phase=next_status.get("phase"),
            message=next_status.get("message"),
            started_at=next_status.get("started_at"),
            finished_at=next_status.get("finished_at"),
            last_heartbeat_at=next_status.get("last_heartbeat_at"),
            error=next_status.get("error"),
            metrics=metrics or None,
        )


def _heartbeat_age_seconds(last_heartbeat_at: str | None) -> int | None:
    if not last_heartbeat_at:
        return None
    heartbeat_at = datetime.fromisoformat(last_heartbeat_at.replace("Z", "+00:00"))
    current = datetime.fromisoformat(now_iso().replace("Z", "+00:00"))
    return max(0, int((current - heartbeat_at).total_seconds()))
