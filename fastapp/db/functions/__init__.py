from tortoise.expressions import Function
import fastapp.db.functions.string as string_func


class Right(Function):
    """
    RIGHT

    :samp:`RIGHT("{FIELD_NAME}", {length})`
    """

    database_func = string_func.Right


class Instr(Function):
    """
    INSTR

    :samp:`INSTR("{FIELD_NAME}", {length})`
    """

    database_func = string_func.Instr
