from fastapi.routing import APIRouter

healthz_router = APIRouter()


@healthz_router.get("/")
async def healthz():
    return {"status": "UP"}
