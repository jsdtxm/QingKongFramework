def get_slice_indices(pagesize, page):
    """
    根据页码和每页大小返回切片的起始和结束索引。

    参数:
        pagesize (int): 每页的数据条数
        page (int): 当前页码（从 1 开始）

    返回:
        tuple: (start, end) 可用于 list[start:end]
    """
    if page < 1 or pagesize < 1:
        raise ValueError("页码和每页大小都必须大于等于1")

    start = (page - 1) * pagesize
    end = start + pagesize
    return start, end
