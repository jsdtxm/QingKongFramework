from typing import Callable, Optional, Type

from starlette.requests import Request
from starlette.responses import Response

from libs.contrib.xcaptcha import XCaptchaLimiter
from libs.contrib.xcaptcha.client import XCaptchaClient
from libs.contrib.xcaptcha.encrypt import encrypt_ts_key
from libs.contrib.xcaptcha.exceptions import CaptchaRequired, Ratelimited, ThrottledException
from libs.contrib.limiter.depends import RateLimiter

class IntelligenceLimiter(RateLimiter):
    def __init__(
        self,
        rules=None,
        identifier: Optional[Callable] = None,
        callback: Optional[Callable] = None,
        limiter: Type[XCaptchaLimiter] = XCaptchaLimiter,
    ):
        self.rules = rules

        self.identifier = identifier
        self.callback = callback

        self.limiter = limiter
        self.client = XCaptchaClient.from_config()

    async def _check(self, key) -> Optional[ThrottledException]:
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
        
        route_index, dep_index = self.get_dep_index(request)

        # moved here because constructor run before app startup
        identifier = self.identifier or self.limiter.identifier
        callback = self.callback or self.limiter.http_callback
        rate_key = await identifier(request)
        key = f"{rate_key}:{route_index}:{dep_index}"

        action = await self._check(key)
        if action is not None:
            return await callback(request, response, action)
