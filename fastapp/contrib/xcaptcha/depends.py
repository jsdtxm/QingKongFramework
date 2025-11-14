import asyncio
from typing import Callable, Optional, Type

from starlette.requests import Request
from starlette.responses import Response

from fastapp.conf import settings
from fastapp.contrib.limiter.depends import RateLimiter
from fastapp.contrib.xcaptcha import XCaptchaLimiter
from fastapp.contrib.xcaptcha.client import XCaptchaClient
from fastapp.contrib.xcaptcha.encrypt import encrypt_ts_key
from fastapp.contrib.xcaptcha.exceptions import (
    CaptchaRequired,
    Ratelimited,
    ThrottledException,
)


class IntelligenceLimiter(RateLimiter):
    def __init__(
        self,
        rules=None,
        identifier: Optional[Callable] = None,
        callback: Optional[Callable] = None,
        limiter: Type[XCaptchaLimiter] = XCaptchaLimiter,
    ):
        if not settings.XCAPTCHA_ENABLE:
            return

        self.rules = rules

        self.identifier = identifier
        self.callback = callback

        self.limiter = limiter
        self.client = XCaptchaClient.from_config()

    def __del__(self):
        asyncio.new_event_loop().run_until_complete(self.client.close())

    async def _check(self, key) -> Optional[ThrottledException]:
        if not settings.XCAPTCHA_ENABLE:
            return None

        try:
            response = await self.client.risk_assessment(
                key, rules=list(map(lambda r: r.to_dict(), self.rules))
            )
            if response.status in (200, 429):
                resp = await response.json()
                if resp["status"] == "throttled":
                    action = resp["data"]["action"]
                    if action == "block":
                        raise Ratelimited(encrypt_ts_key(key))
                    elif action == "captcha":
                        raise CaptchaRequired(encrypt_ts_key(key))
            else:
                response.raise_for_status()
        except (Ratelimited, CaptchaRequired) as e:
            return e
        except OSError as e:
            print(f"Http Error: {e}")
        except Exception as e:
            print(f"Unknown Error {e}")

        return None

    async def __call__(self, request: Request, response: Response):
        if not settings.XCAPTCHA_ENABLE:
            return None

        route_index, dep_index = self.get_dep_index(request)

        # moved here because constructor run before app startup
        identifier = self.identifier or self.limiter.identifier
        callback = self.callback or self.limiter.http_callback
        rate_key = await identifier(request)
        key = f"{rate_key}:{route_index}:{dep_index}"

        action = await self._check(key)
        if action is not None:
            return await callback(request, response, action)
