import asyncio

from asyncmy import connect
from asyncmy.cursors import DictCursor
from libs.utils.strings import to_camel_case


async def table_to_django_model(db_config, table_name):
    # TODO 字段名称标准化
    """
    将数据库表结构转换为Django模型定义。

    :param db_config: 数据库连接配置，例如 {'host': 'localhost', 'user': 'root', 'password': 'password', 'db': 'your_db'}
    :param table_name: 要转换的表名
    :return: Django模型定义的字符串
    """
    # 连接到数据库
    conn = await connect(**db_config)
    async with conn.cursor(cursor=DictCursor) as cursor:
        await cursor.execute(f"DESCRIBE {table_name}")
        columns = await cursor.fetchall()

    # 生成Django模型定义
    model_definition = f"class {to_camel_case(table_name)}(models.Model):\n"
    for column in columns:
        column_name = column["Field"]
        data_type = column["Type"]
        is_nullable = column["Null"] == "YES"
        is_primary_key = column["Key"] == "PRI"
        default_value = column["Default"]

        # 将MySQL数据类型映射到Django字段类型
        field_type = "models.CharField"  # 默认字段类型
        max_length = None
        if data_type.startswith("int"):
            field_type = "models.IntegerField"
        elif data_type.startswith("varchar"):
            field_type = "models.CharField"
            max_length = int(data_type.split("(")[1].split(")")[0])
        elif data_type.startswith("text"):
            field_type = "models.TextField"
        elif data_type.startswith("datetime"):
            field_type = "models.DateTimeField"
        elif data_type.startswith("date"):
            field_type = "models.DateField"
        elif data_type.startswith("float"):
            field_type = "models.FloatField"
        elif data_type.startswith("decimal"):
            field_type = "models.DecimalField"
            max_digits, decimal_places = map(
                int, data_type.split("(")[1].split(")")[0].split(",")
            )

        # 生成字段定义
        field_definition = f"    {column_name} = {field_type}("
        if max_length:
            field_definition += f"max_length={max_length}, "
        if not is_nullable:
            field_definition += "null=False, "
        else:
            field_definition += "null=True, "
        if default_value:
            field_definition += f"default={default_value}, "
        if is_primary_key:
            field_definition += "primary_key=True, "
        field_definition = field_definition.rstrip(", ") + ")\n"

        model_definition += field_definition

    model_definition += "\n    class Meta:\n        table = '" + table_name + "'\n"

    # 关闭数据库连接
    await conn.ensure_closed()

    return model_definition


async def run(table_name, db_config):
    model_definition = await table_to_django_model(db_config, table_name)
    print(model_definition)


if __name__ == "__main__":
    db_config = {"host": "", "user": "", "password": "", "db": ""}

    table_name = ""

    asyncio.run(run(table_name, db_config))
