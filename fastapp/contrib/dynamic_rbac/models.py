from fastapp import models
from fastapp.contrib.auth.models import Group


class DynamicPermission(models.Model):
    """
    DynamicPermission model represents a set of permissions that can be dynamically assigned to groups.
    - perm: Represents the type of permission, such as 'add', 'change', 'delete', 'view', etc.
    - target: Represents the target object or resource to which the permission applies.
    """

    perm = models.CharField(max_length=50)
    target = models.CharField(max_length=255)
    groups = models.ManyToManyField(
        Group, related_name="dynamic_permissions", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("perm", "target")
        indexes = [
            models.Index(
                fields=("perm", "target"), name="dynamic_permission_together_idx"
            ),
        ]
