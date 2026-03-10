from dataclasses import dataclass


@dataclass(slots=True)
class EventRecord:
    id: str
    source: str
    title: str
    content_hash: str


@dataclass(slots=True)
class AnalysisRecord:
    title_zh: str
    summary_zh: str
    is_stable: bool
