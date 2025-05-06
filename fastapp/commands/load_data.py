import asyncio
import json
import os
from functools import lru_cache

import click

from common.settings import settings
from fastapp.initialize.apps import init_apps
from fastapp.initialize.db import async_init_db, get_tortoise_config
from fastapp.models.tortoise import Tortoise
from fastapp.utils.json import remove_comments


def find_file_in_fixtures(folders, filename):
    """
    在给定的文件夹列表中查找特定文件名。

    :param folders: 包含要搜索的顶级文件夹路径的列表。
    :param filename: 要查找的文件名。
    :return: 包含找到的文件的完整路径的列表。
    """
    found_files = []

    for folder in folders:
        # 构建目标子文件夹的路径
        fixtures_path = os.path.join(folder, "fixtures")

        # 检查子文件夹是否存在
        if os.path.isdir(fixtures_path):
            # 遍历子文件夹中的所有文件和子文件夹
            for root, dirs, files in os.walk(fixtures_path):
                if filename in files:
                    # 如果找到了文件，添加其完整路径到结果列表中
                    found_files.append(os.path.join(root, filename))

    return found_files


def get_all_fixtures(folders):
    found_files = []

    for folder in folders:
        # 构建目标子文件夹的路径
        fixtures_path = os.path.join(folder, "fixtures")

        # 检查子文件夹是否存在
        if os.path.isdir(fixtures_path):
            # 遍历子文件夹中的所有文件和子文件夹
            for root, dirs, files in os.walk(fixtures_path):
                for filename in files:
                    if filename.endswith(".json") or filename.endswith(".jsonc"):
                        found_files.append(os.path.join(root, filename))

    return sorted(found_files)


@lru_cache
def _get_model_fk_id_fields_dict(model):
    fk_fields = {}
    for field_name in model._meta.fk_fields:
        field = model._meta.fields_map[field_name]
        fk_fields[field.source_field] = field.related_model

    return fk_fields


async def _handle_fields(model, fields):
    fk_fields_dict = _get_model_fk_id_fields_dict(model)

    for k, v in fields.items():
        if k in fk_fields_dict and isinstance(v, str) and v.startswith("${"):
            obj = await fk_fields_dict[k].get(**dict((v[2:-1].split("="),)))
            fields[k] = obj.id

    return fields


async def _loaddata_inner(file_path):
    if "/" not in file_path and not os.path.exists(file_path):
        app_dirs = list(
            map(
                lambda x: x.replace(".", "/"),
                filter(lambda x: x.startswith("apps"), settings.INSTALLED_APPS),
            )
        )
        files = find_file_in_fixtures(app_dirs, file_path)
        if len(files) > 1:
            raise Exception(
                "Multiple files found with the same name in different apps."
            )
        elif len(files) == 1:
            file_path = files[0]

    with open(file_path, "r") as f:
        data = json.loads(remove_comments(f.read()))
        for item in data:
            app, model_name = item["model"].split(".")
            model = Tortoise.apps.get(app, {}).get(model_name)

            fields = await _handle_fields(model, item["fields"])

            if item.get("pk", None) is None:
                instance = model(**fields)
                await instance.save()
                continue

            if await model.objects.filter(id=item["pk"]).exists():
                await model.objects.filter(id=item["pk"]).update(**fields)
                continue

            instance = model(id=item["pk"], **fields)
            await instance.save()

        conn = Tortoise.get_connection(model._meta.default_connection)
        if "PostgreSQL" in conn.__class__.__name__:
            table = model._meta.db_table
            res = await conn.execute_query(f'''SELECT setval(
                pg_get_serial_sequence('{table}', 'id'),
                COALESCE((SELECT MAX("id") FROM "{table}"), 1)
            );''')
            print("setval", res)


async def _loaddata(file_path):
    init_apps(settings.INSTALLED_APPS)
    await async_init_db(get_tortoise_config(settings.DATABASES))

    if file_path == "all":
        app_dirs = list(
            map(
                lambda x: x.replace(".", "/"),
                filter(lambda x: x.startswith("apps"), settings.INSTALLED_APPS),
            )
        )
        files = sorted(
            get_all_fixtures(app_dirs),
            key=lambda x: (
                int(os.path.basename(x).split("_", 1)[0]),
                os.path.basename(x),
            ),
        )
        for file in files:
            print(file)
            await _loaddata_inner(file)
    else:
        await _loaddata_inner(file_path)

    await Tortoise.close_connections()


@click.argument("file_path", type=click.STRING, default="all")
def loaddata(file_path):
    asyncio.run(_loaddata(file_path))
