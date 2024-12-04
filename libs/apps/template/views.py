from typing import Union

from apps.app_name.models import Tournament
from fastapi.routing import APIRouter

router = APIRouter()

@router.get("/")
async def read_root():
    return {"Hello": "Main"}


@router.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@router.get("/create_event")
async def create_event():
    Tournament.objects.filter()
    Tournament.objects.all()
    await Tournament.objects.create(name="New Tournament")
    return {"Hello": "Main"}
