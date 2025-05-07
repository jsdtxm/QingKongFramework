from fastapp.conf import settings
from fastapp.utils.module_loading import import_string

RateLimiter = import_string(settings.RATE_LIMITER_CLASS)
WebSocketRateLimiter = import_string(settings.WEBSOCKET_RATE_LIMITER_CLASS)
