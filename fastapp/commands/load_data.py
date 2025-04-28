import asyncio
import json
import os

import click

from common.settings import settings
from fastapp.initialize.apps import init_apps
from fastapp.initialize.db import async_init_db, get_tortoise_config
from fastapp.models.tortoise import Tortoise


def remove_comments(jsonc_content: str):
    """移除JSONC内容中的注释"""

    lines = jsonc_content.splitlines()
    cleaned_lines = []
    in_block_comment = False

    for line in lines:
        if not in_block_comment:
            # 清理当前行的行注释
            index = line.find("//")
            if index != -1:
                line = line[:index]

            # 清理当前行开始的块注释起始部分
            index = line.find("/*")
            if index != -1:
                line = line[:index]
                in_block_comment = True

        if in_block_comment:
            # 寻找块注释结束部分
            index = line.find("*/")
            if index != -1:
                line = line[index + 2 :]
                in_block_comment = False
            else:
                line = ""

        if line.strip() or in_block_comment:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


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

            if item.get("pk", None) is None:
                instance = model(**item["fields"])
                await instance.save()
                continue

            if await model.objects.filter(id=item["pk"]).exists():
                # TODO 应该更新
                continue
            instance = model(id=item["pk"], **item["fields"])
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
