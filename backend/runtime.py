from datetime import UTC, datetime

from .config import load_environment
from .daily_summary import build_daily_project_summaries, merge_daily_project_summaries
from .llm import analyze_event, summarize_project_daily_intel
from .projects import collect_project_sources
from .research import enrich_event_for_analysis
from .sources import fetch_feed_entries, fetch_github_releases
from .sync import run_sync_once


def build_sync_runner(store, now_provider=None):
    load_environment()

    def _now_iso() -> str:
        if now_provider is not None:
            return now_provider()
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _run():
        now_iso = _now_iso()
        snapshot = store.load_all()
        config = snapshot["config"]
        repos, feeds = collect_project_sources(snapshot["projects"], snapshot["crawl_profiles"])
        result = run_sync_once(
            store=store,
            repos=repos,
            feeds=feeds,
            release_fetcher=fetch_github_releases,
            feed_fetcher=fetch_feed_entries,
            analyzer=analyze_event,
            event_enricher=enrich_event_for_analysis,
            now_iso=now_iso,
        )
        _refresh_daily_summaries(store=store, now_iso=now_iso, should_use_llm=result["analyzed_events"] > 0)
        return result

    return _run


def _refresh_daily_summaries(*, store, now_iso: str, should_use_llm: bool) -> None:
    snapshot = store.load_all()
    summaries = build_daily_project_summaries(
        snapshot=snapshot,
        summary_date=now_iso[:10],
        now_iso=now_iso,
        summarizer=summarize_project_daily_intel if should_use_llm else None,
    )
    merged = merge_daily_project_summaries(snapshot.get("daily_project_summaries"), summaries)
    store.save_daily_project_summaries(merged)

    state = snapshot.get("state") or {}
    state["last_daily_summary_at"] = now_iso
    store.save_state(state)
