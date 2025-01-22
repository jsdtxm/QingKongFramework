from .check import check
from .create import startapp
from .db import async_migrate, migrate, reverse_generation
from .group import Group
from .misc import about, stubgen
from .server import gateway, runserver
from .shell import shell
from .user import createsuperuser
from .load_data import loaddata

cli = Group()
