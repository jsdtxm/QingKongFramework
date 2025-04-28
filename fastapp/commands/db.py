"""
数据库相关命令行工具模块

该模块提供了与数据库操作相关的命令行工具，包括：
- 数据库迁移（migrate）
- 自动迁移（auto_migrate）
- 反向生成模型（reverse_generation）

模块主要功能：
1. 处理数据库迁移操作，包括安全迁移和引导迁移
2. 从数据库表结构反向生成 Django 模型
3. 自动生成数据库变更脚本
4. 处理与内容类型、权限相关的数据库初始化
"""

import asyncio
from itertools import chain

import click

from common.settings import settings
from fastapp.commands.decorators import async_init_fastapp
from fastapp.db import connections
from fastapp.db.migrate import generate_diff_sql, parse_sql
from fastapp.db.utils import generate_schemas
from fastapp.initialize.apps import init_apps
from fastapp.initialize.db import async_init_db, get_tortoise_config
from fastapp.models.tortoise import Tortoise
from fastapp.tools.get_table_structure import SchemaExporter
from fastapp.tools.reverse_generation import table_to_django_model

INTERNAL_CONTENTTYPES_APP_LABEL = "fastapp.contrib.contenttypes"
INTERNAL_AUTH_APP_LABEL = "fastapp.contrib.auth"
INTERNAL_GUARDIAN_APP_LABEL = "fastapp.contrib.guardian"


async def async_migrate(safe, guided, apps):
    """
    此函数用于异步执行数据库迁移操作。

    Args:
        safe (bool): 表示是否安全迁移。
        guided (bool): 表示是否进行引导迁移。
        apps (list): 要处理的应用列表。
    """
    auth_app_enabled = INTERNAL_AUTH_APP_LABEL in settings.INSTALLED_APPS
    guardian_app_enabled = INTERNAL_GUARDIAN_APP_LABEL in settings.INSTALLED_APPS
    content_type_app_enabled = (
        INTERNAL_CONTENTTYPES_APP_LABEL in settings.INSTALLED_APPS
    )

    if auth_app_enabled and not content_type_app_enabled:
        click.echo(
            f"ERROR {INTERNAL_AUTH_APP_LABEL} required {INTERNAL_CONTENTTYPES_APP_LABEL}"
        )
        return

    if guardian_app_enabled and not auth_app_enabled:
        click.echo(
            f"ERROR {INTERNAL_GUARDIAN_APP_LABEL} required {INTERNAL_AUTH_APP_LABEL}"
        )
        return

    init_apps(settings.INSTALLED_APPS)
    await async_init_db(get_tortoise_config(settings.DATABASES))
    await generate_schemas(Tortoise, safe=safe, guided=guided, apps=apps)

    if len(apps) > 0:
        await Tortoise.close_connections()

        return

    if content_type_app_enabled:
        from fastapp.contrib.contenttypes.models import ContentType

    if auth_app_enabled:
        from fastapp.contrib.auth.models import DefaultPerms, Permission

    # TODO object permission anonymous user

    if content_type_app_enabled:
        # TODO 如果新建模型，不能自动添加content_type
        for x in sorted(
            chain.from_iterable(
                sub_dict.values() for sub_dict in Tortoise.apps.values()
            ),
            key=lambda x: x._meta.app_config.label,
        ):
            content_type, _ = await ContentType.get_or_create(
                app_label=x._meta.app_config.label, model=x.__name__
            )

            if auth_app_enabled:
                for p in DefaultPerms:
                    await Permission.get_or_create(content_type=content_type, perm=p)

        conn = Tortoise.get_connection(ContentType._meta.default_connection)
        if "PostgreSQL" in conn.__class__.__name__:
            table = ContentType._meta.db_table
            res = await conn.execute_query(f'''SELECT setval(
                pg_get_serial_sequence('{table}', 'id'),
                COALESCE((SELECT MAX("id") FROM "{table}"), 1)
            );''')
            print("setval", res)

    await Tortoise.close_connections()


