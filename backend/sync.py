from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from collections.abc import Callable
import inspect
from time import monotonic

from .normalize import normalize_feed_entry, normalize_release_event, should_analyze_event


def run_sync_once(
    *,
    store,
    repos: list[str],
    feeds: list[dict],
    release_fetcher: Callable[[str], list[dict]],
    feed_fetcher: Callable[[dict], list[dict]],
    analyzer: Callable[[dict], dict],
    event_enricher: Callable[[dict], dict] | None = None,
    now_iso: str,
    progress_callback: Callable[..., None] | None = None,
    max_workers: int = 1,
    source_timeout_seconds: float | None = None,
    run_logger=None,
    run_id: str | None = None,
) -> dict:
    snapshot = store.load_all()
    events = snapshot["events"]
    analyses = snapshot["analyses"]
    new_events = 0
    analyzed_events = 0
    failed_events = 0
    skipped_events = 0
    total_sources = len(repos) + len(feeds)
    completed_sources = 0

    def emit_progress(*, message: str, current_label: str = "") -> None:
        if progress_callback is not None:
            progress_callback(
                phase="incremental",
                message=message,
                current_label=current_label,
                processed_sources=completed_sources,
                total_sources=total_sources,
                new_events=new_events,
                analyzed_events=analyzed_events,
                failed_events=failed_events,
                skipped_events=skipped_events,
            )

    def process_repo(repo: str) -> dict:
        local_events = {}
        local_analyses = {}
        event_logs = []
        local_new_events = 0
        local_analyzed_events = 0
        local_failed_events = 0
        local_skipped_events = 0
        repo_label = repo

        def on_repo_progress(*, stage=None, processed_items=None, total_items=None, **_kwargs):
            if progress_callback is None:
                return
            label = repo_label
            if stage == "requesting":
                label = f"{repo_label} · 正在请求 GitHub releases"
            elif stage == "processing" and processed_items is not None and total_items is not None:
                label = f"{repo_label} · {processed_items} / {total_items} 条 release"
            progress_callback(
                phase="incremental",
                message="正在抓取 GitHub releases",
                current_label=label,
                processed_sources=completed_sources,
                total_sources=total_sources,
                new_events=new_events,
                analyzed_events=analyzed_events,
                failed_events=failed_events,
                skipped_events=skipped_events,
            )

        fetched_payloads = _call_with_optional_progress(release_fetcher, repo, on_repo_progress)

        for payload in fetched_payloads:
            event = normalize_release_event(repo, payload)
            is_new = event["id"] not in events and event["id"] not in local_events
            if is_new:
                local_new_events += 1
            if should_analyze_event(event, events | local_events, analyses | local_analyses):
                try:
                    analysis_event = event_enricher(event) if event_enricher else event
                    analysis = analyzer(analysis_event)
                    local_analyses[event["id"]] = analysis
                    local_analyzed_events += 1
                    llm_fields = _llm_log_fields(analysis.get("_llm", {}))
                    event_logs.append(
                        {
                            "event_id": event["id"],
                            "title": event.get("title", ""),
                            "version": event.get("version", ""),
                            "url": event.get("url", ""),
                            "published_at": event.get("published_at"),
                            "status": "analyzed",
                            "is_new": is_new,
                            "analysis": {
                                "title_zh": analysis.get("title_zh", ""),
                                "summary_zh": analysis.get("summary_zh", ""),
                                "urgency": analysis.get("urgency", "low"),
                                "action_items": analysis.get("action_items", []),
                            },
                            "error": None,
                            **llm_fields,
                        }
                    )
                except Exception as exc:
                    local_failed_events += 1
                    llm_fields = _llm_log_fields(exc)
                    event_logs.append(
                        {
                            "event_id": event["id"],
                            "title": event.get("title", ""),
                            "version": event.get("version", ""),
                            "url": event.get("url", ""),
                            "published_at": event.get("published_at"),
                            "status": "failed",
                            "is_new": is_new,
                            "analysis": None,
                            "error": str(exc),
                            **llm_fields,
                        }
                    )
            else:
                local_skipped_events += 1
                event_logs.append(
                    {
                        "event_id": event["id"],
                        "title": event.get("title", ""),
                        "version": event.get("version", ""),
                        "url": event.get("url", ""),
                        "published_at": event.get("published_at"),
                        "status": "skipped",
                        "is_new": is_new,
                        "analysis": None,
                        "error": None,
                    }
                )
            local_events[event["id"]] = event

        return {
            "message": "正在抓取 GitHub releases",
            "label": repo,
            "events": local_events,
            "analyses": local_analyses,
            "event_logs": event_logs,
            "new_events": local_new_events,
            "analyzed_events": local_analyzed_events,
            "failed_events": local_failed_events,
            "skipped_events": local_skipped_events,
        }

    def process_feed(feed: dict) -> dict:
        local_events = {}
        local_analyses = {}
        event_logs = []
        local_new_events = 0
        local_analyzed_events = 0
        local_failed_events = 0
        local_skipped_events = 0
        feed_label = feed.get("name") or feed.get("id", "")

        def on_feed_progress(*, current_url=None, processed_pages=None, max_pages=None, **_kwargs):
            if progress_callback is None or processed_pages is None:
                return
            label = feed_label
            if max_pages:
                label = f"{feed_label} · {processed_pages} / {max_pages} 页"
            progress_callback(
                phase="incremental",
                message="正在抓取文档来源",
                current_label=label,
                processed_sources=completed_sources,
                total_sources=total_sources,
                new_events=new_events,
                analyzed_events=analyzed_events,
                failed_events=failed_events,
                skipped_events=skipped_events,
            )

        fetched_payloads = _call_with_optional_progress(feed_fetcher, feed, on_feed_progress)

        for payload in fetched_payloads:
            event = normalize_feed_entry(feed["id"], payload)
            is_new = event["id"] not in events and event["id"] not in local_events
            if is_new:
                local_new_events += 1
            if should_analyze_event(event, events | local_events, analyses | local_analyses):
                try:
                    analysis_event = event_enricher(event) if event_enricher else event
                    analysis = analyzer(analysis_event)
                    local_analyses[event["id"]] = analysis
                    local_analyzed_events += 1
                    llm_fields = _llm_log_fields(analysis.get("_llm", {}))
                    event_logs.append(
                        {
                            "event_id": event["id"],
                            "title": event.get("title", ""),
                            "version": event.get("version", ""),
                            "url": event.get("url", ""),
                            "published_at": event.get("published_at"),
                            "status": "analyzed",
                            "is_new": is_new,
                            "analysis": {
                                "title_zh": analysis.get("title_zh", ""),
                                "summary_zh": analysis.get("summary_zh", ""),
                                "urgency": analysis.get("urgency", "low"),
                                "action_items": analysis.get("action_items", []),
                            },
                            "error": None,
                            **llm_fields,
                        }
                    )
                except Exception as exc:
                    local_failed_events += 1
                    llm_fields = _llm_log_fields(exc)
                    event_logs.append(
                        {
                            "event_id": event["id"],
                            "title": event.get("title", ""),
                            "version": event.get("version", ""),
                            "url": event.get("url", ""),
                            "published_at": event.get("published_at"),
                            "status": "failed",
                            "is_new": is_new,
                            "analysis": None,
                            "error": str(exc),
                            **llm_fields,
                        }
                    )
            else:
                local_skipped_events += 1
                event_logs.append(
                    {
                        "event_id": event["id"],
                        "title": event.get("title", ""),
                        "version": event.get("version", ""),
                        "url": event.get("url", ""),
                        "published_at": event.get("published_at"),
                        "status": "skipped",
                        "is_new": is_new,
                        "analysis": None,
                        "error": None,
                    }
                )
            local_events[event["id"]] = event

        return {
            "message": "正在抓取文档来源",
            "label": feed_label,
            "events": local_events,
            "analyses": local_analyses,
            "event_logs": event_logs,
            "new_events": local_new_events,
            "analyzed_events": local_analyzed_events,
            "failed_events": local_failed_events,
            "skipped_events": local_skipped_events,
        }

    sources = [("repo", repo) for repo in repos] + [("feed", feed) for feed in feeds]

    if total_sources:
        emit_progress(message="同步任务已开始")

    executor = ThreadPoolExecutor(max_workers=max(1, max_workers))
    future_map = {
        (
            executor.submit(process_repo, source) if kind == "repo" else executor.submit(process_feed, source)
        ): {
            "kind": kind,
            "label": source if kind == "repo" else source.get("name") or source.get("id", ""),
            "url": f"https://github.com/{source}" if kind == "repo" else source.get("url", ""),
        }
        for kind, source in sources
    }
    deadlines = {future: None if source_timeout_seconds is None else monotonic() + source_timeout_seconds for future in future_map}
    pending = set(future_map)

    try:
        while pending:
            if source_timeout_seconds is None:
                done, _ = wait(pending, return_when=FIRST_COMPLETED)
            else:
                next_deadline = min(deadlines[future] for future in pending if deadlines[future] is not None)
                timeout = max(0, next_deadline - monotonic())
                done, _ = wait(pending, timeout=timeout, return_when=FIRST_COMPLETED)

            if not done:
                now = monotonic()
                expired = [future for future in pending if deadlines[future] is not None and deadlines[future] <= now]
                for future in expired:
                    pending.remove(future)
                    failed_events += 1
                    completed_sources += 1
                    meta = future_map[future]
                    emit_progress(message=f'{meta["label"]} 抓取超时', current_label=meta["label"])
                    if run_logger is not None and run_id:
                        run_logger.record_source(
                            run_id,
                            {
                                "kind": "repo" if meta["kind"] == "repo" else "docs",
                                "label": meta["label"],
                                "url": meta.get("url", ""),
                                "status": "timeout",
                                "metrics": {"new_events": 0, "analyzed_events": 0, "failed_events": 1, "skipped_events": 0},
                                "error": "source timeout",
                                "events": [],
                            },
                        )
                continue

            for future in done:
                pending.remove(future)
                meta = future_map[future]
                try:
                    result = future.result()
                except Exception as exc:
                    failed_events += 1
                    completed_sources += 1
                    emit_progress(message=f'{meta["label"]} 抓取失败', current_label=meta["label"])
                    if run_logger is not None and run_id:
                        run_logger.record_source(
                            run_id,
                            {
                                "kind": "repo" if meta["kind"] == "repo" else "docs",
                                "label": meta["label"],
                                "url": meta.get("url", ""),
                                "status": "failed",
                                "metrics": {"new_events": 0, "analyzed_events": 0, "failed_events": 1, "skipped_events": 0},
                                "error": str(exc),
                                "events": [],
                            },
                        )
                    continue

                events.update(result["events"])
                analyses.update(result["analyses"])
                new_events += result["new_events"]
                analyzed_events += result["analyzed_events"]
                failed_events += result["failed_events"]
                skipped_events += result["skipped_events"]
                completed_sources += 1
                emit_progress(message=result["message"], current_label=result["label"])
                if run_logger is not None and run_id:
                    run_logger.record_source(
                        run_id,
                        {
                            "kind": "repo" if meta["kind"] == "repo" else "docs",
                            "label": result["label"],
                            "url": meta.get("url", ""),
                            "status": "failed" if result["failed_events"] else "success",
                            "metrics": {
                                "new_events": result["new_events"],
                                "analyzed_events": result["analyzed_events"],
                                "failed_events": result["failed_events"],
                                "skipped_events": result["skipped_events"],
                            },
                            "error": None,
                            "events": result.get("event_logs", []),
                        },
                    )
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    emit_progress(message="增量抓取与分析完成")

    state = snapshot["state"]
    state["last_sync_at"] = now_iso
    if analyzed_events > 0:
        state["last_analysis_at"] = now_iso

    store.save_state(state)
    store._write_json(store.events_path, events)
    store._write_json(store.analyses_path, analyses)

    return {
        "new_events": new_events,
        "analyzed_events": analyzed_events,
        "failed_events": failed_events,
        "skipped_events": skipped_events,
        "last_sync_at": now_iso,
    }


def _call_with_optional_progress(fetcher, source, progress_callback):
    if "progress_callback" in inspect.signature(fetcher).parameters:
        return fetcher(source, progress_callback=progress_callback)
    return fetcher(source)


def _llm_log_fields(source) -> dict:
    if isinstance(source, dict):
        return {
            "error_kind": source.get("error_kind"),
            "provider": source.get("provider"),
            "model": source.get("model"),
            "used_fallback": source.get("used_fallback", False),
            "fallback_provider": source.get("fallback_provider") or source.get("fallback_from_provider"),
            "fallback_model": source.get("fallback_model") or source.get("fallback_from_model"),
        }

    return {
        "error_kind": getattr(source, "error_kind", None),
        "provider": getattr(source, "provider", None),
        "model": getattr(source, "model", None),
        "used_fallback": getattr(source, "used_fallback", False),
        "fallback_provider": getattr(source, "fallback_provider", None),
        "fallback_model": getattr(source, "fallback_model", None),
    }
