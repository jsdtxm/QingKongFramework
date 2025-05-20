import operator
import re
from typing import TYPE_CHECKING, Dict, List, Type, cast

from pypika.terms import Criterion, Term
from tortoise.backends import mysql
from tortoise.backends.mysql import executor, schema_generator
from tortoise.backends.mysql.executor import MySQLExecutor as RawMySQLExecutor
from tortoise.contrib.mysql.json_functions import (
    JSONExtract,
    _serialize_value,
    operator_keywords,
)
from tortoise.fields import JSONField, TextField, UUIDField
from tortoise.filters import (
    contains,
    ends_with,
    insensitive_contains,
    insensitive_ends_with,
    insensitive_exact,
    insensitive_starts_with,
    is_in,
    json_contained_by,
    json_contains,
    json_filter,
    posix_regex,
    search,
    starts_with,
)
from tortoise.indexes import Index

from fastapp.db.backends.mixin import SchemaGeneratorMixin

if TYPE_CHECKING:  # pragma: nocoverage
    from tortoise.fields.relational import ForeignKeyFieldInstance  # noqa
    from tortoise.fields.relational import ManyToManyFieldInstance
    from tortoise.models import Model


def generate_partition_sql(part):
    primary_keys = []
    # 处理主分区
    main_type = part["type"]
    main_partition_sql = ""
    if main_type in ["RANGE", "LIST"]:
        # 处理函数式表达式
        expr = part["expr"].strip()
        if "(" in expr:
            func_name = expr.split("(")[0].strip()
        else:
            func_name = expr
        primary_keys.extend(part["fields"])
        fields_str = ", ".join([f"`{f}`" for f in part["fields"]])
        main_expr = f"{func_name}({fields_str})"
        main_partition_sql = f"{main_type} ({main_expr})"
    elif main_type in ["RANGE COLUMNS", "LIST COLUMNS"]:
        # 处理列名列表
        fields_str = ", ".join([f"`{f}`" for f in part["fields"]])
        main_partition_sql = f"{main_type} ({fields_str})"
    else:
        # 处理其他类型如 HASH/KEY
        expr = part.get("expr", "")
        main_partition_sql = f"{main_type} ({expr})" if expr else main_type

    # 处理子分区
    sub_partition_sql = ""
    if "sub_partition" in part:
        sub_part = part["sub_partition"]
        sub_type = sub_part["type"]
        primary_keys.extend(sub_part["fields"])
        sub_fields = ", ".join([f"`{f}`" for f in sub_part["fields"]])
        sub_partition_sql = f"SUBPARTITION BY {sub_type} ({sub_fields})"

    # 处理分区定义
    partition_defs = []
    for p in part["partitions"]:
        partition_def = f"PARTITION {p['name']} VALUES {p['expr']}"
        partition_defs.append(partition_def)
    partitions_sql = "(\n    " + ",\n    ".join(partition_defs) + "\n)"

    # 组合所有部分
    sql_lines = [f"PARTITION BY {main_partition_sql}"]
    if sub_partition_sql:
        sql_lines.append(sub_partition_sql)
    sql_lines.append(partitions_sql)

    return "\n".join(sql_lines), primary_keys


