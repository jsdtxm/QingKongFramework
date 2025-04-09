from itertools import chain
from typing import TYPE_CHECKING, List, Set, Type

from tortoise import Model, Tortoise
from tortoise.connection import connections
from tortoise.exceptions import ConfigurationError

from fastapp.db.backends.sqlite import SqliteClient

if TYPE_CHECKING:
    from tortoise.backends.base.client import BaseDBAsyncClient
    from tortoise.backends.base.schema_generator import BaseSchemaGenerator


def _get_models_to_create(
    self: "BaseSchemaGenerator",
    models_to_create: "List[Type[Model]]",
    apps: list[str] = None,
) -> None:
    from tortoise import Tortoise

    for name, app in Tortoise.apps.items():
        if apps and (name not in apps):
            continue
        for model in app.values():
            if model._meta.db == self.client:
                model._check()
                models_to_create.append(model)

    return models_to_create


def generate_hypertable_sql(table_name: str, config: dict) -> str:
    """
    生成TimescaleDB的create_hypertable SQL语句

    :param table_name: 目标表名
    :param config: 配置字典，包含：
        - time_column_name: 必选，时间字段名
        - partitioning_column: 可选，空间分区字段
        - number_partitions: 可选，空间分片数量
        - chunk_time_interval: 可选，分片时间间隔（默认'7 days'）
    :return: 完整的SQL语句
    """
    # 参数校验
    if "time_column_name" not in config:
        raise ValueError("必须指定 time_column_name")

    time_col = config["time_column_name"]
    partitioning_col = config.get("partitioning_column")
    num_partitions = config.get("number_partitions")
    chunk_interval = config.get("chunk_time_interval", "7 days")

    # 空间分区校验
    if (partitioning_col and not num_partitions) or (
        num_partitions and not partitioning_col
    ):
        raise ValueError("partitioning_column 和 number_partitions 必须同时存在")

    # 构建参数列表
    params = [f"'{table_name}'", f"'{time_col}'"]

    # 添加命名参数
    named_params = []
    if partitioning_col and num_partitions:
        named_params.append(f"partitioning_column => '{partitioning_col}'")
        named_params.append(f"number_partitions => {num_partitions}")

    # 始终使用命名参数传递时间间隔
    named_params.append(f"chunk_time_interval => INTERVAL '{chunk_interval}'")

    # 合并所有参数
    full_params = params + named_params

    result_sql = f"""
    DO $$
    DECLARE
        pk_name TEXT;
    BEGIN
        -- 获取当前主键约束的名称
        SELECT constraint_name INTO pk_name
        FROM information_schema.table_constraints 
        WHERE table_name = '{table_name}' AND constraint_type = 'PRIMARY KEY';
            
        -- 检查是否找到主键
        IF pk_name IS NOT NULL THEN
            -- 删除现有的主键
            EXECUTE 'ALTER TABLE {table_name} DROP CONSTRAINT ' || quote_ident(pk_name);
        END IF;

        -- 添加新的主键 (再考虑考虑需要不需要吧)
        -- EXECUTE 'ALTER TABLE {table_name} ADD PRIMARY KEY (id, {time_col}{f", {partitioning_col}" if partitioning_col else ""})';
    END $$;
    """

    result_sql += f"\nSELECT create_hypertable({', '.join(full_params)});"

    if compress_segmentby := config.get("compress_segmentby"):
        result_sql += f"\nALTER TABLE {table_name} SET (timescaledb.compress, timescaledb.compress_segmentby = '{compress_segmentby}');"

    if compression_policy := config.get("compression_policy"):
        result_sql += f"\nSELECT add_compression_policy('{table_name}', INTERVAL '{compression_policy}');"

    return result_sql


def get_create_schema_sql(
    self: "BaseSchemaGenerator", safe: bool = True, apps: list[str] = None
) -> []:
    models_to_create: "List[Type[Model]]" = []

    models_to_create = _get_models_to_create(self, models_to_create, apps)

    extra_sql = []

    tables_to_create = []
    for model in models_to_create:
        data = self._get_table_sql(model, safe)
        if hypertable := getattr(model.Meta, "hypertable", None):
            extra_sql.append(generate_hypertable_sql(model._meta.db_table, hypertable))

        if model._meta.is_managed:
            tables_to_create.append(data)

    if not tables_to_create:
        return []

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
        if (model := next_table_for_create["model"]) and getattr(
            getattr(model, "_meta", None), "is_managed", True
        ):
            ordered_tables_for_create.append(
                next_table_for_create["table_creation_string"]
            )
        m2m_tables_to_create += next_table_for_create["m2m_tables"]

    return chain(ordered_tables_for_create + m2m_tables_to_create + extra_sql)


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
    cls: Type[Tortoise], safe: bool = True, guided=False, apps: list[str] = None
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
        if isinstance(connection, SqliteClient):
            print(connection.filename)
        else:
            print(
                f"{connection.user}@{connection.host}:{connection.port}",
                connection.database,
            )
        await generate_schema_for_client(connection, safe, guided, apps or [])
