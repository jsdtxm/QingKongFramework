import asyncio
import sys
from pathlib import Path
from typing import Type

import click
from pydantic import BaseModel

from common.settings import settings
from fastapp.commands.decorators import async_init_fastapp
from fastapp.serializers.model import ModelSerializerPydanticModel


class PydanticToTS:
    def __init__(self):
        self.definitions = {}

    def _map_type(self, prop: dict) -> str:
        if "$ref" in prop:
            ref_path = prop["$ref"]
            return ref_path.split("/")[-1]

        if "anyOf" in prop:
            return " | ".join([self._map_type(sub) for sub in prop["anyOf"]])

        t = prop.get("type")
        if t == "string":
            return "string"
        elif t in ["integer", "number"]:
            return "number"
        elif t == "boolean":
            return "boolean"
        elif t == "null":
            return "null"
        elif t == "array":
            items = prop.get("items", {})
            return f"{self._map_type(items)}[]"
        elif t == "object":
            if "properties" in prop:
                inner_fields = []
                for field_name, field_prop in prop.get("properties", {}).items():
                    inner_fields.append(
                        f"    {field_name}: {self._map_type(field_prop)};"
                    )
                return "{\n" + "\n".join(inner_fields) + "\n  }"
            return "Record<string, any>"
        elif "enum" in prop:
            return " | ".join(
                [f"'{v}'" if isinstance(v, str) else str(v) for v in prop["enum"]]
            )

        return "any"

    def convert(self, model: Type[BaseModel]) -> str:
        schema = model.model_json_schema()
        self.definitions = schema.get("$defs", {})

        output = []
        output.append(self._generate_interface(schema.get("title", "Root"), schema))

        for name, def_schema in self.definitions.items():
            output.append(self._generate_interface(name, def_schema))

        return "\n\n".join(output)

    def _generate_interface(self, name: str, schema: dict) -> str:
        lines = [f"export interface {name.split('.')[-1]} {{"]
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for field_name, prop in properties.items():
            is_optional = "?" if field_name not in required else ""
            ts_type = self._map_type(prop)
            description = prop.get("description", "")
            if description:
                lines.append(f"  /** {description} */")
            lines.append(f"  {field_name}{is_optional}: {ts_type};")

        lines.append("}")
        return "\n".join(lines)


def get_model_serializers_from_module(module) -> list:
    serializers = []
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, ModelSerializerPydanticModel)
            and attr is not ModelSerializerPydanticModel
        ):
            serializers.append((attr_name, attr))
    return serializers


@click.command()
@click.option(
    "--output-dir",
    default="types",
    help="Path to the output directory for TypeScript files",
)
def generate_typescript(output_dir: str):
    asyncio.run(async_generate_typescript(output_dir))


@async_init_fastapp
async def async_generate_typescript(output_dir: str):
    """
    Generate TypeScript interfaces from ModelSerializerPydanticModel classes.

    This command traverses INSTALLED_APPS, finds all serializers.py modules,
    and generates TypeScript interfaces for ModelSerializerPydanticModel subclasses.
    """
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    converter = PydanticToTS()
    generated_files = []

    for app_path in settings.INSTALLED_APPS:
        serializers_module_name = f"{app_path}.serializers"

        try:
            if serializers_module_name in sys.modules:
                module = sys.modules[serializers_module_name]
            else:
                from importlib import import_module

                module = import_module(serializers_module_name)

            if not hasattr(module, "__name__"):
                continue

            serializers = get_model_serializers_from_module(module)

            if not serializers:
                continue

            app_name = app_path.split(".")[-1]
            click.echo(f"Processing app: {app_path}")

            app_types = []
            for serializer_name, serializer_class in serializers:
                try:
                    ts_code = converter.convert(serializer_class)
                    app_types.append(ts_code)
                    click.echo(f"  Generated: {serializer_name}")
                except Exception as e:
                    click.echo(f"  Error generating {serializer_name}: {e}")

            if app_types:
                output_file = output_path / f"{app_name}.ts"
                combined_code = "\n\n".join(app_types)
                output_file.write_text(combined_code + "\n")
                generated_files.append(str(output_file))
                click.echo(f"  Written: {output_file}")

        except (ImportError, AttributeError):
            continue
        except Exception as e:
            click.echo(f"Error processing {app_path}: {e}")

    if generated_files:
        click.echo(f"\nSuccessfully generated {len(generated_files)} TypeScript files:")
        for f in generated_files:
            click.echo(f"  - {f}")
    else:
        click.echo("\nNo TypeScript files were generated.")
