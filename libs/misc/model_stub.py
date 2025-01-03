import re
import sys
from collections import defaultdict
from itertools import chain

from libs.models.base import BaseModel
from libs.utils.module_loading import import_module


def generate(module_name: str, mode: str):
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

    class_pattern = re.compile(
        r"class\s([A-Za-z_][A-Za-z_0-9]+)\([A-Za-z_][A-Za-z_0-9.]+\):"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    pre_import_lines = [
        "import typing\n",
        "import datetime\n",
        "from tortoise.queryset import Q, QuerySet, QuerySetSingle\n",
        "from tortoise.backends.base.client import BaseDBAsyncClient\n",
        "from libs.contrib.auth.typing import UserProtocol\n",
    ]
    need_import = defaultdict(set)
    modified_lines = []
    for line in lines:
        if m := class_pattern.match(line):
            model_name = m.group(1)
            model_class = getattr(module, model_name)

            modified_lines.append(line)

            if not issubclass(model_class, BaseModel):
                continue

            sub_need_import, query_params = model_class.generate_query_params(mode)
            for k, v in sub_need_import.items():
                need_import[k].update(v)

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
                        f"    objects: typing.Type[{model_name}] # type: ignore\n\n",
                    ],
                    map(
                        lambda x: f"{indent}@classmethod\n{indent}{x}\n{indent*2}...\n\n",
                        [
                            """def create(cls, **kwargs: typing.Unpack[CreateParams]) -> typing.Self: # type: ignore""",
                            """def filter(cls, *args: Q, **kwargs: typing.Unpack[QueryParams]) -> QuerySet[typing.Self]: # type: ignore""",
                            """def exclude(cls, *args: Q, **kwargs: typing.Unpack[QueryParams]) -> QuerySet[typing.Self]: # type: ignore""",
                            """def get(cls, *args: Q, using_db: typing.Optional[BaseDBAsyncClient] = None, **kwargs: typing.Unpack[QueryParams]) -> QuerySetSingle[typing.Self]: # type: ignore""",
                        ],
                    ),
                )
            )
        else:
            modified_lines.append(line)

    pre_import_lines.extend(
        map(lambda x: f"from {x[0]} import {", ".join(x[1])}\n", [x for x in need_import.items() if x[0] != module_name])
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(pre_import_lines + modified_lines)
