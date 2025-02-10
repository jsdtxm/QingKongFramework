import re
from functools import update_wrapper
from inspect import getmembers
from typing import (
    Any,
    Generic,
    Iterable,
    List,
    Literal,
    Optional,
    Self,
    Tuple,
    Type,
    Union,
    overload,
)

from fastapi.routing import APIRouter
from pydantic import BaseModel, SkipValidation
from starlette.requests import Request
from tortoise.queryset import MODEL
from tortoise.queryset import QuerySet as TortoiseQuerySet

from libs import exceptions, serializers
from libs.contrib.auth.utils import OptionalCurrentUser
from libs.models import BaseModel as BaseDBModel
from libs.models import Manager, Model, get_object_or_404
from libs.permissions.base import BasePermission
from libs.requests import DjangoStyleRequest
from libs.responses import JSONResponse
from libs.utils.functional import classonlymethod, copy_method_signature
from libs.utils.module_loading import import_string
from libs.views import mixins
from libs.views.class_based import View, ViewWrapper
from libs.views.decorators import ActionMethodMapper
from libs.utils.strings import split_camel_case

DEFAULTS = {
    "DEFAULT_PERMISSION_CLASSES": [
        "libs.permissions.AllowAny",
    ],
}

REST_ACTION_METHOD_MAPPING = {
    "list": ["get"],
    "retrieve": ["get"],
    "create": ["post"],
    "update": ["put"],
    "destroy": ["delete"],
}

def view_set_name_clear(cls_name: str) -> str:
    return ' '.join(split_camel_case(cls_name.replace('ViewSet', '')))


class ViewSetRouteItem:
    def __init__(self, action, url, methods):
        self.action = action
        self.url = url
        self.methods = methods


BRACE_REGEX = re.compile(r"\{([a-zA-Z0-9_]+)\}")


class GenericViewSetWrapper(ViewWrapper):
    view_class: Type["GenericViewSet"]

    def get_typed_view(self, view, method: str):
        view.__name__ = f"{view_set_name_clear(self.view_class.__name__)}_{method}"

        return view

    def get_routers(self, viewset: "GenericViewSet") -> Iterable[ViewSetRouteItem]:
        routers = []

        for name, action in viewset.get_actions():
            methods = REST_ACTION_METHOD_MAPPING[name]
            detail = name in {"retrieve", "update", "destroy"}

            routers.append(ViewSetRouteItem(name, "/{id}/" if detail else "/", methods))

        for name, action in viewset.get_extra_actions():
            detail = getattr(action, "detail", False)

            routers.append(
                ViewSetRouteItem(
                    name,
                    ("/{id}/" if detail else "/") + action.url_path + "/",
                    action.methods,
                )
            )

        return routers

    def view(self, route: ViewSetRouteItem):  # type: ignore
        matches = re.findall(BRACE_REGEX, route.url)

        extra_params = [f"{match}: int" for match in matches]
        if route.action in ("create", "update"):
            extra_params.append(
                "body: "
                + (
                    "SkipValidation[serializer_class]"
                    if route.action == "update"
                    else "serializer_class"
                )
            )

        extra_params_str = ", ".join(extra_params)
        extra_params_send = ", ".join([f"{match}={match}" for match in matches])

        function_definition = f"""def view_wrapper_factory(route, self):
    async def view_wrapper(request: Request, user: OptionalCurrentUser, {extra_params_str}):
        return await self.view_method(
            route.action, await self.django_request_adapter(request, user), {extra_params_send} 
        )
    return view_wrapper"""

        # HACK for get_serializer_class
        route.serializer_class = self.view_class.serializer_class

        local_env = {}
        exec(
            function_definition,
            {
                "Request": Request,
                "SkipValidation": SkipValidation,
                "OptionalCurrentUser": OptionalCurrentUser,
                "serializer_class": self.view_class.get_serializer_class(route),
            },
            local_env,
        )

        return local_env["view_wrapper_factory"](route, self)

    def as_router(self, name=None, response_model=None, response_class=None):
        # AS Router
        
        router = APIRouter()
        for route_item in self.get_routers(self.view_class):
            router.add_api_route(
                route_item.url,
                self.get_typed_view(self.view(route_item), route_item.action),
                name=name,
                tags=[view_set_name_clear(self.view_class.__name__),],
                methods=route_item.methods,
                response_model=response_model,
                response_class=response_class,
                include_in_schema=True,
            )

        return router


