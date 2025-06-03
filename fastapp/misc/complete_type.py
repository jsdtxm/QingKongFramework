import re
from collections import defaultdict
from itertools import chain

from tortoise.fields import relational

from fastapp.models.base import BaseModel
from fastapp.models.choices import Choices
from fastapp.utils.module_loading import import_module
from fastapp.utils.typing import type_to_str

CLASS_PATTERN = re.compile(
    r"class\s([A-Za-z_][A-Za-z_0-9]*)\([A-Za-z_][A-Za-z_0-9.\[\]\s\,]+\):(\s+...)?"
)
INCOMPLETE_PATTERN = re.compile(r"\s+([A-Za-z_][A-Za-z_0-9]*)\s*:\s*Incomplete")

def remove_meta_class(code_lines):
    """
    删除嵌套在类中的 Meta 类及其内容。

    :param code_lines: 一个包含 Python 代码的行列表
    :return: 处理后的代码行列表
    """
    cleaned_code = []  # 存储清理后的代码
    class_stack = []  # 用于跟踪当前嵌套的类及其缩进
    inside_meta = False  # 标记是否在 Meta 类中

    for line in code_lines:
        stripped_line = line.lstrip()  # 去掉左侧空白以获取实际内容
        indent = line[: len(line) - len(stripped_line)]  # 获取当前行的缩进

        # 检测类定义
        if stripped_line.startswith("class "):
            class_name = (
                stripped_line.split("class ")[1].split("(")[0].split(":")[0].strip()
            )
            class_stack.append((class_name, indent))  # 将当前类名和缩进压入栈

        # 如果检测到 Meta 类的定义
        if "class Meta" in stripped_line and class_stack:
            inside_meta = True  # 进入 Meta 类

        # 如果不在 Meta 类中，则保留代码
        if not inside_meta:
            cleaned_code.append(line)

        # 检测类结束（通过缩进减少）
        if class_stack and len(indent) < len(class_stack[-1][1]):
            if inside_meta:
                inside_meta = False  # 退出 Meta 类
            class_stack.pop()  # 退出当前类

    return cleaned_code


def complete(module_name: str):
    file_path = module_name.replace(".", "/") + ".pyi"
    module = import_module(module_name)

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    result_parts = []
    tmp_part = []
    model_name = None
    model_desc_dict = defaultdict(dict)
    for line in lines:
        if m := CLASS_PATTERN.match(line):
            _model_name = m.group(1)
            model_class = getattr(module, _model_name)

            if not issubclass(model_class, BaseModel):
                tmp_part.append(line)
                continue
            
            model_name = _model_name
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

        elif model_name and (m := INCOMPLETE_PATTERN.match(line)):
            field_name = m.group(1)
            try:
                desc = model_desc_dict[model_name][field_name]
            except Exception:
                tmp_part.append(line)
                continue
            field_type = desc["field_type"]
            if (
                issubclass(field_type, relational.ForeignKeyFieldInstance)
                or issubclass(field_type, relational.OneToOneFieldInstance)
                or issubclass(field_type, relational.BackwardOneToOneRelation)
                or issubclass(field_type, relational.BackwardFKRelation)
                or issubclass(field_type, relational.ManyToManyFieldInstance)
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
    lines = remove_meta_class(chain(*result_parts))
    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(lines)


def complete_choices(module_name: str):
    file_path = module_name.replace(".", "/") + ".pyi"
    module = import_module(module_name)

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    result_parts = []
    tmp_part = []
    model_name = None
    for line in lines:
        if m := CLASS_PATTERN.match(line):
            _model_name = m.group(1)
            model_class = getattr(module, _model_name)

            if not issubclass(model_class, Choices):
                tmp_part.append(line)
                continue

            model_name = _model_name

            generic_type = re.search(r"\[(\S+)\]", line)
            if generic_type:
                generic_type = generic_type.group(1)

            result_parts.append(tmp_part)
            tmp_part = []

        elif model_name and (m := INCOMPLETE_PATTERN.match(line)):
            line_type_str = "ChoiceItem"
            if generic_type:
                line_type_str = f"ChoiceItem[{generic_type}]"

            tmp_part.append(line.replace("Incomplete", line_type_str))

            continue

        tmp_part.append(line)

    result_parts.append(tmp_part)
    lines = chain(*result_parts)
    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(lines)