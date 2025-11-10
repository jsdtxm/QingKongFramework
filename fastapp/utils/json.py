import datetime
import decimal
import json
import math
import uuid

from fastapp.conf import settings


def remove_comments(jsonc_content: str):
    """移除JSONC内容中的注释"""

    lines = jsonc_content.splitlines()
    cleaned_lines = []
    in_block_comment = False

    for line in lines:
        if not in_block_comment:
            # 清理当前行的行注释
            index = line.find("//")
            if index != -1:
                line = line[:index]

            # 清理当前行开始的块注释起始部分
            index = line.find("/*")
            if index != -1:
                line = line[:index]
                in_block_comment = True

        if in_block_comment:
            # 寻找块注释结束部分
            index = line.find("*/")
            if index != -1:
                line = line[index + 2 :]
                in_block_comment = False
            else:
                line = ""

        if line.strip() or in_block_comment:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _get_duration_components(duration):
    days = duration.days
    seconds = duration.seconds
    microseconds = duration.microseconds

    minutes = seconds // 60
    seconds %= 60

    hours = minutes // 60
    minutes %= 60

    return days, hours, minutes, seconds, microseconds


def duration_iso_string(duration):
    if duration < datetime.timedelta(0):
        sign = "-"
        duration *= -1
    else:
        sign = ""

    days, hours, minutes, seconds, microseconds = _get_duration_components(duration)
    ms = ".{:06d}".format(microseconds) if microseconds else ""
    return "{}P{}DT{:02d}H{:02d}M{:02d}{}S".format(
        sign, days, hours, minutes, seconds, ms
    )


def is_aware(value):
    """
    Determine if a given datetime.datetime is aware.

    The concept is defined in Python's docs:
    https://docs.python.org/library/datetime.html#datetime.tzinfo

    Assuming value.tzinfo is either None or a proper datetime.tzinfo,
    value.utcoffset() implements the appropriate logic.
    """
    return value.utcoffset() is not None


def default_datetime_format(o):
    if isinstance(o, datetime.datetime):
        return o.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(o, datetime.date):
        return o.isoformat()
    elif isinstance(o, datetime.time):
        return o.strftime("%H:%M:%S")
    elif isinstance(o, dict):
        return {k: default_datetime_format(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [default_datetime_format(v) for v in o]
    return o


def replace_nan(o):
    if isinstance(o, float) and math.isnan(o):
        return None
    elif isinstance(o, dict):
        return {k: replace_nan(v) for k, v in o.items()}
    elif isinstance(o, list):
        return [replace_nan(v) for v in o]
    return o


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time, decimal types, and
    UUIDs.
    """

    def default(self, o):
        # Copy From Django

        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            return o.strftime(settings.DATETIME_FORMAT)
        elif isinstance(o, datetime.date):
            return o.strftime(settings.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, datetime.timedelta):
            return duration_iso_string(o)
        elif isinstance(o, (decimal.Decimal, uuid.UUID)):
            return str(o)
        else:
            return super().default(o)
