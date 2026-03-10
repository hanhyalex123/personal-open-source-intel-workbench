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
) -> dict:
    snapshot = store.load_all()
    events = snapshot["events"]
    analyses = snapshot["analyses"]
    new_events = 0
    analyzed_events = 0
    failed_events = 0

    for repo in repos:
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

    for feed in feeds:
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
