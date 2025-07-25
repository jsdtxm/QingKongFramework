from typing import Any, Dict, List

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.exceptions import OperationalError

from fastapp.db import connections


class BaseSchemaDumper:
    def __init__(self, conn_name: str, tables: List[str]):
        self.conn_name = conn_name
        self.tables = tables

    async def get_ddl(self) -> str:
        raise NotImplementedError


class AsyncpgDumper(BaseSchemaDumper):
    """PostgreSQL 表结构导出（使用asyncpg）"""

    async def get_ddl(self) -> str:
        ddls = []
        conn = connections[self.conn_name]
        for table in self.tables:
            exists = await self._check_exists(conn, table)
            if not exists:
                continue

            # 获取表元数据
            meta = await self._get_table_meta(conn, table)
            # 生成DDL
            table_ddl = await self._generate_table_ddl(meta)
            # 生成索引
            index_ddl = await self._generate_index_ddl(meta)
            ddls.append(f"{table_ddl}\n{index_ddl}")

        return "\n\n".join(ddls)

    async def _get_table_meta(self, conn: BaseDBAsyncClient, table: str) -> Dict[str, Any]:
        return {
            "columns": await self._get_columns(conn, table),
            "constraints": await self._get_constraints(conn, table),
            "indexes": await self._get_indexes(conn, table),
            "comment": await self._get_table_comment(conn, table),
            "vector_info": await self._get_vector_column_info(conn, table),
        }

    async def _check_exists(self, conn: BaseDBAsyncClient, table: str):
        query = """
            SELECT 
                table_name
            FROM information_schema.tables
            WHERE table_name = $1 AND table_schema = 'public'
        """
        return await conn.execute_query_dict(query, [table])

    async def _get_columns(self, conn: BaseDBAsyncClient, table: str) -> List[Dict]:
        query = """
            SELECT 
                column_name, data_type, udt_name, is_nullable, 
                column_default, ordinal_position,
                character_maximum_length, numeric_precision, numeric_scale
            FROM information_schema.columns
            WHERE table_name = $1 AND table_schema = 'public'
            ORDER BY ordinal_position
        """
        return await conn.execute_query_dict(query, [table])

    async def _get_vector_column_info(self, conn: BaseDBAsyncClient, table: str) -> List[Dict]:
        query = """
            SELECT 
                a.attname AS column_name,
                a.atttypmod AS dimension
            FROM 
                pg_catalog.pg_attribute a
            JOIN 
                pg_catalog.pg_class c ON a.attrelid = c.oid
            JOIN 
                pg_catalog.pg_namespace n ON c.relnamespace = n.oid
            JOIN 
                pg_catalog.pg_type t ON a.atttypid = t.oid
            WHERE 
                c.relname = $1
                AND n.nspname = 'public'
                AND a.attnum > 0
                AND NOT a.attisdropped
                AND t.typname = 'vector'
            ORDER BY 
                a.attnum;
        """
        return await conn.execute_query_dict(query, [table])

    async def _get_constraints(self, conn: BaseDBAsyncClient, table: str) -> List[Dict]:
        query = """
            SELECT 
                con.conname AS name,
                con.contype AS type,
                array_agg(att.attname) AS columns,
                pg_get_constraintdef(con.oid) AS definition
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            LEFT JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = ANY(con.conkey)
            WHERE rel.relname = $1 AND nsp.nspname = 'public'
            GROUP BY con.conname, con.contype, con.oid
        """
        return await conn.execute_query_dict(query, [table])

    async def _get_indexes(self, conn: BaseDBAsyncClient, table: str) -> List[Dict]:
        query = """
            SELECT 
                indexname AS name, indexdef AS definition
            FROM pg_indexes
            WHERE tablename = $1 AND schemaname = 'public'
        """
        return await conn.execute_query_dict(query, [table])

    async def _get_table_comment(self, conn: BaseDBAsyncClient, table: str) -> str:
        query = """
            SELECT description
            FROM pg_description
            WHERE objoid = $1::regclass
        """
        result = await conn.execute_query_dict(query, [table])
        return next(iter(result), {}).get("description", "")

    def _get_column_type(self, col: Dict, meta: Dict) -> str:
        data_type = col["data_type"].upper()

        length_data = []

        if data_type == "USER-DEFINED":
            data_type = col["udt_name"]
            if data_type == "vector":
                vector_length = next(filter(lambda x: x["column_name"] == col["column_name"], meta["vector_info"]), {}).get(
                    "dimension"
                )
                if vector_length is not None and vector_length != -1:
                    length_data = [str(vector_length)]

        # 有点hack的生成括号数据的方案
        length_data = length_data or list(
            map(str, filter(bool, [col["character_maximum_length"], col["numeric_precision"], col["numeric_scale"]]))
        )
        if length_data:
            data_type += "(" + ",".join(length_data) + ")"

        return data_type

    async def _generate_table_ddl(self, meta: Dict) -> str:
        columns = []
        for col in meta["columns"]:
            col_def = [
                f'"{col["column_name"]}"',
                self._get_column_type(col, meta),
                "NOT NULL" if col["is_nullable"] == "NO" else "",
                f"DEFAULT {col['column_default']}" if col["column_default"] else "",
            ]
            columns.append(" ".join(filter(None, col_def)))

        # 处理表级约束
        for con in meta["constraints"]:
            if con["type"] == "p":
                columns.append(f"PRIMARY KEY ({', '.join(con['columns'])})")
            elif con["type"] == "f":
                columns.append(con["definition"])
            elif con["type"] == "u":
                columns.append(f"UNIQUE ({', '.join(con['columns'])})")

        ddl = [f"CREATE TABLE public.{self.tables[0]} (", ",\n  ".join(columns), ");"]

        if meta["comment"]:
            ddl.append(f"\nCOMMENT ON TABLE public.{self.tables[0]} IS '{meta['comment']}';")

        return "\n".join(ddl)

    async def _generate_index_ddl(self, meta: Dict) -> str:
        return "\n".join([idx["definition"] + ";" for idx in meta["indexes"]])


