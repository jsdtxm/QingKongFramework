import json
import os
import socket

import portalocker


def write_port_to_json(
    app_name, port, address=None, json_file_path="service_ports.json", timeout=2
):
    """
    将服务的端口号写入JSON文件中，并处理文件锁。
    :param app_name: 应用程序名称
    :param address: 服务地址
    :param port: 服务端口号
    :param json_file_path: JSON文件路径
    :param timeout: 锁定文件前的最大等待时间
    """
    address = (
        address or socket.gethostname()
    )  # 注意：此处可能需要添加括号调用 socket.gethostname()
    # 确保文件存在，如果不存在则创建并初始化
    if not os.path.exists(json_file_path):
        with open(json_file_path, "w", encoding="utf8") as f:
            json.dump({}, f)
    try:
        with portalocker.Lock(json_file_path, mode="r+", timeout=timeout) as fh:
            # 读取现有内容
            try:
                data = json.load(fh)
            except json.JSONDecodeError:
                data = {}
            # 更新字典
            data[app_name] = f"{address}:{port}"
            # 回到文件开头并写入更新后的数据
            fh.seek(0)
            json.dump(data, fh, indent=4)
            fh.truncate()  # 清除文件末尾可能遗留的内容
            # 刷新并同步到文件系统
            fh.flush()
            os.fsync(fh.fileno())
    except portalocker.exceptions.LockException as e:
        raise e


def read_port_from_json(app_name, json_file_path="service_ports.json", timeout=10):
    """
    从JSON文件中读取服务的端口号，并处理文件锁。
    :param app_name: 应用程序名称
    :param json_file_path: JSON文件路径
    :param timeout: 锁定文件前的最大等待时间
    :return: 包含address和port的字典，如果未找到对应的应用名，则返回None
    """
    # 确保文件存在
    if not os.path.exists(json_file_path):
        with open(json_file_path, "w") as f:
            json.dump({}, f)
    try:
        # 使用portalocker获取共享锁（允许其他读操作）
        with portalocker.Lock(
            json_file_path,
            mode="r+",  # 读写模式以便加锁
            timeout=timeout,
        ) as fh:
            # 读取JSON内容
            try:
                data = json.load(fh)
                result = data.get(app_name, None)
            except json.JSONDecodeError:  # JSON解析错误处理
                result = None
    except portalocker.exceptions.LockException as e:
        raise e

    if result is not None:
        address, port = result.split(":")
        return {"address": address, "port": int(port)}
    else:
        return None


def get_existed_ports(json_file_path="service_ports.json"):
    with open(json_file_path, "r") as file:
        data = json.load(file)

    ports_set = set()  # 创建一个空集合用于存放端口号

    for value in data.values():
        # 分割字符串得到IP和端口
        _, port = value.split(":")
        ports_set.add(int(port))  # 将端口号添加到集合中

    return ports_set
