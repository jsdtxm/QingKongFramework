from typing import Any, Literal, Optional, Union, overload

from tortoise import Model
from tortoise.fields.base import CASCADE, OnDelete
from tortoise.fields.relational import (
    MODEL,
    ForeignKeyFieldInstance,
    ForeignKeyNullableRelation,
    ForeignKeyRelation,
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
        app = utils.exact_app_name(model_name.__module__)
        model_name = f"{app}.{model_name.__name__}"

    return ForeignKeyFieldInstance(
        model_name,
        related_name,
        on_delete,
        db_constraint=db_constraint,
        null=null,
        **kwargs,
    )
