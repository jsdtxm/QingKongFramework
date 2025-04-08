import inspect

from libs import apps
from libs.contrib.dynamic_rbac.mixins import DynamicPermissionMixin
from libs.contrib.dynamic_rbac.models import DynamicPermission


async def initialize_dynamic_permissions():
    """
    Asynchronously initializes dynamic permissions by iterating through all app configurations.
    For each app, it imports the views module and checks for classes that inherit from DynamicPermissionMixin.
    For each such class, it retrieves the view identifier and permission codes,
    then creates or retrieves the corresponding DynamicPermission objects.
    """
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
            ):
                view_identifier = obj.get_view_identifier()
                permission_codes = obj.get_permission_codes()

                for code in permission_codes:
                    await DynamicPermission.objects.get_or_create(
                        perm=code,
                        target=view_identifier,
                    )
