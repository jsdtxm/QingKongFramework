import numbers
from datetime import datetime, timedelta
from datetime import timezone as python_timezone


def maybe_timedelta(delta: int) -> timedelta:
    """Convert integer to timedelta, if argument is an integer."""
    if isinstance(delta, numbers.Real):
        return timedelta(seconds=delta)
    return delta


class TimeZone:
    @staticmethod
    def now():
        """utc"""
        return datetime.now(python_timezone.utc)


timezone = TimeZone()
