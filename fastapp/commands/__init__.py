from .check import check
from .create import startapp
from .db import async_migrate, auto_migrate, migrate, reverse_generation
from .decorators import async_init_fastapp
from .group import Group
from .load_data import loaddata
from .dump_data import dumpdata
from .misc import about, stubgen
from .server import gateway, runserver, runserver_aio, serve_static
from .shell import shell
from .tests import run_tests
from .user import createsuperuser

cli = Group()
