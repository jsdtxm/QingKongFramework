import re

def to_camel_case(snake_str):
    # 将字符串按'_'分割成列表
    components = snake_str.split("_")
    # 使用str.title()方法将每个单词的首字母转为大写，然后用join()方法连接起来
    return "".join(x.capitalize() for x in components)


def pretty_name(name):
    """Convert 'first_name' to 'First name'."""
    if not name:
        return ""
    return name.replace("_", " ").capitalize()


def split_camel_case(camel_case_string):
    # 使用正则表达式按大写字母分割字符串，除了首字母外
    words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', camel_case_string)
    
    return words