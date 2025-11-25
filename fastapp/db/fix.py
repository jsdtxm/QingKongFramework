import re

COMMENT_BEFORE_CONSTRAINTS_PATTERN = re.compile(r"UNIQUE\s+COMMENT\s+(\S+)")


def fix_comment_before_constraints(sql: str) -> str:
    """
    预处理 CREATE TABLE 语句，将列定义中出现在 UNIQUE / PRIMARY KEY 后的
    COMMENT '...' 移到约束之前，以便 sqlglot 能解析。
    仅处理单引号 COMMENT（MySQL 默认）。
    """
    return COMMENT_BEFORE_CONSTRAINTS_PATTERN.sub(r"COMMENT \1 UNIQUE", sql)
