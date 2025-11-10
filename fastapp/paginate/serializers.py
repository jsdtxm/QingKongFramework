from typing import Generic, TypeVar

from pydantic import BaseModel, Field

MODEL = TypeVar("MODEL")


class PaginateResponse(BaseModel, Generic[MODEL]):
    data: list[MODEL] = Field()
    total: int = Field(default=0)
    success: bool = Field(default=True)
