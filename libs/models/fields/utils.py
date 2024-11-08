import re


def exact_app_name(module_name):
    return re.search(r"^\S+?\.(\S+)\.\S+$", module_name).group(1)


def model_object_to_name(model):
    return f"{exact_app_name(model.__module__)}.{model.__name__}"