from libs.responses import JsonResponse

from libs.contrib.xcaptcha.encrypt import decrypt_ts_key
# from utils.decorator_util import pro_exec_api
# from utils.mixin import LoginRequiredMixin
# from utils.response_code import Code, Msg, SubCode
from libs.contrib.xcaptcha.client import XCaptchaClient
from libs.views.class_based import View
from functools import wraps

class CaptchaAcquireView(View):
    async def post(self, request):
        track_id = request.GET.get("track_id")
        if not track_id:
            res = {
                "code": Code.OK,
                "msg": Msg.OK,
                "sub_code": SubCode.BAD_REQUEST,
                "sub_msg": "invalid track_id.",
            }
            return JsonResponse(res)

        key = decrypt_ts_key(track_id)
        response = await XCaptchaClient.from_config().acquire_challenges(key)

        resp_json = response.json()
        if resp_json["status"] == "ok":
            data = resp_json.get("data")
        else:
            data = resp_json

        res = {
            "code": Code.OK,
            "msg": Msg.OK,
            "sub_code": SubCode.OK,
            "sub_msg": "OK!",
            "data": data,
        }
        return JsonResponse(res)


class CaptchaResolveView( View):
    async def post(self, request):
        track_id = request.GET.get("track_id")
        if not track_id:
            res = {
                "code": Code.OK,
                "msg": Msg.OK,
                "sub_code": SubCode.BAD_REQUEST,
                "sub_msg": "invalid track_id.",
            }
            return JsonResponse(res)

        point, token = request.json_data.get("point"), request.json_data.get("token")
        if not point or not token:
            res = {
                "code": Code.OK,
                "msg": Msg.OK,
                "sub_code": SubCode.BAD_REQUEST,
                "sub_msg": "invalid point and token.",
            }
            return JsonResponse(res)

        key = decrypt_ts_key(track_id)
        response = XCaptchaClient.from_config().resolve_challenges(key, point, token)

        resp_json = response.json()
        if resp_json["status"] == "ok":
            data = resp_json.get("data")
        else:
            data = resp_json

        res = {
            "code": Code.OK,
            "msg": Msg.OK,
            "sub_code": SubCode.OK,
            "sub_msg": "OK!",
            "data": data,
        }
        return JsonResponse(res)