class MySQLSchemaGenerator(SchemaGeneratorMixin, schema_generator.MySQLSchemaGenerator):
    extra_sql_dict = {}

    TABLE_CREATE_TEMPLATE = (
        "CREATE TABLE {exists}`{table_name}` ({fields}){extra}{comment}{partition};"
    )

    def _get_table_sql(self, model: "Type[Model]", safe: bool = True) -> dict:
        fields_to_create = []
        fields_with_index = []
        m2m_tables_for_create = []
        references = set()
        models_to_create: "List[Type[Model]]" = []

        self._get_models_to_create(models_to_create)
        models_tables = [model._meta.db_table for model in models_to_create]
        for field_name, column_name in model._meta.fields_db_projection.items():
            field_object = model._meta.fields_map[field_name]
            comment = (
                self._column_comment_generator(
                    table=model._meta.db_table,
                    column=column_name,
                    comment=field_object.description,
                )
                if field_object.description
                else ""
            )

            default = field_object.default
            auto_now_add = getattr(field_object, "auto_now_add", False)
            auto_now = getattr(field_object, "auto_now", False)
            if default is not None or auto_now or auto_now_add:
                if callable(default) or isinstance(
                    field_object, (UUIDField, TextField, JSONField)
                ):
                    default = ""
                else:
                    default = field_object.to_db_value(default, model)
                    try:
                        default = self._column_default_generator(
                            model._meta.db_table,
                            column_name,
                            self._escape_default_value(default),
                            auto_now_add,
                            auto_now,
                        )
                    except NotImplementedError:
                        default = ""
            else:
                default = ""

            # TODO: PK generation needs to move out of schema generator.
            if field_object.pk:
                if field_object.generated:
                    generated_sql = field_object.get_for_dialect(
                        self.DIALECT, "GENERATED_SQL"
                    )
                    if generated_sql:  # pragma: nobranch
                        fields_to_create.append(
                            self.GENERATED_PK_TEMPLATE.format(
                                field_name=column_name,
                                generated_sql=generated_sql,
                                comment=comment,
                            )
                        )
                        continue

            nullable = "NOT NULL" if not field_object.null else ""
            unique = "UNIQUE" if field_object.unique else ""

            if getattr(field_object, "reference", None):
                reference = cast("ForeignKeyFieldInstance", field_object.reference)
                comment = (
                    self._column_comment_generator(
                        table=model._meta.db_table,
                        column=column_name,
                        comment=reference.description,
                    )
                    if reference.description
                    else ""
                )

                to_field_name = reference.to_field_instance.source_field
                if not to_field_name:
                    to_field_name = reference.to_field_instance.model_field_name

                field_creation_string = self._create_string(
                    db_column=column_name,
                    field_type=field_object.get_for_dialect(self.DIALECT, "SQL_TYPE"),
                    nullable=nullable,
                    unique=unique,
                    is_primary_key=field_object.pk,
                    comment=comment if not reference.db_constraint else "",
                    default=default,
                ) + (
                    self._create_fk_string(
                        constraint_name=self._generate_fk_name(
                            model._meta.db_table,
                            column_name,
                            reference.related_model._meta.db_table,
                            to_field_name,
                        ),
                        db_column=column_name,
                        table=reference.related_model._meta.db_table,
                        field=to_field_name,
                        on_delete=reference.on_delete,
                        comment=comment,
                    )
                    if reference.db_constraint
                    else ""
                )
                references.add(reference.related_model._meta.db_table)
            else:
                field_creation_string = self._create_string(
                    db_column=column_name,
                    field_type=field_object.get_for_dialect(self.DIALECT, "SQL_TYPE"),
                    nullable=nullable,
                    unique=unique,
                    is_primary_key=field_object.pk,
                    comment=comment,
                    default=default,
                )

            fields_to_create.append(field_creation_string)

            if field_object.index and not field_object.pk:
                fields_with_index.append(column_name)

        if model._meta.unique_together:
            for unique_together_list in model._meta.unique_together:
                unique_together_to_create = []

                for field in unique_together_list:
                    field_object = model._meta.fields_map[field]
                    unique_together_to_create.append(field_object.source_field or field)

                fields_to_create.append(
                    self._get_unique_constraint_sql(model, unique_together_to_create)
                )

        # Indexes.
        _indexes = [
            self._get_index_sql(model, [field_name], safe=safe)
            for field_name in fields_with_index
        ]

        if model._meta.indexes:
            field_indexes = set(
                map(
                    lambda x: re.search(r"\(`(\S+)`\)", x).group(1), self._field_indexes
                )
            )
            for indexes_list in model._meta.indexes:
                if not isinstance(indexes_list, Index):
                    indexes_to_create = []
                    for field in indexes_list:
                        field_object = model._meta.fields_map[field]
                        indexes_to_create.append(field_object.source_field or field)

                    _indexes.append(
                        self._get_index_sql(model, indexes_to_create, safe=safe)
                    )
                else:
                    if not safe and (
                        len(indexes_list.fields) == 1
                        and indexes_list.fields[0] in field_indexes
                    ):
                        continue

                    _indexes.append(indexes_list.get_sql(self, model, safe))

        field_indexes_sqls = [val for val in list(dict.fromkeys(_indexes)) if val]

        fields_to_create.extend(self._get_inner_statements())

        # HACK allow PARTITION clause
        partition = ""
        if partition_config := getattr(model.Meta, "partition", None):
            partition, extra_primary_keys = generate_partition_sql(partition_config)
            partition = "\n" + partition
            raw_primary_key_field = None
            for idx, val in enumerate(fields_to_create):
                if "PRIMARY KEY" in val:
                    raw_primary_key_field = re.search(r"`(\S+)`", val).group(1).strip()

                    fields_to_create[idx] = val.replace("PRIMARY KEY ", "")
                    break

            fields_to_create.append(
                f"PRIMARY KEY ({', '.join(map(lambda x: f'`{x}`', [raw_primary_key_field, *extra_primary_keys]))})"
            )

        table_fields_string = "\n    {}\n".format(",\n    ".join(fields_to_create))
        table_comment = (
            self._table_comment_generator(
                table=model._meta.db_table, comment=model._meta.table_description
            )
            if model._meta.table_description
            else ""
        )

        table_create_string = self.TABLE_CREATE_TEMPLATE.format(
            exists="IF NOT EXISTS " if safe else "",
            table_name=model._meta.db_table,
            fields=table_fields_string,
            comment=table_comment,
            extra=self._table_generate_extra(table=model._meta.db_table),
            partition=partition,
        )

        table_create_string = "\n".join([table_create_string, *field_indexes_sqls])

        table_create_string += self._post_table_hook()

        for m2m_field in model._meta.m2m_fields:
            field_object = cast(
                "ManyToManyFieldInstance", model._meta.fields_map[m2m_field]
            )
            if field_object._generated or field_object.through in models_tables:
                continue
            backward_key, forward_key = (
                field_object.backward_key,
                field_object.forward_key,
            )
            backward_fk = forward_fk = ""
            if field_object.db_constraint:
                backward_fk = self._create_fk_string(
                    "",
                    backward_key,
                    model._meta.db_table,
                    model._meta.db_pk_column,
                    field_object.on_delete,
                    "",
                )
                forward_fk = self._create_fk_string(
                    "",
                    forward_key,
                    field_object.related_model._meta.db_table,
                    field_object.related_model._meta.db_pk_column,
                    field_object.on_delete,
                    "",
                )
            exists = "IF NOT EXISTS " if safe else ""
            table_name = field_object.through
            m2m_create_string = self.M2M_TABLE_TEMPLATE.format(
                exists=exists,
                table_name=table_name,
                backward_fk=backward_fk,
                forward_fk=forward_fk,
                backward_key=backward_key,
                backward_type=model._meta.pk.get_for_dialect(self.DIALECT, "SQL_TYPE"),
                forward_key=forward_key,
                forward_type=field_object.related_model._meta.pk.get_for_dialect(
                    self.DIALECT, "SQL_TYPE"
                ),
                extra=self._table_generate_extra(table=field_object.through),
                comment=(
                    self._table_comment_generator(
                        table=field_object.through, comment=field_object.description
                    )
                    if field_object.description
                    else ""
                ),
            )
            if not field_object.db_constraint:
                m2m_create_string = m2m_create_string.replace(
                    """,
    ,
    """,
                    "",
                )  # may have better way
            m2m_create_string += self._post_table_hook()
            if field_object.create_unique_index:
                unique_index_create_sql = self._get_unique_index_sql(
                    exists, table_name, [backward_key, forward_key]
                )
                if unique_index_create_sql.endswith(";"):
                    m2m_create_string += "\n" + unique_index_create_sql
                else:
                    lines = m2m_create_string.splitlines()
                    lines[-2] += ","
                    indent = m.group() if (m := re.match(r"\s+", lines[-2])) else ""
                    lines.insert(-1, indent + unique_index_create_sql)
                    m2m_create_string = "\n".join(lines)
            m2m_tables_for_create.append(m2m_create_string)

        return {
            "table": model._meta.db_table,
            "model": model,
            "table_creation_string": table_create_string,
            "references": references,
            "m2m_tables": m2m_tables_for_create,
        }