@click.option("--safe", default=True)
@click.option("--guided", default=True)
@click.option("--apps", multiple=True)
def migrate(safe=True, guided=True, apps=None):
    """
    此函数用于执行数据库迁移操作。

    Args:
        safe (bool): 表示是否安全迁移，默认为 True。
        guided (bool): 表示是否进行引导迁移，默认为 True。
        apps (list): 要处理的应用列表，默认为 None。
    """
    if apps is None:
        apps = []
    asyncio.run(async_migrate(safe, guided, apps))


async def print_result(func, *args, **kwargs):
    """
    此函数用于异步调用指定的函数，并打印其返回结果。

    Args:
        func (callable): 要调用的函数。
        *args: 传递给函数的位置参数。
        **kwargs: 传递给函数的关键字参数。
    """
    print(await func(*args, **kwargs))


@click.argument("table")
@click.option("--connection", default="default")
@click.option("--db", default=None)
def reverse_generation(connection, db, table):
    """
    此函数用于从数据库表反向生成 Django 模型。

    Args:
        connection (str): 数据库连接名称。
        db (str): 数据库名称。
        table (str): 要反向生成的表名。
    """
    db_config = settings.DATABASES[connection]

    asyncio.run(
        print_result(
            table_to_django_model,
            {
                "host": db_config["HOST"],
                "port": db_config["PORT"],
                "user": db_config["USER"],
                "password": db_config["PASSWORD"],
                "db": db or db_config["NAME"],
            },
            table,
        )
    )


@async_init_fastapp
async def async_auto_migrate(apps: list[str], guided: bool = True):
    """
    异步自动迁移数据库的函数。

    此函数会处理指定应用的数据库迁移，通过比较旧的和新的数据库模式，生成并打印数据库变更脚本。

    Args:
        apps (list[str]): 要处理的应用列表。
    """
    process_apps = []
    for app in Tortoise.apps:
        if not apps or app in apps:
            process_apps.append(app)

    alert_sql_list = []
    for app in process_apps:
        for model in Tortoise.apps[app].values():
            if not model._meta.is_managed:  # pylint: disable=W0212
                continue

            table = model._meta.db_table  # pylint: disable=W0212

            exporter = SchemaExporter(
                "default",
                [
                    table,
                ],
            )
            res = await exporter.export()

            conn = connections["default"]

            generator = conn.schema_generator(conn)

            sql = generator._get_table_sql(model, True)  # pylint: disable=W0212

            conn_class_name = conn.__class__.__name__
            if "PostgreSQL" in conn_class_name:
                dialect = "Postgres"
            elif "MySQL" in conn_class_name:
                dialect = "MySQL"
            elif "Sqlite" in conn_class_name:
                dialect = "SQLite"
            else:
                raise ValueError(f"Unsupported database: {conn_class_name}")

            old_schema = parse_sql(res, True, dialect.lower())
            new_schema = parse_sql(sql["table_creation_string"], True, dialect.lower())

            changes = generate_diff_sql(old_schema, new_schema, dialect.lower())

            if changes and changes[0]:
                alert_sql = "\n".join(changes[0])
                alert_sql_list.append(alert_sql)

    for alert_sql in alert_sql_list:
        if not alert_sql:
            continue

        print(alert_sql)

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
            await conn.execute_query(alert_sql)
        elif user_input == "N":
            continue
        elif user_input == "Q":
            return


@click.option("--apps", multiple=True)
@click.option("--guided", default=True)
def auto_migrate(apps, guided):
    """
    自动迁移数据库的函数。

    此函数会调用异步自动迁移函数 `async_auto_migrate` 来处理数据库迁移。

    Args:
        apps (list[str]): 要处理的应用列表。
    """
    asyncio.run(async_auto_migrate(apps, guided))
