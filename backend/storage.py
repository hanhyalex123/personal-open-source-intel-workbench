import json
from pathlib import Path
from tempfile import NamedTemporaryFile

DEFAULT_ASSISTANT_CONFIG = {
    "enabled": True,
    "default_mode": "hybrid",
    "default_project_ids": [],
    "default_categories": [],
    "default_timeframe": "14d",
    "max_evidence_items": 3,
    "max_source_items": 4,
    "retrieval": {
        "release_weight": 1.0,
        "docs_weight": 1.2,
    },
    "live_search": {
        "enabled": True,
        "provider": "duckduckgo",
        "max_results": 5,
        "max_pages": 3,
    },
    "prompts": {
        "classification": "",
        "answer": "",
    },
}

DEFAULT_CONFIG = {
    "sync_interval_minutes": 60,
    "assistant": DEFAULT_ASSISTANT_CONFIG,
}

DEFAULT_STATE = {
    "last_sync_at": None,
    "last_analysis_at": None,
    "last_daily_summary_at": None,
    "last_fetch_success_at": None,
    "last_incremental_analysis_at": None,
    "last_daily_digest_at": None,
    "last_heartbeat_at": None,
    "scheduler": {
        "running": False,
        "interval_minutes": 60,
        "timezone": "Asia/Shanghai",
        "jobs": {
            "incremental": {"enabled": True},
            "daily_digest": {"enabled": True, "hour": 8, "minute": 0},
        },
    },
}


class JsonStore:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def config_path(self) -> Path:
        return self.base_dir / "config.json"

    @property
    def events_path(self) -> Path:
        return self.base_dir / "events.json"

    @property
    def analyses_path(self) -> Path:
        return self.base_dir / "analyses.json"

    @property
    def projects_path(self) -> Path:
        return self.base_dir / "projects.json"

    @property
    def crawl_profiles_path(self) -> Path:
        return self.base_dir / "crawl_profiles.json"

    @property
    def daily_project_summaries_path(self) -> Path:
        return self.base_dir / "daily_project_summaries.json"

    @property
    def state_path(self) -> Path:
        return self.base_dir / "state.json"

    def load_all(self) -> dict:
        return {
            "config": normalize_config(self._load_json(self.config_path, DEFAULT_CONFIG)),
            "events": self._load_json(self.events_path, {}),
            "analyses": self._load_json(self.analyses_path, {}),
            "projects": self._load_json(self.projects_path, []),
            "crawl_profiles": self._load_json(self.crawl_profiles_path, {}),
            "daily_project_summaries": self._load_json(self.daily_project_summaries_path, {}),
            "state": self._load_json(self.state_path, DEFAULT_STATE),
        }

    def save_event(self, event: dict) -> None:
        events = self._load_json(self.events_path, {})
        events[event["id"]] = event
        self._write_json(self.events_path, events)

    def save_analysis(self, event_id: str, analysis: dict) -> None:
        analyses = self._load_json(self.analyses_path, {})
        analyses[event_id] = analysis
        self._write_json(self.analyses_path, analyses)

    def save_state(self, state: dict) -> None:
        self._write_json(self.state_path, state)

    def save_config(self, config: dict) -> None:
        self._write_json(self.config_path, normalize_config(config))

    def save_project(self, project: dict) -> None:
        projects = self._load_json(self.projects_path, [])
        existing_index = next((index for index, item in enumerate(projects) if item["id"] == project["id"]), None)
        if existing_index is None:
            projects.append(project)
        else:
            projects[existing_index] = project
        self._write_json(self.projects_path, projects)

    def save_projects(self, projects: list[dict]) -> None:
        self._write_json(self.projects_path, projects)

    def save_crawl_profile(self, project_id: str, profile: dict) -> None:
        profiles = self._load_json(self.crawl_profiles_path, {})
        profiles[project_id] = profile
        self._write_json(self.crawl_profiles_path, profiles)

    def save_daily_project_summaries(self, summaries: dict) -> None:
        self._write_json(self.daily_project_summaries_path, summaries)

    def _load_json(self, path: Path, default: dict) -> dict:
        if not path.exists():
            self._write_json(path, default)
            return json.loads(json.dumps(default))
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_path = Path(handle.name)
        temp_path.replace(path)


def normalize_config(config: dict | None) -> dict:
    config = config or {}
    assistant = config.get("assistant") or {}
    return {
        "sync_interval_minutes": config.get("sync_interval_minutes", DEFAULT_CONFIG["sync_interval_minutes"]),
        "assistant": {
            "enabled": assistant.get("enabled", DEFAULT_ASSISTANT_CONFIG["enabled"]),
            "default_mode": assistant.get("default_mode", DEFAULT_ASSISTANT_CONFIG["default_mode"]),
            "default_project_ids": assistant.get("default_project_ids", DEFAULT_ASSISTANT_CONFIG["default_project_ids"]),
            "default_categories": assistant.get("default_categories", DEFAULT_ASSISTANT_CONFIG["default_categories"]),
            "default_timeframe": assistant.get("default_timeframe", DEFAULT_ASSISTANT_CONFIG["default_timeframe"]),
            "max_evidence_items": assistant.get("max_evidence_items", DEFAULT_ASSISTANT_CONFIG["max_evidence_items"]),
            "max_source_items": assistant.get("max_source_items", DEFAULT_ASSISTANT_CONFIG["max_source_items"]),
            "retrieval": {
                "release_weight": (assistant.get("retrieval") or {}).get(
                    "release_weight",
                    DEFAULT_ASSISTANT_CONFIG["retrieval"]["release_weight"],
                ),
                "docs_weight": (assistant.get("retrieval") or {}).get(
                    "docs_weight",
                    DEFAULT_ASSISTANT_CONFIG["retrieval"]["docs_weight"],
                ),
            },
            "live_search": {
                "enabled": (assistant.get("live_search") or {}).get(
                    "enabled",
                    DEFAULT_ASSISTANT_CONFIG["live_search"]["enabled"],
                ),
                "provider": (assistant.get("live_search") or {}).get(
                    "provider",
                    DEFAULT_ASSISTANT_CONFIG["live_search"]["provider"],
                ),
                "max_results": (assistant.get("live_search") or {}).get(
                    "max_results",
                    DEFAULT_ASSISTANT_CONFIG["live_search"]["max_results"],
                ),
                "max_pages": (assistant.get("live_search") or {}).get(
                    "max_pages",
                    DEFAULT_ASSISTANT_CONFIG["live_search"]["max_pages"],
                ),
            },
            "prompts": {
                "classification": (assistant.get("prompts") or {}).get(
                    "classification",
                    DEFAULT_ASSISTANT_CONFIG["prompts"]["classification"],
                ),
                "answer": (assistant.get("prompts") or {}).get(
                    "answer",
                    DEFAULT_ASSISTANT_CONFIG["prompts"]["answer"],
                ),
            },
        },
    }
