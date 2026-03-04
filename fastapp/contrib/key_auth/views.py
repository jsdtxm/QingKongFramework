import secrets
from typing import Optional

from starlette import status

from fastapp.contrib.auth.mixins import SuperUserRequiredMixin
from fastapp.contrib.key_auth.models import APIKey
from fastapp.contrib.key_auth.serializers import (
    APIKeyCreateSerializer,
    APIKeySerializer,
)
from fastapp.contrib.key_auth.utils import RawApiKey
from fastapp.responses import JSONResponse
from fastapp.router import APIRouter
from fastapp.views.viewsets import ModelViewSet

token_router = APIRouter(tags=["KeyAuth"])


@token_router.post("/key/verify/")
async def token_verify(data: RawApiKey):
    payload, api_key = data

    return {"payload": payload, "uuid": api_key.uuid}


class ApiKeyActionMixin:
    async def create(self, request, *args, **kwargs):
        serializer = await self.get_serializer(data=await request.data)

        # 自动生成 app_key 和 app_secret
        app_key = secrets.token_hex(8)  # 32位十六进制字符串
        app_secret = secrets.token_hex(16)  # 32位十六进制字符串

        serializer.app_key = app_key
        serializer.app_secret = app_secret

        instance = await self.perform_create(serializer)  # type: ignore

        return JSONResponse(
            (await self.get_serializer(instance)).model_dump(),
            status_code=status.HTTP_201_CREATED,
        )


class APIKeyViewSet(ApiKeyActionMixin, SuperUserRequiredMixin, ModelViewSet):
    queryset = APIKey
    serializer_class = APIKeySerializer

    def get_serializer_class(self, override_action: Optional[str] = None):
        current_action = override_action or self.action
        if current_action == "create":
            return APIKeyCreateSerializer
        return self.serializer_class
