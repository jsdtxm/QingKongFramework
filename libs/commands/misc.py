import re
import sys
from itertools import chain

from common.settings import settings
from libs.initialize.apps import init_apps
from libs.misc.ascii_art import print_logo
from libs.utils.module_loading import import_module


def about():
    print_logo()


def stubgen():
    from mypy.stubgen import Options, generate_stubs

    init_apps(settings.INSTALLED_APPS)

    module_name = "apps.polypro.models"
    module = import_module("apps.polypro.models")

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
                "apps.polypro.models",
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

    modified_lines = [
        "# type: ignore\n",
        "from tortoise.queryset import Q, QuerySet, QuerySetSingle\n",
        "import typing\n",
        "import datetime\n",
        "from tortoise.backends.base.client import BaseDBAsyncClient\n",
    ]
    for line in lines:
        if m := class_pattern.match(line):
            model_name = m.group(1)
            model_class = getattr(module, model_name)

            modified_lines.append(line)

            modified_lines.extend(
                map(lambda x: f"    {x}\n", model_class.generate_stub().split("\n"))
            )
            # HACK
            indent = " " * 4
            modified_lines.extend(
                chain(
                    [
                        f"    objects: typing.Type[{model_name}]\n\n",
                    ],
                    map(
                        lambda x: f"{indent}@classmethod\n{indent}{x}\n{indent*2}...\n\n",
                        [
                            """def filter(cls, *args: Q, **kwargs: typing.Unpack[QueryParams]) -> QuerySet[typing.Self]: # type: ignore""",
                            """def exclude(cls, *args: Q, **kwargs: typing.Unpack[QueryParams]) -> QuerySet[typing.Self]: # type: ignore""",
                            """def get(cls, *args: Q, using_db: typing.Optional[BaseDBAsyncClient] = None, **kwargs: typing.Unpack[QueryParams]) -> QuerySetSingle[typing.Self]: # type: ignore""",
                        ],
                    ),
                )
            )
        else:
            modified_lines.append(line)

    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(modified_lines)
