import aiohttp

from common.settings import settings


class XCaptchaClient:
    def __init__(self, base_url, headers=None):
        self.base_url = base_url
        self.session = aiohttp.ClientSession()
        if headers is not None:
            self.session.headers.update(headers)

    async def close(self):
        await self.session.close()

    @classmethod
    def from_config(cls):
        return cls(settings.XCAPTCHA_URL, {"X-API-Key": settings.XCAPTCHA_API_KEY})

    async def request(self, method, url, **kwargs):
        merged_url = f"{self.base_url}/{url}"
        return await self.session.request(method, merged_url, **kwargs)

    async def post(self, url, **kwargs):
        req_kwargs = {"timeout": 2}
        req_kwargs.update(kwargs)

        return await self.request("POST", url, **req_kwargs)

    async def risk_assessment(self, key, rules):
        return await self.post(
            "guard/risk_assessment",
            params={"key": key},
            json={"rules": rules},
        )

    async def acquire_challenges(self, key):
        return await self.post(
            "guard/challenges/acquire",
            params={"key": key},
            json={"captcha_type": "click_word"},
            timeout=10,
        )

    async def resolve_challenges(self, key, point, token):
        return await self.post(
            "guard/challenges/resolve",
            params={"key": key},
            json={
                "point": point,
                "token": token,
            },
            timeout=10,
        )
