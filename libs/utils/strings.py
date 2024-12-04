def to_camel_case(snake_str):
    # 将字符串按'_'分割成列表
    components = snake_str.split("_")
    # 使用str.title()方法将每个单词的首字母转为大写，然后用join()方法连接起来
    return "".join(x.capitalize() for x in components)
