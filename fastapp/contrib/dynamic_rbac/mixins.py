from typing import Optional

from fastapp.contrib.dynamic_rbac.models import DynamicPermission


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
            return self.handle_no_permission()

        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        perm = self.get_action_permissions().get(
            self.action,
            {
                "GET": "view",
                "POST": "add",
                "PUT": "change",
                "PATCH": "change",
                "DELETE": "delete",
            }.get(self.request.method, "view"),
        )

        has_perm = await DynamicPermission.objects.filter(
            perm=perm, target=self.get_view_identifier(), groups__user=request.user
        ).exists()

        if not has_perm:
            return self.handle_no_permission()

        return await super().dispatch(request, *args, **kwargs)

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
