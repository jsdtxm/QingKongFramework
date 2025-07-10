import asyncio
import json

import click
from tortoise.fields.relational import BackwardFKRelation, BackwardOneToOneRelation

from common.settings import settings
from fastapp.initialize.apps import init_apps
from fastapp.initialize.db import async_init_db, get_tortoise_config
from fastapp.models.fields import ForeignKeyFieldInstance, ManyToManyFieldInstance
from fastapp.models.fields.vector import VectorField
from fastapp.models.tortoise import Tortoise
from fastapp.utils.json import JSONEncoder


async def _dumpdata(model_name):
    init_apps(settings.INSTALLED_APPS)
    await async_init_db(get_tortoise_config(settings.DATABASES))

    for app, models in Tortoise.apps.items():
        for name, model in models.items():
            if model_name != name:
                continue

            dump_field_set = set()
            for field_name, field in model._meta.fields_map.items():
                if isinstance(
                    field,
                    (
                        ForeignKeyFieldInstance,
                        BackwardOneToOneRelation,
                        ManyToManyFieldInstance,
                        BackwardFKRelation,
                    ),
                ):
                    continue
                elif isinstance(field, VectorField):
                    continue

                dump_field_set.add(field_name)

            result_list = []
            async for obj in model.all().order_by("id"):
                result_item = {
                    "model": f"{model.app.label}.{model.__name__}",
                    "pk": obj.id,
                    "fields": {},
                }
                for field_name in dump_field_set - {"id"}:
                    value = getattr(obj, field_name)
                    if value is None:
                        continue
                    result_item["fields"][field_name] = value
                result_list.append(result_item)

            json_data = json.dumps(
                result_list,
                cls=JSONEncoder,
                ensure_ascii=False,
                indent=2,
            )
            print(json_data)

    await Tortoise.close_connections()


@click.argument("model", type=click.STRING)
def dumpdata(model):
    asyncio.run(_dumpdata(model))
