from tortoise.expressions import Function

import fastapp.db.functions.json as json_func
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


class JsonExtract(Function):
    """
    JSON_EXTRACT
    :samp:`JSON_EXTRACT("{FIELD_NAME}
    """

    database_func = json_func.JsonExtract


class JsonUnquote(Function):
    """
    JSON_UNQUOTE
    :samp:`JSON_UNQUOTE("{FIELD_NAME}
    """

    database_func = json_func.JsonUnquote
