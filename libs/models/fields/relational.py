from typing import Any, Literal, Optional, Union, overload

from tortoise import Model
from tortoise.fields.base import CASCADE, OnDelete
from tortoise.fields.relational import (
    MODEL,
    ForeignKeyFieldInstance,
    ForeignKeyNullableRelation,
    ForeignKeyRelation,
    ManyToManyFieldInstance,
    ManyToManyRelation,
)

from . import utils


@overload
def ForeignKeyField(
    model_name: Union[str, Model],
    related_name: Union[Optional[str], Literal[False]] = None,
    on_delete: OnDelete = CASCADE,
    db_constraint: bool = True,
    *,
    null: Literal[True],
    **kwargs: Any,
) -> "ForeignKeyNullableRelation[MODEL]": ...


@overload
def ForeignKeyField(
    model_name: Union[str, Model],
    related_name: Union[Optional[str], Literal[False]] = None,
    on_delete: OnDelete = CASCADE,
    db_constraint: bool = True,
    null: Literal[False] = False,
    **kwargs: Any,
) -> "ForeignKeyRelation[MODEL]": ...


def ForeignKeyField(
    model_name: Union[str, Model],
    related_name: Union[Optional[str], Literal[False]] = None,
    on_delete: OnDelete = CASCADE,
    db_constraint: bool = True,
    null: bool = False,
    **kwargs: Any,
) -> "ForeignKeyRelation[MODEL] | ForeignKeyNullableRelation[MODEL]":
    """
    ForeignKey relation field.

    This field represents a foreign key relation to another model.

    See :ref:`foreign_key` for usage information.

    You must provide the following:

    ``model_name``:
        The name of the related model in a :samp:`'{app}.{model}'` format.

    The following is optional:

    ``related_name``:
        The attribute name on the related model to reverse resolve the foreign key.
    ``on_delete``:
        One of:
            ``field.CASCADE``:
                Indicate that the model should be cascade deleted if related model gets deleted.
            ``field.RESTRICT``:
                Indicate that the related model delete will be restricted as long as a
                foreign key points to it.
            ``field.SET_NULL``:
                Resets the field to NULL in case the related model gets deleted.
                Can only be set if field has ``null=True`` set.
            ``field.SET_DEFAULT``:
                Resets the field to ``default`` value in case the related model gets deleted.
                Can only be set is field has a ``default`` set.
            ``field.NO_ACTION``:
                Take no action.
    ``to_field``:
        The attribute name on the related model to establish foreign key relationship.
        If not set, pk is used
    ``db_constraint``:
        Controls whether or not a constraint should be created in the database for this foreign key.
        The default is True, and that’s almost certainly what you want; setting this to False can be very bad for data integrity.
    """

    if issubclass(model_name, Model):
        model_name = utils.model_object_to_name(model_name)

    return ForeignKeyFieldInstance(
        model_name,
        related_name,
        on_delete,
        db_constraint=db_constraint,
        null=null,
        **kwargs,
    )


def ManyToManyField(
    model_name: Union[str, Model],
    through: Optional[str] = None,
    forward_key: Optional[str] = None,
    backward_key: str = "",
    related_name: str = "",
    on_delete: OnDelete = CASCADE,
    db_constraint: bool = True,
    create_unique_index: bool = True,
    **kwargs: Any,
) -> "ManyToManyRelation[Any]":
    """
    ManyToMany relation field.

    This field represents a many-to-many between this model and another model.

    See :ref:`many_to_many` for usage information.

    You must provide the following:

    ``model_name``:
        The name of the related model in a :samp:`'{app}.{model}'` format.

    The following is optional:

    ``through``:
        The DB table that represents the through table.
        The default is normally safe.
    ``forward_key``:
        The forward lookup key on the through table.
        The default is normally safe.
    ``backward_key``:
        The backward lookup key on the through table.
        The default is normally safe.
    ``related_name``:
        The attribute name on the related model to reverse resolve the many to many.
    ``db_constraint``:
        Controls whether or not a constraint should be created in the database for this foreign key.
        The default is True, and that’s almost certainly what you want; setting this to False can be very bad for data integrity.
    ``on_delete``:
        One of:
            ``field.CASCADE``:
                Indicate that the model should be cascade deleted if related model gets deleted.
            ``field.RESTRICT``:
                Indicate that the related model delete will be restricted as long as a
                foreign key points to it.
            ``field.SET_NULL``:
                Resets the field to NULL in case the related model gets deleted.
                Can only be set if field has ``null=True`` set.
            ``field.SET_DEFAULT``:
                Resets the field to ``default`` value in case the related model gets deleted.
                Can only be set is field has a ``default`` set.
            ``field.NO_ACTION``:
                Take no action.
    ``create_unique_index``:
        Controls whether or not a unique index should be created in the database to speed up select queries.
        The default is True. If you want to allow repeat records, set this to False.
    """

    if issubclass(model_name, Model):
        model_name = utils.model_object_to_name(model_name)

    return ManyToManyFieldInstance(  # type: ignore
        model_name,
        through,
        forward_key,
        backward_key,
        related_name,
        on_delete=on_delete,
        db_constraint=db_constraint,
        create_unique_index=create_unique_index,
        **kwargs,
    )
