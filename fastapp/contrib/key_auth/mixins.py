import hashlib
import json
import time

from fastapp.contrib.auth.mixins import AccessMixin
from fastapp.contrib.key_auth.models import APIKey
from fastapp.requests import DjangoStyleRequest


# 时间戳允许误差（毫秒）
TIMESTAMP_TOLERANCE = 600  # 10分钟


class KeyAuthMixin(AccessMixin):
    """Verify that the current user is authenticated using API key."""

    @staticmethod
    def md5_encryption(data: str) -> str:
        """MD5 加密函数"""
        md5 = hashlib.md5()
        md5.update(data.encode("utf-8"))
        return md5.hexdigest()

    @staticmethod
    def dict_to_md5(data_str: str, app_secret: str) -> str:
        """生成签名"""
        return KeyAuthMixin.md5_encryption(data_str + app_secret)

    async def dispatch(self, request: DjangoStyleRequest, *args, **kwargs):
        # 1. 检查必要参数是否存在
        app_key = request.headers.get("appKey")
        timestamp_str = request.headers.get("timestamp")
        sign = request.headers.get("sign")

        if not app_key or not timestamp_str or not sign:
            return self.handle_no_permission()

        # 2. 从数据库查询有效的 appKey
        api_key_obj = await APIKey.filter(app_key=app_key, is_active=True).first()
        if not api_key_obj or not api_key_obj.app_secret:
            return self.handle_no_permission()

        app_secret = api_key_obj.app_secret

        # 3. 检查时间戳是否过期
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            return self.handle_no_permission()

        current_time = int(time.time() * 1000)
        if abs(current_time - timestamp) > TIMESTAMP_TOLERANCE:
            return self.handle_no_permission()

        # 4. 获取请求体原始内容（用于签名计算）
        body = await request.body()
        if body:
            try:
                data_dict = json.loads(body.decode("utf-8"))
                data_str = json.dumps(data_dict, sort_keys=True, separators=(",", ":"))
            except json.JSONDecodeError:
                data_str = body.decode("utf-8")
        else:
            data_str = ""

        # 5. 计算服务端签名
        expected_sign = KeyAuthMixin.dict_to_md5(data_str, app_secret)

        # 6. 比对签名
        if sign != expected_sign:
            return self.handle_no_permission()

        # 7. 验证通过
        return await super().dispatch(request, *args, **kwargs)
