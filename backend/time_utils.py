from datetime import UTC, datetime
from email.utils import parsedate_to_datetime


def parse_datetime(value: str | None) -> datetime | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    try:
        return datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(normalized)
    except (TypeError, ValueError, IndexError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def normalize_timestamp(value: str | None) -> str:
    parsed = parse_datetime(value)
    if not parsed:
        return value or ""
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def date_key(value: str | None) -> str:
    parsed = parse_datetime(value)
    return parsed.date().isoformat() if parsed else ""


def timestamp_for_sort(value: str | None) -> int:
    parsed = parse_datetime(value)
    return int(parsed.timestamp()) if parsed else 0
