"""
数据库迁移工具模块

该模块提供了以下主要功能：
1. parse_sql: 解析 SQL 文件或内容，提取表结构和索引信息
2. generate_diff_sql: 比较两个数据库模式，生成差异 SQL 脚本
3. async_auto_migrate: 异步自动执行数据库迁移

主要功能说明：
- 支持 MySQL 语法解析
- 能够处理 CREATE TABLE、CREATE INDEX 等语句
- 自动检测字段重命名、新增/删除字段等变更
- 生成可执行的 SQL 迁移脚本

注意事项：
1. 生成的 SQL 脚本需要人工验证，特别是字段重命名操作
2. 目前仅支持 MySQL 语法，其他数据库可能需要调整
3. 对于复杂的约束变更，可能需要手动处理
"""

from difflib import SequenceMatcher
from itertools import chain

import sqlglot
from sqlglot import exp
from sqlglot.dialects.dialect import Dialect

NUMBER_TYPE_SET = {
    exp.DataType.Type.BIGINT,
    exp.DataType.Type.UBIGINT,
    exp.DataType.Type.INT,
    exp.DataType.Type.UINT,
    exp.DataType.Type.MEDIUMINT,
    exp.DataType.Type.UMEDIUMINT,
    exp.DataType.Type.SMALLINT,
    exp.DataType.Type.USMALLINT,
    exp.DataType.Type.TINYINT,
    exp.DataType.Type.UTINYINT,
}


def merge_and_sort_columns(data):
    grouped = {}
    for item in data:
        name = item["name"]
        columns = item["columns"]
        item_type = item["type"]
        if name in grouped:
            grouped[name]["columns"].extend(columns)
        else:
            grouped[name] = {"columns": list(columns), "type": item_type}

    result = []
    for name, info in grouped.items():
        sorted_columns = sorted(list(set(info["columns"])))
        result.append({"name": name, "columns": sorted_columns, "type": info["type"]})

    return result


