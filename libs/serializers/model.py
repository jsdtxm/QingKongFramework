from typing import Tuple, Type

from libs.serializers.base import Serializer, SerializerMetaclass
from libs.serializers.creator import pydantic_model_creator


class ModelSerializerMetaclass(SerializerMetaclass):
    # TODO
    # read_only_fields = ['account_name']
    # extra_kwargs = {'password': {'write_only': True}}
    # validators = [
    #             UniqueTogetherValidator(
    #                 queryset=Event.objects.all(),
    #                 fields=['room_number', 'date']
    #             )
    #         ]
    def __new__(mcs, name: str, bases: Tuple[Type, ...], attrs: dict):
        if meta := attrs.get("Meta", None):
            pydantic_meta = getattr(meta.model, "PydanticMeta", None)
            if pydantic_meta is None:
                fields = getattr(meta, "fields", ())
                exclude = getattr(meta, "exclude", ())
                if fields:
                    assert not (fields and exclude), (
                        "Cannot set both 'fields' and 'exclude' options on "
                        "serializer {serializer_class}.".format(serializer_class=name)
                    )
                    if fields == "__all__":
                        fields, exclude = (), ()

                pydantic_meta = type(
                    "PydanticMeta",
                    (),
                    {
                        k: v
                        for k, v in {
                            "include": fields,
                            "exclude": exclude,
                            "max_recursion": getattr(meta, "depth", None),
                        }.items()
                        if v is not None
                    },
                )
                meta.model.PydanticMeta = pydantic_meta

            return pydantic_model_creator(meta.model)

        return super(SerializerMetaclass, mcs).__new__(mcs, name, bases, attrs)


class ModelSerializer(Serializer, metaclass=ModelSerializerMetaclass):
    """
    ModelSerializer
    ```python
    class PolyAiDoiSerializer(ModelSerializer):
        class Meta:
            model = ModelName
            fields = (field1, field2)
            exclude = (field1, field2)
    ```
    """

    pass
