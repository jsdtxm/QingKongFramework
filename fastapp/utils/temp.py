import os
import platform


def get_temp_directory():
    # 获取操作系统名称
    system_name = platform.system()

    if system_name == "Linux":
        # Linux 系统的临时文件夹通常是 /tmp
        return "/tmp"
    elif system_name == "Windows":
        # Windows 系统的临时文件夹通常是 %TEMP% 环境变量指向的路径
        return os.environ.get("TEMP")  # 或者 os.environ.get("TMP")
    else:
        # 其他操作系统（如 macOS）
        return None
