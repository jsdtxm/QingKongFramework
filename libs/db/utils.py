from itertools import chain
from typing import TYPE_CHECKING, List, Set, Type

from tortoise import Model, Tortoise
from tortoise.connection import connections
from tortoise.exceptions import ConfigurationError

if TYPE_CHECKING:  # pragma: nocoverage
    from tortoise.backends.base.client import BaseDBAsyncClient
    from tortoise.backends.base.schema_generator import BaseSchemaGenerator


def _get_models_to_create(
    self: "BaseSchemaGenerator",
    models_to_create: "List[Type[Model]]",
    apps: list[str] = None,
) -> None:
    from tortoise import Tortoise

    for name, app in Tortoise.apps.items():
        if apps and name not in apps:
            continue
        for model in app.values():
            if model._meta.db == self.client:
                model._check()
                models_to_create.append(model)


def get_create_schema_sql(
    self: "BaseSchemaGenerator", safe: bool = True, apps: list[str] = None
) -> str:
    models_to_create: "List[Type[Model]]" = []

    _get_models_to_create(self, models_to_create)

    tables_to_create = []
    for model in models_to_create:
        tables_to_create.append(self._get_table_sql(model, safe))

    tables_to_create_count = len(tables_to_create)

    created_tables: Set[dict] = set()
    ordered_tables_for_create: List[str] = []
    m2m_tables_to_create: List[str] = []
    while True:
        if len(created_tables) == tables_to_create_count:
            break
        try:
            next_table_for_create = next(
                t
                for t in tables_to_create
                if t["references"].issubset(created_tables | {t["table"]})
            )
        except StopIteration:
            raise ConfigurationError("Can't create schema due to cyclic fk references")
        tables_to_create.remove(next_table_for_create)
        created_tables.add(next_table_for_create["table"])
        if (model := next_table_for_create["model"]) and not getattr(
            getattr(model, "_meta", None), "external", False
        ):
            ordered_tables_for_create.append(
                next_table_for_create["table_creation_string"]
            )
        m2m_tables_to_create += next_table_for_create["m2m_tables"]

    return chain(ordered_tables_for_create + m2m_tables_to_create)


def get_schema_sql(client: "BaseDBAsyncClient", safe: bool, apps: list[str]) -> str:
    """
    Generates the SQL schema for the given client.

    :param client: The DB client to generate Schema SQL for
    :param safe: When set to true, creates the table only when it does not already exist.
    """
    generator = client.schema_generator(client)
    return get_create_schema_sql(generator, safe, apps)


async def generate_schema_for_client(
    client: "BaseDBAsyncClient", safe: bool, guided: bool, apps: list[str]
) -> None:
    """
    Generates and applies the SQL schema directly to the given client.

    :param client: The DB client to generate Schema SQL for
    :param safe: When set to true, creates the table only when it does not already exist.
    """
    generator = client.schema_generator(client)
    schema_list = get_schema_sql(client, safe, apps)
    for schema in schema_list:
        if not schema:  # pragma: nobranch
            continue

        print(schema)
        user_input = "Y"
        try:
            while guided:
                user_input = (
                    input(
                        "Please enter '[Y]' to execute the sql, 'N' to skip the sql, or 'Q' to quit: "
                    )
                    .strip()
                    .upper()
                )
                if user_input == "":
                    user_input = "Y"
                    break
                elif user_input not in ("Y", "N", "Q"):
                    print(f"Invalid input '{user_input}'")
                    continue
                else:
                    break
        except KeyboardInterrupt:
            return

        if user_input == "Y":
            await generator.generate_from_string(schema)
        elif user_input == "N":
            continue
        elif user_input == "Q":
            return


async def generate_schemas(
    cls: Tortoise, safe: bool = True, guided=False, apps: list[str] = None
) -> None:
    """
    Generate schemas according to models provided to ``.init()`` method.
    Will fail if schemas already exists, so it's not recommended to be used as part
    of application workflow

    :param safe: When set to true, creates the table only when it does not already exist.

    :raises ConfigurationError: When ``.init()`` has not been called.
    """
    if not cls._inited:
        raise ConfigurationError(
            "You have to call .init() first before generating schemas"
        )
    for connection in connections.all():
        await generate_schema_for_client(connection, safe, guided, apps or [])