class AsyncmyDumper(BaseSchemaDumper):
    """MySQL 表结构导出（使用asyncmy）"""

    async def get_ddl(self) -> str:
        ddls = []
        conn = connections[self.conn_name]
        for table in self.tables:
            # 检查表是否存在
            exists = await conn.execute_query_dict(
                f"SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END AS 'exists' FROM information_schema.tables WHERE table_name = '{table}'"
            )
            if not (exists and exists[0]["exists"] == 1):
                continue

            # 获取表结构
            table_result = await conn.execute_query_dict(f"SHOW CREATE TABLE {table}")
            ddl = table_result[0]["Create Table"]

            # 获取额外索引（非自动生成的）
            indexes = await conn.execute_query_dict(f"SHOW INDEX FROM {table}")

            # 过滤主键和唯一约束
            extra_indexes = [
                f"CREATE INDEX {idx['Key_name']} ON {table} (`{idx['Column_name']}`);"
                for idx in indexes
                if idx["Key_name"] != "PRIMARY" and not idx["Non_unique"]
            ]

            full_ddl = f"{ddl};\n" + "\n".join(extra_indexes)
            ddls.append(full_ddl)

        return "\n\n".join(ddls)


class AiosqliteDumper(BaseSchemaDumper):
    """SQLite 表结构导出（使用aiosqlite）"""

    async def get_ddl(self) -> str:
        ddls = []
        conn = connections[self.conn_name]
        for table in self.tables:
            # 获取表结构
            table_result = await conn.execute_query_dict(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            ddl = table_result[0]["sql"]

            # 获取索引
            indexes = await conn.execute_query_dict(
                "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=?",
                (table,),
            )

            full_ddl = f"{ddl};\n" + "\n".join([idx["sql"] + ";" for idx in indexes])
            ddls.append(full_ddl)
        return "\n\n".join(ddls)


class SchemaExporter:
    def __init__(self, conn_name: str, tables: List[str]):
        self.conn_name = conn_name
        self.tables = tables

    def _get_dumper_class(self):
        conn = connections[self.conn_name]

        # 精确判断连接类型
        conn_class_name = conn.__class__.__name__
        if "PostgreSQL" in conn_class_name:
            return AsyncpgDumper
        elif "MySQL" in conn_class_name:
            return AsyncmyDumper
        elif "Sqlite" in conn_class_name:
            return AiosqliteDumper
        raise ValueError(f"Unsupported connection type: {type(conn)}")

    async def export(self):
        dumper_class = self._get_dumper_class()
        dumper = dumper_class(self.conn_name, self.tables)

        return await dumper.get_ddl()

    async def export_file(self, output_file: str):
        dumper_class = self._get_dumper_class()
        dumper = dumper_class(self.conn_name, self.tables)

        with open(output_file, "w") as f:
            ddl = await dumper.get_ddl()
            f.write("-- Generated by SchemaExporter\n")
            f.write(f"-- Connection: {self.conn_name}\n")
            f.write(f"-- Tables: {', '.join(self.tables)}\n\n")
            f.write(ddl)


# 使用示例
async def example():
    # 导出PostgreSQL（包含完整约束和索引）
    pg_exporter = SchemaExporter("pg_conn", ["users"])
    await pg_exporter.export("pg_schema.sql")

    # 导出MySQL（包含额外索引）
    mysql_exporter = SchemaExporter("mysql_conn", ["orders"])
    await mysql_exporter.export("mysql_schema.sql")

    # 导出SQLite
    sqlite_exporter = SchemaExporter("sqlite_conn", ["logs"])
    await sqlite_exporter.export("sqlite_schema.sql")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example())
