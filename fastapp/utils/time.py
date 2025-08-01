import numbers
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapp.conf import settings


def maybe_timedelta(delta: int) -> timedelta:
    """Convert integer to timedelta, if argument is an integer."""
    if isinstance(delta, numbers.Real):
        return timedelta(seconds=delta)
    return delta


class TimeZone:
    @staticmethod
    def now():
        """utc"""
        return datetime.now(ZoneInfo(settings.TIME_ZONE))

    @staticmethod
    def utcnow():
        """utc"""
        return datetime.now(ZoneInfo("UTC"))

    @staticmethod
    def timedelta(*args, **kwargs):
        return timedelta(*args, **kwargs)


timezone = TimeZone()
