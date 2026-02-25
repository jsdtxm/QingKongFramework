import re
import sys
from collections import defaultdict
from itertools import chain
from typing import Literal

from fastapp.misc.complete_type import CLASS_PATTERN
from fastapp.models.base import BaseModel
from fastapp.utils.module_loading import import_module


def generate(module_name: str, mode: Literal["lite", "full", "mini"] = "lite"):
    from mypy.stubgen import Options, generate_stubs

    module = import_module(module_name)

    pyversion = sys.version_info[:2]
    generate_stubs(
        Options(
            pyversion=pyversion,
            no_import=False,
            inspect=False,
            doc_dir="",
            search_path=[],
            interpreter=sys.executable,
            ignore_errors=False,
            parse_only=False,
            include_private=False,
            output_dir=".",
            modules=[
                module_name,
            ],
            packages=[],
            files=[],
            verbose=False,
            quiet=False,
            export_less=False,
            include_docstrings=False,
        )
    )

    file_path = module_name.replace(".", "/") + ".pyi"

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    pre_import_lines = [
        "import typing\n",
        "import datetime\n",
        "import decimal\n",
        "import uuid\n",
        "from tortoise.queryset import Q, QuerySetSingle\n",
        "from tortoise.backends.base.client import BaseDBAsyncClient\n",
        "from fastapp.contrib.auth.typing import UserProtocol\n",
        "from fastapp.models.base import QuerySet\n",
        "from fastapp.models.choices import ChoiceItem, Choices\n",
        "from fastapp.models.fields import ManyToManyRelation\n",
    ]

    try:
        import numpy as _

        pre_import_lines.append("import numpy\n")
    except ImportError:
        pass

    # TODO 需要对abstractUser特殊处理
    # TODO model的方法会丢失
    # TODO manager存在的情况需要特殊处理
    need_import = defaultdict(set)
    modified_lines = []

    model_name = None
    for line in lines:
        if m := CLASS_PATTERN.match(line):
            model_name = m.group(1)
            model_class = getattr(module, model_name)

            modified_lines.append("\n")

            if re.search(r"\.\.\.", line):
                new_line = re.sub(r"\.\.\.", "\n    pass", line)
                modified_lines.append(new_line)
            else:
                modified_lines.append(line)

            if not issubclass(model_class, BaseModel):
                model_name = None
                continue

            sub_need_import, query_params = model_class.generate_query_params(mode)
            for k, v in sub_need_import.items():
                need_import[k].update(v)

            if mode != "mini":
                # MINI模式下不需要生成query_params
                objects_typing = f'typing.Type["{model_name}"]'
                if manager := getattr(model_class.Meta, "manager", None):
                    objects_typing = manager.__class__.__name__

                modified_lines.extend(
                    map(
                        lambda x: f"    {x}\n",
                        query_params.split("\n"),
                    )
                )
                indent = " " * 4
                modified_lines.extend(
                    chain(
                        [
                            f"    objects: {objects_typing} # type: ignore\n\n",
                        ],
                        map(
                            lambda x: f"{indent}@classmethod\n{indent}{x}\n{indent * 2}...\n\n",
                            [
                                """async def create(cls, **kwargs: typing.Unpack[CreateParams]) -> typing.Self: # type: ignore""",
                                """def filter(cls, *args: Q, **kwargs: typing.Unpack[QueryParams]) -> QuerySet[typing.Self]: # type: ignore""",
                                """def exclude(cls, *args: Q, **kwargs: typing.Unpack[QueryParams]) -> QuerySet[typing.Self]: # type: ignore""",
                                """async def get(cls, *args: Q, using_db: typing.Optional[BaseDBAsyncClient] = None, **kwargs: typing.Unpack[QueryParams]) -> QuerySetSingle[typing.Self]: # type: ignore""",
                                """async def get_or_none(cls, *args: Q, using_db: typing.Optional[BaseDBAsyncClient] = None, **kwargs: typing.Unpack[QueryParams]) -> QuerySetSingle[typing.Optional[typing.Self]]: # type: ignore""",
                                """async def get_or_create(cls, defaults: typing.Optional[dict] = None, using_db: typing.Optional[BaseDBAsyncClient] = None, **kwargs: typing.Unpack[QueryParams]) -> typing.Tuple[typing.Self, bool]: # type: ignore""",
                            ],
                        ),
                    )
                )
        else:
            modified_lines.append(line)

    pre_import_lines.extend(
        map(
            lambda x: f"from {x[0]} import {', '.join(x[1])}\n",
            [x for x in need_import.items() if x[0] != module_name],
        )
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(pre_import_lines + modified_lines)
