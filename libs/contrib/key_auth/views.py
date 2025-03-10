import time
from datetime import timedelta
from typing import Optional

from starlette import status
from uuid6 import uuid7

from libs.contrib.auth.mixins import SuperUserRequiredMixin
from libs.contrib.key_auth.models import APIKey
from libs.contrib.key_auth.serializers import APIKeyCreateSerializer, APIKeySerializer
from libs.contrib.key_auth.utils import RawApiKey
from libs.responses import JSONResponse
from libs.router import APIRouter
from libs.security.jwt import create_token
from libs.views.viewsets import ModelViewSet

token_router = APIRouter(tags=["KeyAuth"])


@token_router.post("/key/verify/")
async def token_verify(data: RawApiKey):
    payload, api_key = data

    return {"payload": payload, "uuid": api_key.uuid}


class APIKeyViewSet(ModelViewSet):
    queryset = APIKey
    serializer_class = APIKeySerializer

    def get_serializer_class(self, override_action: Optional[str] = None):
        current_action = override_action or self.action
        if current_action == "create":
            return APIKeyCreateSerializer
        return self.serializer_class

    async def create(self, request, *args, **kwargs):
        data = (await request.data) | {"uuid": str(uuid7())}

        serializer = await self.get_serializer(data=data)

        token = create_token(
            {"uuid": serializer.uuid, "iat": int(time.time())},
            timedelta(days=3650),
        )
        serializer.suffix = token[-32:]

        instance = await self.perform_create(serializer)  # type: ignore

        instance.key = token

        return JSONResponse(
            (await self.get_serializer(instance)).model_dump(),
            status_code=status.HTTP_201_CREATED,
        )
