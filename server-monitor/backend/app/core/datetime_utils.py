import calendar
from datetime import datetime, timedelta, timezone


UTC = timezone.utc


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


def ensure_utc(value: datetime | None) -> datetime | None:
    """
    Normalize datetimes to UTC.

    SQLite often returns naive datetimes even when the app writes UTC values.
    In that case we treat the stored value as UTC to keep API responses stable.
    """
    if value is None:
        return None

    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def serialize_datetime(value: datetime | None) -> str | None:
    """Serialize a datetime as ISO 8601 with an explicit UTC offset."""
    normalized = ensure_utc(value)
    if normalized is None:
        return None
    return normalized.isoformat().replace("+00:00", "Z")


def format_datetime_in_spain(value: datetime) -> str:
    """Format a datetime in mainland Spain time without external tz data."""
    normalized = ensure_utc(value)
    assert normalized is not None

    offset_hours, label = _spain_offset_for_utc(normalized)
    local_dt = normalized + timedelta(hours=offset_hours)
    return f"{local_dt.strftime('%d/%m/%Y %H:%M:%S')} {label}"


def _spain_offset_for_utc(value: datetime) -> tuple[int, str]:
    """
    Return the UTC offset and label for mainland Spain.

    Spain follows the EU daylight saving rule:
    - Starts: last Sunday of March at 01:00 UTC
    - Ends:   last Sunday of October at 01:00 UTC
    """
    year = value.year
    dst_start = datetime(year, 3, _last_sunday(year, 3), 1, 0, tzinfo=UTC)
    dst_end = datetime(year, 10, _last_sunday(year, 10), 1, 0, tzinfo=UTC)

    if dst_start <= value < dst_end:
        return 2, "CEST"

    return 1, "CET"


def _last_sunday(year: int, month: int) -> int:
    """Return the day number for the last Sunday of a month."""
    last_day = calendar.monthrange(year, month)[1]
    for day in range(last_day, last_day - 7, -1):
        if datetime(year, month, day).weekday() == calendar.SUNDAY:
            return day

    raise ValueError(f"Could not calculate last Sunday for {year}-{month:02d}")
