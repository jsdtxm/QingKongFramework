from libs.contrib.auth.mixins import SuperUserRequiredMixin
from libs.contrib.key_auth.models import APIKey
from libs.contrib.key_auth.serializers import APIKeySerializer
from libs.contrib.key_auth.utils import RawApiKey
from libs.router import APIRouter
from libs.views.viewsets import ModelViewSet

token_router = APIRouter(tags=["KeyAuth"])


@token_router.post("/key/verify/")
async def token_verify(data: RawApiKey):
    payload, api_key = data

    return {"payload": payload, "uuid": api_key.uuid}


class APIKeyViewSet(SuperUserRequiredMixin, ModelViewSet):
    queryset = APIKey
    serializer_class = APIKeySerializer
