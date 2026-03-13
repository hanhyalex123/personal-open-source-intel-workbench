from collections.abc import Callable

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
    run_logger=None,
    run_id: str | None = None,
) -> dict:
    snapshot = store.load_all()
    events = snapshot["events"]
    analyses = snapshot["analyses"]
    new_events = 0
    analyzed_events = 0
    failed_events = 0
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
            )

    def record_source(*, kind: str, label: str, url: str, local_new: int, local_analyzed: int, local_failed: int, events):
        if run_logger is None or not run_id:
            return
        run_logger.record_source(
            run_id,
            {
                "kind": kind,
                "label": label,
                "url": url,
                "status": "failed" if local_failed else "success",
                "metrics": {
                    "new_events": local_new,
                    "analyzed_events": local_analyzed,
                    "failed_events": local_failed,
                },
                "error": None,
                "events": events,
            },
        )

    if total_sources:
        emit_progress(message="同步任务已开始")

    for repo in repos:
        emit_progress(message="正在抓取 GitHub releases", current_label=repo)
        local_events = {}
        local_analyses = {}
        event_logs = []
        local_new_events = 0
        local_analyzed_events = 0
        local_failed_events = 0

        for payload in release_fetcher(repo):
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
                        }
                    )
                except Exception as exc:
                    local_failed_events += 1
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
                        }
                    )
            else:
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

        events.update(local_events)
        analyses.update(local_analyses)
        new_events += local_new_events
        analyzed_events += local_analyzed_events
        failed_events += local_failed_events
        completed_sources += 1
        record_source(
            kind="repo",
            label=repo,
            url=f"https://github.com/{repo}",
            local_new=local_new_events,
            local_analyzed=local_analyzed_events,
            local_failed=local_failed_events,
            events=event_logs,
        )

    for feed in feeds:
        feed_label = feed.get("name") or feed.get("id", "")
        emit_progress(message="正在抓取文档来源", current_label=feed_label)
        local_events = {}
        local_analyses = {}
        event_logs = []
        local_new_events = 0
        local_analyzed_events = 0
        local_failed_events = 0

        for payload in feed_fetcher(feed):
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
                        }
                    )
                except Exception as exc:
                    local_failed_events += 1
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
                        }
                    )
            else:
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

        events.update(local_events)
        analyses.update(local_analyses)
        new_events += local_new_events
        analyzed_events += local_analyzed_events
        failed_events += local_failed_events
        completed_sources += 1
        record_source(
            kind="docs",
            label=feed_label,
            url=feed.get("url", ""),
            local_new=local_new_events,
            local_analyzed=local_analyzed_events,
            local_failed=local_failed_events,
            events=event_logs,
        )

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
        "last_sync_at": now_iso,
    }
