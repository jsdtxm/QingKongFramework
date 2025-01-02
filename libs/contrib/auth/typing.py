from typing import Optional, Protocol, Self


class UserProtocol(Protocol):
    id: int
    username: str

    is_active: bool

    objects: "UserProtocol"

    @classmethod
    def get_or_none(cls, **kwargs) -> Optional[Self]: ...

    @classmethod
    def get(cls, **kwargs) -> Self: ...
