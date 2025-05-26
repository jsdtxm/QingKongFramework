import inspect

from fastapp import apps
from fastapp.conf import settings
from fastapp.contrib.dynamic_rbac.mixins import DynamicPermissionMixin
from fastapp.contrib.dynamic_rbac.models import DynamicPermission


async def initialize_dynamic_permissions():
    """
    Asynchronously initializes dynamic permissions by iterating through all app configurations.
    For each app, it imports the views module and checks for classes that inherit from DynamicPermissionMixin.
    For each such class, it retrieves the view identifier and permission codes,
    then creates or retrieves the corresponding DynamicPermission objects.
    """

    created_perms = set()

    for target, perms in getattr(settings, "DYNAMIC_PERMISSIONS", {}).items():
        for perm in perms:
            await DynamicPermission.objects.get_or_create(
                perm=perm,
                target=target,
            )
            created_perms.add((perm, target))

    for app_config in apps.apps.app_configs.values():
        views_module = app_config.import_module("views")
        if views_module is None:
            continue

        for name in dir(views_module):
            if name.startswith("_"):
                continue

            obj = getattr(views_module, name)
            if (
                inspect.isclass(obj)
                and issubclass(obj, DynamicPermissionMixin)
                and obj != DynamicPermissionMixin
                and not obj.__name__.endswith("Mixin")
            ):
                view_identifier = obj.get_view_identifier()
                permission_codes = obj.get_permission_codes()

                for code in permission_codes:
                    if (code, view_identifier) in created_perms:
                        continue

                    await DynamicPermission.objects.get_or_create(
                        perm=code,
                        target=view_identifier,
                    )

                    created_perms.add((code, view_identifier))