def parse_sql(file_path, is_content=False, dialect="mysql"):
    """解析 SQL 文件并返回包含表结构和索引的字典"""
    # print(file_path)
    if is_content:
        sql = file_path
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()

    dialect = Dialect.get_or_raise(dialect)

    tables = {}
    table_name = None
    statements = sqlglot.parse(sql, read=dialect, dialect=dialect)

    generator = dialect.Generator()

    unique_key_dict = {}

    for stmt in statements:
        # 处理 CREATE TABLE 语句
        if isinstance(stmt, exp.Create) and isinstance(stmt.this, exp.Schema) and isinstance(stmt.this.this, exp.Table):
            schema = stmt.this
            table: exp.Table = schema.this

            table_name = table.name
            columns = {}
            indexes = []

            for constraint in chain(
                stmt.find_all(exp.UniqueColumnConstraint),
                stmt.find_all(exp.IndexColumnConstraint),
                stmt.find_all(exp.Constraint),
            ):
                if isinstance(constraint.parent.parent, exp.Create):
                    index_name = constraint.this.name

                    if isinstance(constraint, exp.IndexColumnConstraint):
                        index_fields = [x.this.this.this for x in constraint.expressions]
                    elif isinstance(constraint, exp.Constraint):
                        if len(constraint.expressions) == 1:
                            # 写于pg处理fastapp_content_type的场景
                            index_fields = [x.this for x in constraint.expressions[0].this.expressions]
                        else:
                            raise Exception("暂不支持多字段索引")
                    else:
                        index_fields = [x.name for x in constraint.this.expressions]

                    unique_key_dict[index_name] = index_fields
                elif isinstance(constraint, exp.UniqueColumnConstraint):
                    if isinstance(constraint.parent.parent, exp.ColumnDef):
                        # 列定义中的unique
                        name = constraint.parent.parent.this.name
                        unique_key_dict[name] = [
                            name,
                        ]
                    else:
                        # 写于pg处理fastapp_content_type的场景
                        unique_key_dict[constraint.parent.name] = [x.this for x in constraint.this.expressions]

                else:
                    # 貌似和上面处理的情况一样，再看看
                    constraint = constraint.parent.parent
                    name = constraint.this.name
                    unique_key_dict[name] = [
                        name,
                    ]

            # 解析列定义
            for col_def in stmt.find_all(exp.ColumnDef):
                col_name = col_def.name
                col_kind: exp.DataType = col_def.args["kind"]

                col_type = generator.datatype_sql(col_kind)
                constraints = []
                default = None

                # 处理列约束（NOT NULL、DEFAULT 等）
                for constraint in col_def.args.get("constraints", []):
                    if isinstance(constraint, exp.NotNullColumnConstraint):
                        constraints.append("NOT NULL")
                    elif isinstance(constraint, exp.DefaultColumnConstraint):
                        default = constraint.this.sql()

                columns[col_name] = {
                    "type": col_type,
                    "kind": col_kind,
                    "default": default,
                    "constraints": constraints,
                }

            # 解析表级约束（PRIMARY KEY、UNIQUE）
            for constraint in stmt.find_all(exp.Constraint):
                kind = constraint.args.get("kind")
                if kind == "PRIMARY KEY":
                    index_columns = [col.name for col in constraint.find_all(exp.Identifier)]
                    indexes.append(
                        {
                            "name": "PRIMARY",
                            "columns": index_columns,
                            "type": "PRIMARY KEY",
                        }
                    )
                elif kind == "UNIQUE":
                    name = constraint.args.get("name")
                    name = name.name if name else None
                    index_columns = [col.name for col in constraint.find_all(exp.Identifier)]
                    indexes.append({"name": name, "columns": index_columns, "type": "UNIQUE"})

            tables[table_name] = {"columns": columns, "indexes": indexes, "stmt": stmt}

        # 处理独立的 CREATE INDEX 语句
        elif isinstance(stmt, exp.Create) and isinstance(stmt.this, exp.Index):
            index = stmt.this
            table_name = index.args["table"].name
            index_name = index.name
            columns = [x.name for x in index.args["params"].find_all(exp.Identifier)]

            index_type = None
            if params := stmt.this.args.get("params", None):
                if using := params.args.get("using"):
                    index_type = using.this.upper()

            if index_type is None:
                index_type = "UNIQUE" if stmt.args.get("unique") else "BTREE"

            if table_name in tables:
                tables[table_name]["indexes"].append({"name": index_name, "columns": columns, "type": index_type})

        if not table_name:
            continue

        # 合并同名index字段
        tables[table_name]["indexes"] = merge_and_sort_columns(tables[table_name]["indexes"])
        for index_name, columns in unique_key_dict.items():
            if next(
                filter(lambda x: x["name"] == index_name, tables[table_name]["indexes"]),
                None,
            ):
                continue
            data = {
                "name": index_name,
                "columns": sorted(columns),
                "type": "BTREE",  # TODO
            }

            if data not in tables[table_name]["indexes"]:
                tables[table_name]["indexes"].append(data)

    return tables


