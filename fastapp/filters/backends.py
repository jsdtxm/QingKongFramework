from fastapp.filters import filterset
from fastapp.requests import DjangoStyleRequest


class FilterBackend:
    filterset_base = filterset.FilterSet
    raise_exception = True

    def get_filterset(self, request, queryset, view):
        filterset_class = self.get_filterset_class(view, queryset)
        if filterset_class is None:
            return None

        kwargs = self.get_filterset_kwargs(request, queryset, view)
        return filterset_class(**kwargs)

    def get_filterset_class(self, view, queryset=None):
        """
        Return the `FilterSet` class used to filter the queryset.
        """
        filterset_class = getattr(view, "filterset_class", None)

        if filterset_class:
            return filterset_class

        filterset_fields = getattr(view, "filterset_fields", None)

        if filterset_fields and queryset is not None:
            MetaBase = getattr(self.filterset_base, "Meta", object)

            class AutoFilterSet(self.filterset_base):
                class Meta(MetaBase):
                    model = queryset.model
                    fields = filterset_fields

            return AutoFilterSet

        return None

    def get_filterset_kwargs(self, request: DjangoStyleRequest, queryset, view):
        return {
            "data": request.GET,
            "queryset": queryset,
            "request": request,
        }

    def filter_queryset(self, request, queryset, view):
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset

        return filterset.qs
