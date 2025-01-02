from typing import Type

from libs.contrib.auth.typing import UserProtocol
from libs.exceptions import ImproperlyConfigured
from libs.utils.module_loading import import_string


def get_user_model() -> Type[UserProtocol]:
    """
    Return the User model that is active in this project.
    """
    from common.settings import settings

    try:
        return import_string(settings.AUTH_USER_MODEL)
    except ValueError:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL refers to model '%s' that has not been installed"
            % settings.AUTH_USER_MODEL
        )
