from common.settings import settings
from fastapp import models
from fastapp.contrib.auth import get_user_model
from fastapp.contrib.auth.models import Group, Permission
from fastapp.contrib.contenttypes.models import ContentType
from fastapp.contrib.guardian.manager import BaseObjectPermissionManager


class UserObjectPermission(models.Model):
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        db_constraint=settings.AUTH_USER_DB_CONSTRAINT,
    )  # type: ignore
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    object_id = models.CharField("object ID", max_length=255)

    objects = BaseObjectPermissionManager()

    class Meta:
        db_table = f"{settings.INTERNAL_APP_PREFIX}_user_object_permissions"
        unique_together = ["user", "permission", "object_id"]
        indexes = [
            models.Index(
                fields=("content_type_id", "object_id"),
                name="user_object_permissions_idx",
            ),
        ]
        manager = BaseObjectPermissionManager()

    def __str__(self):
        return f"{self.user} {self.permission} #{self.object_id}"


class GroupObjectPermission(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    object_id = models.CharField("object ID", max_length=255)

    objects = BaseObjectPermissionManager()

    class Meta:
        db_table = f"{settings.INTERNAL_APP_PREFIX}_group_object_permissions"
        unique_together = ["group", "permission", "object_id"]
        indexes = [
            models.Index(
                fields=("content_type_id", "object_id"),
                name="group_object_permissions_idx",
            ),
        ]
        manager = BaseObjectPermissionManager()

    def __str__(self):
        return f"{self.group} {self.permission} #{self.object_id}"
