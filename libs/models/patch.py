from tortoise import models

from .info import MetaInfo


def patch_meta_info():
    print("patch_meta_info")
    models.MetaInfo = MetaInfo
