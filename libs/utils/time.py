import numbers
from datetime import timedelta


def maybe_timedelta(delta: int) -> timedelta:
    """Convert integer to timedelta, if argument is an integer."""
    if isinstance(delta, numbers.Real):
        return timedelta(seconds=delta)
    return delta
