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
    address = address or socket.gethostname()

    # 确保文件存在，如果不存在则创建并初始化
    if not os.path.exists(json_file_path):
        with open(json_file_path, "w") as f:
            json.dump({}, f)

    while True:
        with open(json_file_path, "r+") as f:
            try:
                # 尝试获取排他锁，设置超时时间
                portalocker.lock(f, portalocker.LOCK_EX, timeout=timeout)
            except portalocker.LockException:
                raise Exception("获取文件锁超时")

            # 成功获取锁后读取现有内容
            try:
                data = json.load(f)
            except ValueError:
                data = {}

            # 更新字典
            data[app_name] = f"{address}:{port}"

            # 回到文件开头并写入更新后的数据
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()  # 清除文件末尾可能遗留的内容

            # 解锁
            portalocker.unlock(f)
            break


def read_port_from_json(app_name, json_file_path="service_ports.json", timeout=10):
    """
    从JSON文件中读取服务的端口号，并处理文件锁。

    :param app_name: 应用程序名称
    :param json_file_path: JSON文件路径
    :param timeout: 锁定文件前的最大等待时间
    :return: 包含address和port的字典，如果未找到对应的应用名，则返回None
    """
    while True:
        if not os.path.exists(json_file_path):
            with open(json_file_path, "w") as f:
                json.dump({}, f)

        with open(json_file_path, "r") as f:
            try:
                # 尝试获取排他锁，设置超时时间
                portalocker.lock(f, portalocker.LOCK_EX, timeout=timeout)
            except portalocker.LockException:
                raise Exception("获取文件锁超时")

            # 成功获取锁后读取现有内容
            try:
                data = json.load(f)
                result = data.get(app_name, None)
            except ValueError:
                result = None

            # 解锁
            portalocker.unlock(f)
            break

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