def calculate_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def generate_alter_statements(old_schema, new_schema, table_name, dialect):
    old_columns = old_schema.get("columns", {})
    new_columns = new_schema.get("columns", {})
    old_indexes = old_schema.get("indexes", [])
    new_indexes = new_schema.get("indexes", [])

    alter_ops = []
    renamed_columns = {}

    # 处理字段重命名
    deleted_cols = set(old_columns.keys()) - set(new_columns.keys())
    added_cols = set(new_columns.keys()) - set(old_columns.keys())

    possible_renames = []
    for del_col in deleted_cols:
        for add_col in added_cols:
            sim = calculate_similarity(del_col, add_col)
            if sim > 0.6:  # 相似度阈值可调整
                possible_renames.append((del_col, add_col, sim))

    # 按相似度降序排序，优先处理最可能的
    possible_renames.sort(key=lambda x: -x[2])
    handled = set()
    for old_col, new_col, _ in possible_renames:
        if old_col in handled or new_col in handled:
            continue
        response = input(f"是否将字段 '{old_col}' 重命名为 '{new_col}'? [Y/N]: ").strip().upper()
        if response == "Y":
            renamed_columns[old_col] = new_col
            handled.add(old_col)
            handled.add(new_col)
            alter_ops.append(f"ALTER TABLE {table_name} RENAME COLUMN {old_col} TO {new_col};")

    # 更新删除和新增字段列表
    deleted_cols = [c for c in deleted_cols if c not in renamed_columns]
    added_cols = [c for c in added_cols if c not in renamed_columns.values()]

    # 处理删除字段
    for col in deleted_cols:
        alter_ops.append(f"ALTER TABLE {table_name} DROP COLUMN {col};")

    # 处理新增字段
    for col in added_cols:
        col_def = new_columns[col]
        type_def = col_def["type"]
        default = col_def["default"]
        constraints = " ".join(col_def["constraints"])
        default_clause = f" DEFAULT {default}" if default is not None else ""
        alter_ops.append(f"ALTER TABLE {table_name} ADD COLUMN {col} {type_def}{default_clause} {constraints};")

    # 处理修改字段
    common_cols = set(old_columns.keys()) & set(new_columns.keys())
    for col in common_cols:
        old_def = old_columns[col]
        new_def = new_columns[col]
        if (
            old_def["type"] != new_def["type"]
            or old_def["default"] != new_def["default"]
            or old_def["constraints"] != new_def["constraints"]
        ):
            if old_def["type"] != new_def["type"] and "kind" in old_def and "kind" in new_def:
                old_kind, new_kind = old_def["kind"], new_def["kind"]

                if old_kind.this == new_kind.this and new_kind.this in NUMBER_TYPE_SET:
                    if not new_kind.expressions and old_kind.expressions:
                        # 跳过new_schema没有数字类型长度的问题
                        continue

                if str(old_kind).upper() == "TINYINT(1)" and str(new_def["kind"]).upper() == "BOOLEAN":
                    continue

                if str(old_kind).upper() == "BIGINT(64)" and str(new_def["kind"]).upper() == "BIGSERIAL":
                    continue

                if str(old_kind).upper() == "TEXT" and str(new_def["kind"]).upper() == "JSON":
                    # TODO这边似乎是mysql的锅
                    continue

            constraints = " ".join(new_def["constraints"])
            default_clause = f" DEFAULT {new_def['default']}" if new_def["default"] is not None else ""
            alter_ops.append(f"ALTER TABLE {table_name} MODIFY COLUMN {col} {new_def['type']}{default_clause} {constraints};")

    # 处理索引
    def process_indexes(old_idx_list, new_idx_list, drop_command=True):
        # 过滤pg中的主键索引
        old_idx_list = [idx for idx in old_idx_list if idx["columns"] != ["id"]]
        new_idx_list = [idx for idx in new_idx_list if idx["columns"] != ["id"]]
        old_idx_map = {}
        for idx in old_idx_list:
            key = (tuple(idx["columns"]), idx["type"])
            old_idx_map[key] = idx

        new_idx_map = {}
        for idx in new_idx_list:
            key = (tuple(idx["columns"]), idx["type"])
            new_idx_map[key] = idx

        # 删除旧索引
        if drop_command:
            for key in old_idx_map.keys() - new_idx_map.keys():
                idx = old_idx_map[key]
                alter_ops.append(f"DROP INDEX {idx['name']} ON {table_name};")

        # 新增索引
        for key in new_idx_map.keys() - old_idx_map.keys():
            idx = new_idx_map[key]
            columns = ", ".join(idx["columns"]) if isinstance(idx["columns"], list) else idx["columns"]
            index_type = idx["type"].replace("_", " ").upper()
            # TODO fixme the columns may empty
            if dialect == "postgres":
                sql = f"CREATE INDEX IF NOT EXISTS {idx['name']} ON {table_name} USING {index_type} ({columns});"
            else:
                sql = f"CREATE {index_type} IF NOT EXISTS {idx['name']} ON {table_name} ({columns});"
            alter_ops.append(sql)

    # 先删除旧索引，再创建新索引
    process_indexes(old_indexes, new_indexes)

    return alter_ops


def generate_diff_sql(old_schema, new_schema, dialect):
    # FIXME 有问题，抓不到null的变更
    table_name_set = set(old_schema.keys()) | set(new_schema.keys())

    res = []
    for table_name in table_name_set:
        if table_name not in old_schema:
            res.append(
                [
                    new_schema[table_name]["stmt"].sql(dialect),
                ]
            )
            continue

        alter_scripts = generate_alter_statements(old_schema[table_name], new_schema[table_name], table_name, dialect)
        res.append(alter_scripts)

    return res


async def async_auto_migrate():
    """
    异步自动执行数据库迁移的函数。
    该函数会解析旧的和新的数据库模式，生成差异 SQL 脚本，并打印出来。
    """
    old_schema = parse_sql("old_schema.sql")
    new_schema = parse_sql("new_schema.sql")
    changes = generate_diff_sql(old_schema, new_schema)
    print("-- 数据库变更脚本")
    print("\n".join(changes))
