import re

BRACE_REGEX = re.compile(r"\{([a-zA-Z0-9_]+)\}")


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
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", camel_case_string)

    return words


def extract_type_and_name(pattern):
    # 定义一个正则表达式模式，用于匹配 "type:name" 的形式
    regex = r"/<(\w+):(\w+)>"

    # 使用 re 模块的 search 方法查找匹配项
    match = re.search(regex, pattern)

    # 如果找到了匹配项，则返回 (type, name) 元组的列表
    if match:
        return [(match.group(2), match.group(1))]
    else:
        # 如果没有找到匹配项，则返回空列表
        return []


def convert_url_format(url_pattern):
    """
    将形如 "download/<uuid:file_uuid>" 的URL模式转换为 "download/{file_uuid}"

    参数:
        url_pattern (str): 原始的URL模式。

    返回:
        str: 转换后的URL模式。
    """

    # 使用正则表达式查找 "<type:name>" 形式的子串
    def replacement(match):
        # 返回只包含名称部分的字符串，用大括号包裹
        return "{" + match.group(2) + "}"

    # 定义正则表达式模式，匹配 "<type:name>"
    regex = r"(?<=/)<(\w+):(\w+)>"

    # 使用 re.sub 方法进行替换
    converted_url = re.sub(regex, replacement, url_pattern)

    return converted_url
