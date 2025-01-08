import re
from collections import defaultdict
from itertools import chain

from tortoise.fields import relational

from libs.models.base import BaseModel
from libs.utils.module_loading import import_module
from libs.utils.typing import type_to_str


def complete(module_name: str):
    file_path = module_name.replace(".", "/") + ".pyi"
    module = import_module(module_name)

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    class_pattern = re.compile(
        r"class\s([A-Za-z_][A-Za-z_0-9]*)\([A-Za-z_][A-Za-z_0-9.]+\):"
    )

    incomplete_pattern = re.compile(r"\s+([A-Za-z_][A-Za-z_0-9]*)\s*:\s*Incomplete")

    result_parts = []
    tmp_part = []
    model_name = None
    model_desc_dict = defaultdict(dict)
    for line in lines:
        if m := class_pattern.match(line):
            model_name = m.group(1)
            model_class = getattr(module, model_name)

            if not issubclass(model_class, BaseModel):
                tmp_part.append(line)
                continue

            for _, fields in filter(
                lambda x: x[0]
                in {"pk_field", "data_fields", "fk_fields", "backward_fk_fields"},
                model_class.describe(serializable=False).items(),
            ):
                if not isinstance(fields, list):
                    fields = [
                        fields,
                    ]
                for field in fields:
                    model_desc_dict[model_name][field["name"]] = field

            result_parts.append(tmp_part)
            tmp_part = []

        elif model_name and (m := incomplete_pattern.match(line)):
            field_name = m.group(1)
            try:
                desc = model_desc_dict[model_name][field_name]
            except Exception:
                tmp_part.append(line)
                continue
            field_type = desc["field_type"]
            if (
                field_type is relational.ForeignKeyFieldInstance
                or field_type is relational.OneToOneFieldInstance
                or field_type is relational.BackwardOneToOneRelation
                or field_type is relational.BackwardFKRelation
                or field_type is relational.ManyToManyFieldInstance
            ):
                ptype = field["python_type"].__name__
                if field["nullable"] is True:
                    ptype = f"typing.Optional[{ptype}]"
                
                if ptype == "User":
                    ptype = 'typing.Union["User", "UserProtocol"]'

                tmp_part.append(line.replace("Incomplete", ptype))
                continue

            ptype = desc["python_type"]

            ptype_str = type_to_str(ptype)
            
            optional = desc.get("nullable")

            line_type_str = f"typing.Optional[{ptype_str}]" if optional else ptype_str

            tmp_part.append(line.replace("Incomplete", line_type_str))

            continue

        tmp_part.append(line)

    result_parts.append(tmp_part)
    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(chain(*result_parts))