def mysql_json_filter(field: Term, value: Dict) -> Criterion:
    if len(value) > 1:
        criterions = [
            mysql_json_filter(
                field,
                dict([x]),
            )
            for x in value.items()
        ]
        wheres = criterions[0]
        for c in criterions[1:]:
            wheres &= c
        return wheres

    ((key, filter_value),) = value.items()

    key_parts = [
        int(item)
        if item.isdigit()
        else str(item).replace("_\\_", "__")  # HACK add replace("_\\_", "__")
        for item in key.split("__")
    ]

    # HACK add is_in
    if len(key_parts) == 2 and key_parts[1] == "in":
        key_parts = key_parts[:-1]
        return is_in(JSONExtract(field, key_parts), filter_value)

    filter_value = _serialize_value(filter_value)

    operator_ = operator.eq
    if key_parts[-1] in operator_keywords:
        operator_ = operator_keywords[str(key_parts.pop(-1))]  # type: ignore

    return operator_(JSONExtract(field, key_parts), filter_value)


class MySQLExecutor(RawMySQLExecutor):
    FILTER_FUNC_OVERRIDE = {
        contains: executor.mysql_contains,
        starts_with: executor.mysql_starts_with,
        ends_with: executor.mysql_ends_with,
        insensitive_exact: executor.mysql_insensitive_exact,
        insensitive_contains: executor.mysql_insensitive_contains,
        insensitive_starts_with: executor.mysql_insensitive_starts_with,
        insensitive_ends_with: executor.mysql_insensitive_ends_with,
        search: executor.mysql_search,
        json_contains: executor.mysql_json_contains,
        json_contained_by: executor.mysql_json_contained_by,
        json_filter: mysql_json_filter,
        posix_regex: executor.mysql_posix_regex,
    }


class MySQLClient(mysql.MySQLClient):
    schema_generator = MySQLSchemaGenerator
    executor_class = MySQLExecutor


client_class = MySQLClient
