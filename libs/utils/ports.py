import socket

def find_free_port(start=19000, end=20000):
    """
    在指定的范围内查找一个未被占用的端口。

    :param start: 范围内起始端口
    :param end: 范围内结束端口
    :return: 未被占用的端口号或者 None（如果在范围内没有可用端口）
    """
    for port in range(start, end + 1):
        # 创建一个新的socket对象用于测试
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                # 尝试绑定端口
                s.bind(('127.0.0.1', port))
                return port
            except socket.error as e:
                # 如果端口已被占用或出现其他错误，则继续循环
                if e.errno == 98:  # Address already in use
                    continue
                else:
                    raise e  # 如果是其他异常则抛出
    return None