import json
import fcntl
import time
import os
import socket

def write_port_to_json(app_name, port, address=None, json_file_path='service_ports.json', timeout=2):
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
        with open(json_file_path, 'w') as f:
            json.dump({}, f)

    start_time = time.time()
    while True:
        with open(json_file_path, 'r+') as f:
            try:
                # 尝试获取锁
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                # 如果无法立即获得锁，则检查是否超时
                if time.time() - start_time > timeout:
                    raise Exception("获取文件锁超时")
                else:
                    time.sleep(0.1)  # 等待一段时间后重试
                    continue
            
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
            fcntl.flock(f, fcntl.LOCK_UN)
            break


def read_port_from_json(app_name, json_file_path='service_ports.json', timeout=10):
    """
    从JSON文件中读取服务的端口号，并处理文件锁。
    
    :param app_name: 应用程序名称
    :param json_file_path: JSON文件路径
    :param timeout: 锁定文件前的最大等待时间
    :return: 包含address和port的字典，如果未找到对应的应用名，则返回None
    """
    start_time = time.time()
    while True:
        if not os.path.exists(json_file_path):
            with open(json_file_path, 'w') as f:
                json.dump({}, f)
                
        with open(json_file_path, 'r') as f:
            try:
                # 尝试获取共享锁（允许其他读操作同时进行）
                fcntl.flock(f, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except IOError:
                # 如果无法立即获得锁，则检查是否超时
                if time.time() - start_time > timeout:
                    raise Exception("获取文件锁超时")
                else:
                    time.sleep(0.1)  # 等待一段时间后重试
                    continue
            
            # 成功获取锁后读取现有内容
            try:
                data = json.load(f)
                result = data.get(app_name, None)
            except ValueError:
                result = None
            
            # 解锁
            fcntl.flock(f, fcntl.LOCK_UN)
            break
    
    if result is not None:
        address, port = result.split(":")
        return {"address": address, "port": int(port)}
    else:
        return None
