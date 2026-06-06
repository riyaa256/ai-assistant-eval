from datetime import datetime, timezone


def get_datetime(timezone_str: str = "UTC") -> str:
    """Return the current date and time."""
    try:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        if timezone_str.upper() == "UTC":
            tz = timezone.utc
        else:
            tz = ZoneInfo(timezone_str)
        now = datetime.now(tz)
        return now.strftime(f"%A, %B %d, %Y at %I:%M %p {timezone_str}")
    except Exception:
        now = datetime.now(timezone.utc)
        return now.strftime("%A, %B %d, %Y at %I:%M %p UTC")