def _is_extra_action(attr):
    return hasattr(attr, "detail")


def _check_attr_name(name, func):
    assert func.__name__ == name, (
        "Expected function (`{func.__name__}`) to match its attribute name "
        "(`{name}`). If using a decorator, ensure the inner function is "
        "decorated with `functools.wraps`, or that `{func.__name__}.__name__` "
        "is otherwise set to `{name}`."
    ).format(func=func, name=name)
    return name, func


def load_classes(classes_string_list: list[str]) -> list[Type[BasePermission]]:
    return [import_string(permission) for permission in classes_string_list]


class APIView(View):
    permission_classes = load_classes(DEFAULTS["DEFAULT_PERMISSION_CLASSES"])

    def permission_denied(self, request: DjangoStyleRequest, message=None, code=None):
        """
        If request is not permitted, determine what kind of exception to raise.
        """
        if request.user is None:
            raise exceptions.NotAuthenticated()
        raise exceptions.PermissionDenied(detail=message, code=code)

    def get_permissions(self) -> list[BasePermission]:
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]

    def check_permissions(self, request):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                self.permission_denied(
                    request,
                    message=getattr(permission, "message", None),
                    code=getattr(permission, "code", None),
                )

    async def check_object_permissions(self, request, obj):
        """
        Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request,
                    message=getattr(permission, "message", None),
                    code=getattr(permission, "code", None),
                )


class ListSerializerWrapper:
    data: List[BaseModel]

    @copy_method_signature(BaseModel.model_dump)
    def model_dump(self, *args, **kwargs):
        return [x.model_dump(*args, **kwargs) for x in self.data]

    def __init__(self, data):
        self.data = data


class GenericAPIView(Generic[MODEL], APIView):
    """
    Base class for all other generic views.
    """

    # You'll need to either set these attributes,
    # or override `get_queryset()`/`get_serializer_class()`.
    # If you are overriding a view method, it is important that you call
    # `get_queryset()` instead of accessing the `queryset` property directly,
    # as `queryset` will get evaluated only once, and those results are cached
    # for all subsequent requests.
    queryset: Union[TortoiseQuerySet[MODEL], Manager[MODEL], MODEL]
    serializer_class: Optional[Type[serializers.BaseSerializer]] = None

    # If you want to use object lookups other than pk, set 'lookup_field'.
    # For more complex lookup requirements override `get_object()`.
    lookup_field = "id"
    lookup_url_kwarg = None

    # The filter backend classes to use for queryset filtering
    # filter_backends = api_settings.DEFAULT_FILTER_BACKENDS

    # The style to use for queryset pagination.
    # pagination_class = api_settings.DEFAULT_PAGINATION_CLASS
    pagination_class = None

    # Allow generic typing checking for generic views.
    def __class_getitem__(cls, *args, **kwargs):
        return cls

    def get_queryset(self):
        """
        Get the list of items for this view.
        This must be an iterable, and may be a queryset.
        Defaults to using `self.queryset`.

        This method should always be used rather than accessing `self.queryset`
        directly, as `self.queryset` gets evaluated only once, and those results
        are cached for all subsequent requests.

        You may want to override this if you need to provide different
        querysets depending on the incoming request.

        (Eg. return a list of items that is specific to the user)
        """
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method." % self.__class__.__name__
        )

        queryset = self.queryset
        if isinstance(queryset, type) and issubclass(queryset, Model):
            queryset = queryset.objects.all()
        elif isinstance(queryset, TortoiseQuerySet):
            queryset = queryset.all()
        return queryset

    async def get_object(self):
        """
        Returns the object the view is displaying.

        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = await self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            "Expected view %s to be called with a URL keyword argument "
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            "attribute on the view correctly."
            % (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = await get_object_or_404(queryset, **filter_kwargs)

        # May raise a permission denied
        await self.check_object_permissions(self.request, obj)

        return obj

    def get_serializer_class(
        self, override_action: Optional[str] = None
    ) -> Type[serializers.BaseSerializer]:
        """
        Return the class to use for the serializer.
        Defaults to using `self.serializer_class`.

        You may want to override this if you need to provide different
        serializations depending on the incoming request.

        (Eg. admins get full serialization, others get basic serialization)
        """
        assert self.serializer_class is not None, (
            "'%s' should either include a `serializer_class` attribute, "
            "or override the `get_serializer_class()` method." % self.__class__.__name__
        )

        return self.serializer_class

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {"request": self.request, "view": self}

    @overload
    async def get_serializer(
        self,
        instance: Any = None,
        data: Any = None,
        many: Optional[bool] = False,
        **kwargs,
    ) -> serializers.BaseSerializer: ...

    @overload
    async def get_serializer(
        self,
        instance: Any = None,
        data: Any = None,
        many: Literal[True] = True,
        **kwargs,
    ) -> ListSerializerWrapper: ...

    @overload
    async def get_serializer(
        self,
        instance: Any = None,
        data: Any = None,
        many: Literal[False] = False,
        **kwargs,
    ) -> serializers.BaseSerializer: ...

    async def get_serializer(
        self,
        instance: Any = None,
        data: Any = None,
        many: Optional[bool] = False,
        override_action: Optional[str] = None,
        **kwargs,
    ) -> ListSerializerWrapper | serializers.BaseSerializer:
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.

        override_action: override self.action
        """
        serializer_class = self.get_serializer_class(override_action=override_action)
        if isinstance(instance, TortoiseQuerySet):
            return ListSerializerWrapper(await serializer_class.from_queryset(instance))
        elif isinstance(instance, list):
            return ListSerializerWrapper(
                [serializer_class.model_validate(x) for x in instance]
            )

        if data is not None:
            if instance is None:
                return serializer_class.model_validate(data)
            else:
                instance = instance.update_from_dict(data)
                serializer = await serializer_class.from_tortoise_orm(instance)
                return serializer

        if isinstance(instance, BaseDBModel):
            return await serializer_class.from_tortoise_orm(instance)

        return serializer_class.model_validate(instance)

    async def filter_queryset(self, queryset):
        """
        Given a queryset, filter it with whichever filter backend is in use.

        You are unlikely to want to override this method, although you may need
        to call it either from a list view, or from a custom `get_object`
        method if you want to apply the configured filtering backend to the
        default queryset.
        """
        # for backend in list(self.filter_backends):
        #     queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, "_paginator"):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        # if self.paginator is None:
        #     return None
        # return self.paginator.paginate_queryset(queryset, self.request, view=self)
        return None

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        # assert self.paginator is not None
        # return self.paginator.get_paginated_response(data)

        return JSONResponse(data)


class GenericViewSet(GenericAPIView):
    action: str

    wrapper_class = GenericViewSetWrapper
    serializer_class: Optional[Type[serializers.ModelSerializer]] = None

    @classmethod
    def get_actions(cls):
        actions = []
        for name in REST_ACTION_METHOD_MAPPING:
            if method := getattr(cls, name, None):
                actions.append((name, method))
        return actions

    @classmethod
    def get_extra_actions(cls) -> List[Tuple[str, ActionMethodMapper]]:
        return [
            _check_attr_name(name, method)
            for name, method in getmembers(cls, _is_extra_action)
        ]

    @classonlymethod  # type: ignore
    def as_view(cls, **initkwargs):
        """Main entry point for a request-response process."""
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError(
                    "The method name %s is not accepted as a keyword argument "
                    "to %s()." % (key, cls.__name__)
                )
            if not hasattr(cls, key):
                raise TypeError(
                    "%s() received an invalid keyword %r. as_view "
                    "only accepts arguments that are already "
                    "attributes of the class." % (cls.__name__, key)
                )

        def view(action: str, request: Request, *args, **kwargs):
            self: Self = cls(**initkwargs)  # type: ignore
            self.action = action
            self.setup(request, *args, **kwargs)
            if not hasattr(self, "request"):
                raise AttributeError(
                    "%s instance has no 'request' attribute. Did you override "
                    "setup() and forget to call super()?" % cls.__name__  # type: ignore
                )
            return self.dispatch(request, *args, **kwargs)

        # view.view_class = cls
        # view.view_initkwargs = initkwargs

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())

        return cls.wrapper_class(view, cls, initkwargs)

    def setup(self, request: Request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.kwargs = kwargs

    def dispatch(self, request: Request, *args, **kwargs):
        handler = getattr(self, self.action, self.http_method_not_allowed)

        return handler(request, *args, **kwargs)


class ReadOnlyModelViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet
):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """

    pass


class ModelViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """
    A viewset that provides default `list()` and `retrieve()` actions.
    """

    pass
