from typing import List

from pydantic import BaseModel, Field


class PermActionSerializer(BaseModel):
    perms: List[str] = Field(default_factory=list, min_length=1)
    user_id: int = Field(..., description="用户ID")
