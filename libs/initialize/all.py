from .apps import init_apps
from .db import async_init_db

def init_all():
    init_apps()
    async_init_db()