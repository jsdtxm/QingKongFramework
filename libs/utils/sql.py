def get_limit_offset(pageSize, current):
    """
    根据给定的pageSize和当前页码计算SQL查询中需要的LIMIT和OFFSET值。

    参数:
    pageSize (int): 每页显示的记录数。
    current (int): 当前请求的页码，从1开始。

    返回:
    (LIMIT, OFFSET)
    """
    if not isinstance(pageSize, int) or not isinstance(current, int):
        raise ValueError("pageSize和current参数必须是整数。")
    if pageSize <= 0 or current <= 0:
        raise ValueError("pageSize和current参数必须大于0。")

    limit = pageSize
    offset = (current - 1) * pageSize

    return limit, offset