from tortoise.expressions import Function
from . import pika

class Right(Function):
    """
    RIGHT

    :samp:`RIGHT("{FIELD_NAME}", {length})`
    """

    database_func = pika.Right