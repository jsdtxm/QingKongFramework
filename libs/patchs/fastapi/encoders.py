import datetime

from fastapi.encoders import ENCODERS_BY_TYPE

ENCODERS_BY_TYPE[datetime.datetime] = lambda x: x.strftime("%Y-%m-%d %H:%M:%S")
