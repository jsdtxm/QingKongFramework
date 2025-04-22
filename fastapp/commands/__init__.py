from .check import check
from .create import startapp
from .db import async_migrate, auto_migrate, migrate, reverse_generation
from .decorators import async_init_qingkong
from .group import Group
from .load_data import loaddata
from .misc import about, stubgen
from .server import gateway, runserver, runserver_aio, serve_static
from .shell import shell
from .user import createsuperuser

cli = Group()
