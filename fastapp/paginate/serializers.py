from pydantic import BaseModel, Field


class PaginateResponse(BaseModel):
    data: list = Field(default=[])
    total: int = Field(default=0)
    success: bool = Field(default=True)
