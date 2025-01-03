from typing import Any, Protocol


def action(methods=None, detail=None, url_path=None, **kwargs):
    """
    Mark a ViewSet method as a routable action.

    `@action`-decorated functions will be endowed with a `mapping` property,
    a `MethodMapper` that can be used to add additional method-based behaviors
    on the routed action.

    :param methods: A list of HTTP method names this action responds to.
                    Defaults to GET only.
    :param detail: Required. Determines whether this action applies to
                   instance/detail requests or collection/list requests.
    :param url_path: Define the URL segment for this action. Defaults to the
                     name of the method decorated.
    :param kwargs: Additional properties to set on the view.  This can be used
                   to override viewset-level *_classes settings, equivalent to
                   how the `@renderer_classes` etc. decorators work for function-
                   based API views.
    """
    methods = ["get"] if methods is None else methods
    methods = [method.lower() for method in methods]

    assert detail is not None, "@action() missing required argument: 'detail'"

    # name and suffix are mutually exclusive
    if "name" in kwargs and "suffix" in kwargs:
        raise TypeError("`name` and `suffix` are mutually exclusive arguments.")

    def decorator(func):
        func.methods = methods
        func.detail = detail
        func.url_path = url_path if url_path else func.__name__

        # These kwargs will end up being passed to `ViewSet.as_view()` within
        # the router, which eventually delegates to Django's CBV `View`,
        # which assigns them as instance attributes for each request.
        func.kwargs = kwargs

        return func

    return decorator


class ActionMethodMapper(Protocol):
    methods: list[str]
    detail: bool
    url_path: str
    kwargs: Any
