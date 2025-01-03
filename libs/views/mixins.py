from libs.responses import Response


class RetrieveModelMixin:
    """
    Retrieve a model instance.
    """

    async def retrieve(self, request, *args, **kwargs):
        print("retrieve")
        return {}
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ListModelMixin:
    """
    List a queryset.
    """
    async def list(self, request, *args, **kwargs):
        print("retrieve")
        return {}
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
