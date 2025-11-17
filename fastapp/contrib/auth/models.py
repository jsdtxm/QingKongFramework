from typing import Iterable, Optional, Self, Type, Union

from tortoise.queryset import MODEL

from common.settings import settings
from fastapp import models
from fastapp.contrib.auth.backends.base import BasePermissionBackend
from fastapp.contrib.auth.utils import ANONYMOUS_USERNAME
from fastapp.contrib.contenttypes.models import ContentType
from fastapp.django.hashers import make_password
from fastapp.models import Manager, QuerySet
from fastapp.utils.module_loading import import_string

DefaultPerms = ["add", "change", "delete", "view"]


class Permission(models.Model):
    """
    The permissions system provides a way to assign permissions to specific
    users and groups of users.

    The permission system is used by the Django admin site, but may also be
    useful in your own code. The Django admin site uses permissions as follows:

        - The "add" permission limits the user's ability to view the "add" form
          and add an object.
        - The "change" permission limits a user's ability to view the change
          list, view the "change" form and change an object.
        - The "delete" permission limits the ability to delete an object.
        - The "view" permission limits the ability to view an object.

    Permissions are set globally per type of object, not per specific object
    instance. It is possible to say "Mary may change news stories," but it's
    not currently possible to say "Mary may change news stories, but only the
    ones she created herself" or "Mary may only change news stories that have a
    certain status or publication date.

    The permissions listed above are automatically created for each model.
    """

    description = models.CharField("description", max_length=512, null=True)
    content_type = models.ForeignKey(
        ContentType,
        models.CASCADE,
        verbose_name="content type",
    )
    perm = models.CharField("perm", max_length=128)

    class Meta:
        verbose_name = "permission"
        verbose_name_plural = "permissions"
        unique_together = [["content_type", "perm"]]
        ordering = ["content_type__app_label", "content_type__model", "perm"]

    def __str__(self):
        return "%s | %s" % (self.content_type, self.perm)


class LoadPermissionBackendMixin:
    permission_backend: Optional[Type["BasePermissionBackend"]] = None

    @classmethod
    def get_permission_backend(cls):
        if cls.permission_backend is None:
            cls.permission_backend = import_string(settings.AUTH_PERMISSION_BACKEND)
        return cls.permission_backend


class Group(models.Model, LoadPermissionBackendMixin):
    """
    Groups are a generic way of categorizing users to apply permissions, or
    some other label, to those users. A user can belong to any number of
    groups.

    A user in a group automatically has all the permissions granted to that
    group. For example, if the group 'Site editors' has the permission
    can_edit_home_page, any user in that group will have that permission.

    Beyond permissions, groups are a convenient way to categorize users to
    apply some label, or extended functionality, to them. For example, you
    could create a group 'Special users', and you could write code that would
    do special things to those users -- such as giving them access to a
    members-only portion of your site, or sending them members-only email
    messages.
    """

    name = models.CharField("name", max_length=150, unique=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name="permissions",
        blank=True,
        related_name="group_set",
        through=f"{settings.INTERNAL_APP_PREFIX}_auth_group_permissions",
    )

    user_set: models.ManyToManyRelation["AbstractUser"]

    class Meta:
        verbose_name = "group"
        verbose_name_plural = "groups"

    def __str__(self):
        return self.name

    async def has_perm(
        self,
        perm: str,
        obj: Optional[Union[models.Model, Type[models.Model]]] = None,
    ) -> bool:
        return await self.get_permission_backend().has_perm(self, perm, obj)

    async def has_perms(
        self,
        perm_list: Iterable[str],
        obj: Optional[Union[models.Model, Type[models.Model]]] = None,
    ):
        return await self.get_permission_backend().has_perms(self, perm_list, obj)

    async def has_module_perms(self, app_label: str) -> bool:
        return await self.get_permission_backend().has_module_perms(self, app_label)


class UserManager(Manager[MODEL]):
    async def create_user(self, username, email=None, password=None, **extra_fields):
        return await self._model.create(
            username=username,
            email=email,
            password=make_password(password),
            **extra_fields,
        )


class AbstractUser(models.Model, LoadPermissionBackendMixin):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)

    email = models.EmailField(null=True)

    is_active = models.BooleanField(default=True)

    last_login = models.DateTimeField(null=True)

    is_superuser = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="user_set",
        related_query_name="user",
        through=f"{settings.INTERNAL_APP_PREFIX}_auth_user_groups",
        db_constraint=settings.AUTH_USER_DB_CONSTRAINT,
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="user_set",
        related_query_name="user",
        through=f"{settings.INTERNAL_APP_PREFIX}_auth_user_permissions",
        db_constraint=settings.AUTH_USER_DB_CONSTRAINT,
    )

    objects: Union[UserManager[Self], QuerySet[Self]]

    def __str__(self):
        return f"<User: {self.username}>"

    @property
    def is_authenticated(self):
        return self.username != ANONYMOUS_USERNAME

    @property
    def is_anonymous(self):
        return self.username == ANONYMOUS_USERNAME

    async def has_perm(
        self,
        perm: str,
        obj: Optional[Union[models.Model, Type[models.Model]]] = None,
    ) -> bool:
        """
        Return True if the user has the specified permission. Query all
        available auth backends, but return immediately if any backend returns
        True. Thus, a user who has permission from a single auth backend is
        assumed to have permission in general. If an object is provided, check
        permissions for that object.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return await self.get_permission_backend().has_perm(self, perm, obj)

    async def has_perms(
        self,
        perm_list: Iterable[str],
        obj: Optional[Union[models.Model, Type[models.Model]]] = None,
    ):
        return await self.get_permission_backend().has_perms(self, perm_list)

    async def has_module_perms(self, app_label: str) -> bool:
        """
        Return True if the user has any permissions in the given app label.
        Use similar logic as has_perm(), above.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return await self.get_permission_backend().has_module_perms(self, app_label)

    def set_password(self, password):
        self.password = make_password(password)

    class Meta:
        abstract = True
        manager = UserManager()

    class PydanticMeta:
        write_only_fields = ["password"]


if settings.AUTH_USER_MODEL == "fastapp.contrib.auth.models.User":

    class User(AbstractUser):
        objects = UserManager()

        class Meta(AbstractUser.Meta):
            abstract = False
