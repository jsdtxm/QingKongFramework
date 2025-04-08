from fastapp.contrib.auth import get_user_model
from fastapp.contrib.auth.models import Group
from fastapp.contrib.guardian.exceptions import NotUserNorGroup
from fastapp.models import QuerySet
from fastapp.utils.module_loading import import_string


def get_identity(identity):
    """Get a tuple with the identity of the given input.

    Returns a tuple with one of the members set to `None` depending on whether the input is
    a `Group` instance or a `User` instance.
    Also accepts AnonymousUser instance but would return `User` instead.
    It is convenient and needed for authorization backend to support anonymous users.

    Returns:
         identity (tuple): Either (user_obj, None) or (None, group_obj) depending on the input type.

    Parameters:
        identity (User | Group): Instance of `User` or `Group` to get identity from.

    Raises:
        NotUserNorGroup: If the function cannot return proper identity instance

    Examples:
        ```shell
        >>> from django.contrib.auth.models import User
        >>> user = User.objects.create(username='joe')
        >>> get_identity(user)
        (<User: joe>, None)

        >>> group = Group.objects.create(name='users')
        >>> get_identity(group)
        (None, <Group: users>)

        >>> anon = AnonymousUser()
        >>> get_identity(anon)
        (<User: AnonymousUser>, None)

        >>> get_identity("not instance")
        ...
        NotUserNorGroup: User/AnonymousUser or Group instance is required (got )
        ```
    """

    # get identity from queryset model type
    if isinstance(identity, QuerySet):
        identity_model_type = identity.model
        if identity_model_type == get_user_model():
            return identity, None
        elif identity_model_type == Group:
            return None, identity

    # get identity from first element in list
    if isinstance(identity, list) and isinstance(identity[0], get_user_model()):
        return identity, None
    if isinstance(identity, list) and isinstance(identity[0], Group):
        return None, identity

    if isinstance(identity, get_user_model()):
        return identity, None
    if isinstance(identity, Group):
        return None, identity

    raise NotUserNorGroup(
        "User/AnonymousUser or Group instance is required " "(got %s)" % identity
    )


def get_user_obj_perms_model_class():
    return import_string("fastapp.contrib.guardian.models.UserObjectPermission")


def get_group_obj_perms_model_class():
    return import_string("fastapp.contrib.guardian.models.GroupObjectPermission")
