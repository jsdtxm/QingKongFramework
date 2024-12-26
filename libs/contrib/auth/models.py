from libs import models
from libs.contrib.contenttypes.models import ContentType


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
    certain status or publication date."

    The permissions listed above are automatically created for each model.
    """

    name = models.CharField("name", max_length=255)
    content_type = models.ForeignKey(
        ContentType,
        models.CASCADE,
        verbose_name="content type",
    )
    codename = models.CharField("codename", max_length=100)

    class Meta:
        verbose_name = "permission"
        verbose_name_plural = "permissions"
        unique_together = [["content_type", "codename"]]
        ordering = ["content_type__app_label", "content_type__model", "codename"]

    def __str__(self):
        return "%s | %s" % (self.content_type, self.name)


class Group(models.Model):
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
        through="qingkong_auth_group_permissions",
    )

    class Meta:
        verbose_name = "group"
        verbose_name_plural = "groups"

    def __str__(self):
        return self.name


class AbstractUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)

    email = models.EmailField(blank=True)

    is_active = models.BooleanField(default=True)

    last_login = models.DateTimeField("last login", blank=True, null=True)

    is_superuser = models.BooleanField(
        "superuser status",
        default=False,
        help_text=(
            "Designates that this user has all permissions without "
            "explicitly assigning them."
        ),
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name="groups",
        blank=True,
        help_text=(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="user_set",
        related_query_name="user",
        through="qingkong_auth_user_groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="user_set",
        related_query_name="user",
        through="qingkong_auth_user_permissions",
    )

    class Meta:
        abstract = True


class User(AbstractUser):
    class Meta(AbstractUser.Meta):
        abstract = False
