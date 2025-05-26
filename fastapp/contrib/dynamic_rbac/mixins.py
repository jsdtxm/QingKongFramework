from typing import Optional

from fastapp.contrib.dynamic_rbac.models import DynamicPermission
from fastapp.exceptions import NotAuthenticated


class DynamicPermissionMixin:
    """
    需要动态权限控制的ViewSet Mixin
    默认配置标准操作的权限：
    - create: add
    - retrieve/list: view
    - update: change
    - destroy: delete
    """

    permission_classes = [DynamicPermission]

    _action_permissions: Optional[dict[str, str]] = None

    _default_action_permissions = {
        "create": "add",
        "retrieve": "view",
        "update": "change",
        "destroy": "delete",
        "list": "view",
    }

    action_permissions: dict[str, str] = {}

    async def dispatch(self, request, *args, **kwargs):
        if request.user is None or not request.user.is_authenticated:
            raise NotAuthenticated()

        action = getattr(self, "action", None)
        if not action or not getattr(self, action, None):
            return await super().dispatch(request, *args, **kwargs)

        if request.user.is_superuser:
            return await super().dispatch(request, *args, **kwargs)

        has_perm = await self.has_dynamic_permission(request)
        if not has_perm:
            return self.permission_denied(request, message="Permission denied")

        return await super().dispatch(request, *args, **kwargs)

    async def get_action_permission(self):
        handler = getattr(self, self.action)
        if perm := getattr(handler, "_perm", None):
            return perm

        perm = self.get_action_permissions_map().get(
            self.action,
            {
                "GET": "view",
                "POST": "add",
                "PUT": "change",
                "PATCH": "change",
                "DELETE": "delete",
            }.get(self.request.method, "view"),
        )

        return perm

    async def has_dynamic_permission(self, request):
        perm = await self.get_action_permission()

        handler = getattr(self, self.action)
        target = getattr(handler, "_target", self.get_view_identifier())

        has_perm = await DynamicPermission.objects.filter(
            perm=perm, target=target, groups__user_set=request.user
        ).exists()

        return has_perm

    @classmethod
    def get_action_permissions_map(cls):
        if cls._action_permissions:
            return cls._action_permissions
        cls._action_permissions = (
            cls._default_action_permissions | cls.action_permissions
        )
        return cls._action_permissions

    @classmethod
    def get_permission_codes(cls):
        action_permissions = cls.get_action_permissions_map()

        perm_code_set = set()
        for perm in action_permissions.values():
            perm_code_set.add(perm)

        return perm_code_set

    @classmethod
    def get_view_identifier(cls):
        return f"{cls.__module__}.{cls.__name__}"
