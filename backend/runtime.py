from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from .daily_summary import build_daily_project_summaries, merge_daily_project_summaries
from .digest_history import build_daily_digest_history
from .config import load_environment
from .llm import analyze_event, summarize_project_daily_intel
from .projects import collect_project_sources
from .research import enrich_event_for_analysis
from .sources import fetch_feed_entries, fetch_github_releases
from .sync import run_sync_once

LOCAL_TIMEZONE = ZoneInfo("Asia/Shanghai")


def build_sync_runner(store, now_provider=None):
    return build_incremental_sync_runner(store, now_provider=now_provider)


def build_incremental_sync_runner(store, now_provider=None):
    load_environment()

    def _now_iso() -> str:
        if now_provider is not None:
            return now_provider()
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _run(*, progress_callback=None, run_logger=None, run_id=None):
        now_iso = _now_iso()
        snapshot = store.load_all()
        config = snapshot.get("config") or {}
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
            progress_callback=progress_callback,
            run_logger=run_logger,
            run_id=run_id,
            max_workers=config.get("sync_concurrency", 4),
            source_timeout_seconds=config.get("sync_source_timeout_seconds", 120),
        )
        _update_incremental_state(store=store, now_iso=now_iso, analyzed_events=result["analyzed_events"])
        return result

    return _run


def build_daily_digest_runner(store, now_provider=None):
    load_environment()

    def _now_iso() -> str:
        if now_provider is not None:
            return now_provider()
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _run(*, progress_callback=None, run_logger=None, run_id=None):
        now_iso = _now_iso()
        summary_date = datetime.fromisoformat(now_iso.replace("Z", "+00:00")).astimezone(LOCAL_TIMEZONE).date().isoformat()
        snapshot = store.load_all()
        config = snapshot.get("config") or {}
        repos, feeds = collect_project_sources(snapshot["projects"], snapshot["crawl_profiles"])
        if feeds:
            run_sync_once(
                store=store,
                repos=[],
                feeds=feeds,
                release_fetcher=fetch_github_releases,
                feed_fetcher=fetch_feed_entries,
                analyzer=analyze_event,
                event_enricher=enrich_event_for_analysis,
                now_iso=now_iso,
                progress_callback=progress_callback,
                run_logger=run_logger,
                run_id=run_id,
                max_workers=config.get("sync_concurrency", 4),
                source_timeout_seconds=config.get("sync_source_timeout_seconds", 120),
            )
            snapshot = store.load_all()
        if progress_callback is not None:
            progress_callback(
                phase="daily_digest",
                message="正在整理今日日报",
                current_label=f"{len(snapshot.get('projects') or [])} 个项目",
                processed_sources=0,
                total_sources=len(snapshot.get("projects") or []),
            )
        summaries = build_daily_project_summaries(
            snapshot=snapshot,
            summary_date=summary_date,
            now_iso=now_iso,
            summarizer=summarize_project_daily_intel,
        )
        merged = merge_daily_project_summaries(snapshot.get("daily_project_summaries"), summaries)
        store.save_daily_project_summaries(merged)

        state = snapshot.get("state") or {}
        state["last_daily_digest_at"] = now_iso
        state["last_daily_summary_at"] = now_iso
        state["last_heartbeat_at"] = now_iso
        store.save_state(state)

        return {
            "summary_date": summary_date,
            "summary_count": len(summaries),
            "history_count": len(build_daily_digest_history(merged)),
        }

    return _run


def _update_incremental_state(*, store, now_iso: str, analyzed_events: int) -> None:
    snapshot = store.load_all()
    state = snapshot.get("state") or {}
    state["last_fetch_success_at"] = now_iso
    state["last_sync_at"] = now_iso
    state["last_heartbeat_at"] = now_iso
    if analyzed_events > 0:
        state["last_incremental_analysis_at"] = now_iso
        state["last_analysis_at"] = now_iso
    store.save_state(state)
