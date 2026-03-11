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
) -> dict:
    snapshot = store.load_all()
    events = snapshot["events"]
    analyses = snapshot["analyses"]
    new_events = 0
    analyzed_events = 0
    failed_events = 0
    total_sources = len(repos) + len(feeds)
    completed_sources = 0

    for repo in repos:
        if progress_callback is not None:
            progress_callback(
                phase="incremental",
                message="正在抓取 GitHub releases",
                current_label=repo,
                processed_sources=completed_sources,
                total_sources=total_sources,
                new_events=new_events,
                analyzed_events=analyzed_events,
                failed_events=failed_events,
            )
        for payload in release_fetcher(repo):
            event = normalize_release_event(repo, payload)
            if event["id"] not in events:
                new_events += 1
            if should_analyze_event(event, events, analyses):
                try:
                    analysis_event = event_enricher(event) if event_enricher else event
                    analyses[event["id"]] = analyzer(analysis_event)
                    analyzed_events += 1
                except Exception:
                    failed_events += 1
            events[event["id"]] = event
        completed_sources += 1

    for feed in feeds:
        if progress_callback is not None:
            progress_callback(
                phase="incremental",
                message="正在抓取文档来源",
                current_label=feed.get("name") or feed.get("id", ""),
                processed_sources=completed_sources,
                total_sources=total_sources,
                new_events=new_events,
                analyzed_events=analyzed_events,
                failed_events=failed_events,
            )
        for payload in feed_fetcher(feed):
            event = normalize_feed_entry(feed["id"], payload)
            if event["id"] not in events:
                new_events += 1
            if should_analyze_event(event, events, analyses):
                try:
                    analysis_event = event_enricher(event) if event_enricher else event
                    analyses[event["id"]] = analyzer(analysis_event)
                    analyzed_events += 1
                except Exception:
                    failed_events += 1
            events[event["id"]] = event
        completed_sources += 1

    if progress_callback is not None:
        progress_callback(
            phase="incremental",
            message="增量抓取与分析完成",
            current_label="",
            processed_sources=completed_sources,
            total_sources=total_sources,
            new_events=new_events,
            analyzed_events=analyzed_events,
            failed_events=failed_events,
        )

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
