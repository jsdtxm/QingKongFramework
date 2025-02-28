from libs import models
from libs.contrib.auth import get_user_model
from libs.contrib.auth.models import Group, Permission
from libs.contrib.contenttypes.models import ContentType
from libs.contrib.guardian.manager import BaseObjectPermissionManager


class UserObjectPermission(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)  # type: ignore
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    object_id = models.CharField("object ID", max_length=255)

    objects = BaseObjectPermissionManager()

    class Meta:
        db_table = "qingkong_user_object_permissions"
        unique_together = ["user", "permission", "object_id"]
        indexes = [
            models.Index(
                fields=("content_type", "object_id"), name="user_object_permissions_idx"
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
        db_table = "qingkong_group_object_permissions"
        unique_together = ["group", "permission", "object_id"]
        indexes = [
            models.Index(
                fields=("content_type", "object_id"),
                name="group_object_permissions_idx",
            ),
        ]
        manager = BaseObjectPermissionManager()

    def __str__(self):
        return f"{self.group} {self.permission} #{self.object_id}"
