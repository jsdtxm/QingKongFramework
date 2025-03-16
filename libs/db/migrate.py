import sqlglot
from sqlglot import exp


def parse_sql(file_path, is_content=False):
    """解析 SQL 文件并返回表结构字典"""

    if is_content:
        sql = file_path
    else:
        with open(file_path, "r") as f:
            sql = f.read()

    tables = {}
    for create in sqlglot.parse(sql, read="postgres")[0].find_all(
        exp.Create, exp.Table
    ):
        table_name = create.this.name
        columns = {}

        for col in create.find_all(exp.ColumnDef):
            col_name = col.this.name
            col_type = col.args["kind"].this.name.upper()
            constraints = []
            default = None

            for constraint in col.args.get("constraints", []):
                if isinstance(constraint, exp.NotNullColumnConstraint):
                    constraints.append("NOT NULL")
                elif isinstance(constraint, exp.DefaultColumnConstraint):
                    default = constraint.this.sql()

            columns[col_name] = {
                "type": col_type,
                "default": default,
                "constraints": constraints,
            }

        tables[table_name] = columns
    return tables


def generate_diff_sql(old_tables, new_tables):
    """生成差异 SQL 脚本"""
    sql_statements = []

    # 处理新增表
    for table in set(new_tables) - set(old_tables):
        sql_statements.append(f"-- 新建表: {table}\n{new_tables[table]['_create_sql']}")

    # 处理删除表（根据需求决定是否生成 DROP 语句）

    # 处理现有表的变更
    for table in set(old_tables) & set(new_tables):
        old_cols = old_tables[table]
        new_cols = new_tables[table]

        # 字段重命名检测
        candidates = []
        deleted = set(old_cols) - set(new_cols)
        added = set(new_cols) - set(old_cols)

        # 寻找类型和约束相同的字段对
        for del_col in list(deleted):
            for add_col in list(added):
                if (
                    old_cols[del_col]["type"] == new_cols[add_col]["type"]
                    and old_cols[del_col]["constraints"]
                    == new_cols[add_col]["constraints"]
                ):
                    candidates.append((del_col, add_col))
                    deleted.remove(del_col)
                    added.remove(add_col)
                    break

        # 生成重命名语句（需要人工验证）
        for old_name, new_name in candidates:
            sql_statements.append(
                f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name};"
            )

        # 新增字段
        for col in added:
            col_def = new_cols[col]
            sql = f"ALTER TABLE {table} ADD COLUMN {col} {col_def['type']}"
            if col_def["default"]:
                sql += f" DEFAULT {col_def['default']}"
            sql += " " + " ".join(col_def["constraints"]) + ";"
            sql_statements.append(sql)

        # 删除字段
        for col in deleted:
            sql_statements.append(f"ALTER TABLE {table} DROP COLUMN {col};")

        # 字段类型/约束变更（简化示例）
        for col in set(old_cols) & set(new_cols):
            old = old_cols[col]
            new = new_cols[col]
            if old != new:
                sql_statements.append(
                    f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {new['type']};"
                )
                # 需要更详细的约束处理逻辑

    return sql_statements


async def async_auto_migrate():
    old_schema = parse_sql("old_schema.sql")
    new_schema = parse_sql("new_schema.sql")
    changes = generate_diff_sql(old_schema, new_schema)
    print("-- 数据库变更脚本")
    print("\n".join(changes))
