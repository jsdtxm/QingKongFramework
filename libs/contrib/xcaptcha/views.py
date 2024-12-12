from starlette.status import HTTP_400_BAD_REQUEST

from libs.contrib.xcaptcha.client import XCaptchaClient
from libs.contrib.xcaptcha.encrypt import decrypt_ts_key
from libs.exceptions import HTTPException
from libs.requests import DjangoStyleRequest
from libs.responses import JsonResponse
from libs.views.class_based import View


class CaptchaAcquireView(View):
    async def post(self, request: DjangoStyleRequest):
        track_id = request.GET.get("track_id")
        if not track_id:
            raise HTTPException(
                HTTP_400_BAD_REQUEST,
                "Invalid track_id",
            )

        key = decrypt_ts_key(track_id)
        response = await XCaptchaClient.from_config().acquire_challenges(key)

        resp_json = await response.json()
        if resp_json["status"] == "ok":
            data = resp_json.get("data")
        else:
            data = resp_json

        return JsonResponse(data)


class CaptchaResolveView(View):
    async def post(self, request: DjangoStyleRequest):
        track_id = request.GET.get("track_id")
        if not track_id:
            raise HTTPException(
                HTTP_400_BAD_REQUEST,
                "Invalid track_id",
            )

        point, token = (
            (await request.json()).get("point"),
            (await request.json()).get("token"),
        )
        if not point or not token:
            raise HTTPException(
                HTTP_400_BAD_REQUEST,
                "Invalid point or token",
            )

        key = decrypt_ts_key(track_id)
        response = XCaptchaClient.from_config().resolve_challenges(key, point, token)

        resp_json = response.json()
        if resp_json["status"] == "ok":
            data = resp_json.get("data")
        else:
            data = resp_json

        return JsonResponse(data)
