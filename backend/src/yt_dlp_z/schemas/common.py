from datetime import UTC, datetime


def as_utc_iso(value: datetime | None) -> str | None:
    # SQLite drops timezone info; stored values are always UTC.
    if value is None:
        return None
    return value.replace(tzinfo=value.tzinfo or UTC).isoformat()
