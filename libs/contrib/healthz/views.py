from fastapi.routing import APIRouter

from libs.contrib.healthz.utils import check_db_and_cache
from libs.responses import JsonResponse

router = APIRouter(tags=["Healthz"])


@router.get("/healthz/")
async def healthz():
    return {"status": "UP"}


@router.get("/healthz_extend/")
async def healthz_extend():
    checks, status_code = await check_db_and_cache()

    return JsonResponse(checks, status_code=status_code)
