import re


def exact_app_name(module_name):
    return re.search(r"^\S+?\.(\S+)\.\S+$", module_name).group(1)
