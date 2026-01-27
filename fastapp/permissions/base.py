from typing import ClassVar, Self, Tuple, Type

from fastapp.core.operable import OperableClassBase, OperableClassMeta
from fastapp.requests import DjangoStyleRequest

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class OperablePermissionBase(OperableClassBase):
    _sources: ClassVar[Tuple[Type["OperablePermissionBase"], ...]]
    _operation: ClassVar[str]

    async def has_object_permission(
        self, request: DjangoStyleRequest, view, obj=None
    ) -> bool:
        """
        子类必须实现此方法（原子权限），
        或由 OperablePermissionMeta 自动生成（组合权限）。
        """
        raise NotImplementedError

    async def has_permission(self, request: DjangoStyleRequest, view) -> bool:
        """
        子类可选实现此方法（原子权限），
        或由 OperablePermissionMeta 自动生成（组合权限）。
        """
        raise NotImplementedError


class OperablePermissionMeta(OperableClassMeta):
    def __new__(mcs, name, bases, namespace, **kwargs):
        if "has_permission" not in namespace:

            async def has_permission(self, request: DjangoStyleRequest, view) -> bool:
                return await self.has_object_permission(request, view, None)

            namespace["has_permission"] = has_permission
        return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __or__(cls, other: Self):
        if not isinstance(other, OperablePermissionMeta):
            raise NotImplementedError

        new_name = f"{cls.__name__}_OR_{other.__name__}"

        async def has_object_permission(self, request, view, obj) -> bool:
            left = cls().has_object_permission(request, view, obj)
            right = other().has_object_permission(request, view, obj)
            return await left or await right

        async def has_permission(self, request: DjangoStyleRequest, view) -> bool:
            left = cls().has_permission(request, view)
            right = other().has_permission(request, view)
            return await left or await right

        return OperablePermissionMeta._create_binary_op(
            new_name, (cls, other), "|", has_object_permission, has_permission
        )

    def __and__(cls, other: Self):
        if not isinstance(other, OperablePermissionMeta):
            raise NotImplementedError

        new_name = f"{cls.__name__}_AND_{other.__name__}"

        async def has_object_permission(self, request, view, obj) -> bool:
            left = await cls().has_object_permission(request, view, obj)
            right = await other().has_object_permission(request, view, obj)
            return left and right

        async def has_permission(self, request: DjangoStyleRequest, view) -> bool:
            left = await cls().has_permission(request, view)
            right = await other().has_permission(request, view)
            return left and right

        return OperablePermissionMeta._create_binary_op(
            new_name, (cls, other), "&", has_object_permission, has_permission
        )

    def __xor__(cls, other: Self):
        if not isinstance(other, OperablePermissionMeta):
            raise NotImplementedError

        new_name = f"{cls.__name__}_XOR_{other.__name__}"

        async def has_object_permission(self, request, view, obj) -> bool:
            left = await cls().has_object_permission(request, view, obj)
            right = await other().has_object_permission(request, view, obj)
            return left ^ right

        async def has_permission(self, request: DjangoStyleRequest, view) -> bool:
            left = await cls().has_permission(request, view)
            right = await other().has_permission(request, view)
            return left ^ right

        return OperablePermissionMeta._create_binary_op(
            new_name, (cls, other), "^", has_object_permission, has_permission
        )

    def __invert__(cls):
        new_name = f"NOT_{cls.__name__}"

        async def has_object_permission(self, request, view, obj) -> bool:
            val = await cls().has_object_permission(request, view, obj)
            return not val

        async def has_permission(self, request: DjangoStyleRequest, view) -> bool:
            val = await cls().has_permission(request, view)
            return not val

        return OperablePermissionMeta._create_unary_op(
            new_name, (cls,), "~", has_object_permission, has_permission
        )

    @staticmethod
    def _create_binary_op(name: str, sources: tuple, op: str, object_method, method):
        return OperablePermissionMeta(
            name,
            (OperablePermissionBase,),
            {
                "_sources": sources,
                "_operation": op,
                "has_object_permission": object_method,
                "has_permission": method,
            },
        )

    @staticmethod
    def _create_unary_op(name: str, sources: tuple, op: str, object_method, method):
        return OperablePermissionMeta(
            name,
            (OperablePermissionBase,),
            {
                "_sources": sources,
                "_operation": op,
                "has_object_permission": object_method,
                "has_permission": method,
            },
        )

    def __repr__(cls: Type[OperableClassBase]):
        if hasattr(cls, "_sources"):
            op = cls._operation
            if op == "~":
                inner = cls._sources[0].__name__
                return f"<PermissionClass {cls.__name__} (from ~{inner})>"
            else:
                names = f" {op} ".join(c.__name__ for c in cls._sources)
                return f"<PermissionClass {cls.__name__} (from {names})>"
        return super().__repr__()
