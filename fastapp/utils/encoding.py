from decimal import Decimal
import datetime

_PROTECTED_TYPES = (
    type(None), int, float, Decimal, datetime.datetime, datetime.date, datetime.time,
)

class FastAppUnicodeDecodeError(UnicodeDecodeError):
    def __init__(self, obj, *args):
        self.obj = obj
        super().__init__(*args)

    def __str__(self):
        return '%s. You passed in %r (%s)' % (super().__str__(), self.obj, type(self.obj))


def is_protected_type(obj):
    """Determine if the object instance is of a protected type.

    Objects of protected types are preserved as-is when passed to
    force_str(strings_only=True).
    """
    return isinstance(obj, _PROTECTED_TYPES)

def punycode(domain):
    """Return the Punycode of the given domain if it's non-ASCII."""
    return domain.encode("idna").decode("ascii")


def force_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_str(), except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first for performance reasons.
    if issubclass(type(s), str):
        return s
    if strings_only and is_protected_type(s):
        return s
    try:
        if isinstance(s, bytes):
            s = str(s, encoding, errors)
        else:
            s = str(s)
    except UnicodeDecodeError as e:
        raise FastAppUnicodeDecodeError(s, *e.args)
    return s