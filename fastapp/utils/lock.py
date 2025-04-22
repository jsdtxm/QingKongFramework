import errno
import os
import time
from typing import Optional

from fastapp.utils.temp import get_temp_directory


class FileLock:
    """
    使用默认的 /tmp 目录
    ```
    with FileLock(name="mylock.lock", timeout=5):
        print("锁已获取，执行关键操作...")
        time.sleep(3)
    ```
    指定自定义目录
    ```
    with FileLock(name="custom.lock", dir="/var/lock", timeout=2):
        print("自定义目录锁生效")
    ```
    """

    def __init__(
        self, name: str, dir: Optional[str] = None, timeout: Optional[float] = 5
    ):
        """
        基于文件的锁，支持 with 语法
        :param name: 锁文件名（例如 "mylock.lock"）
        :param dir: 锁文件目录，默认为 /tmp
        :param timeout: 超时时间（秒），超时后抛出 TimeoutError
        """
        self.lock_file = os.path.join(dir or get_temp_directory(), name)
        self.timeout = timeout
        self.fd = None

    def __enter__(self):
        start_time = time.time()
        while True:
            try:
                # 原子性创建锁文件并写入PID
                self.fd = os.open(self.lock_file, os.O_EXCL | os.O_CREAT | os.O_RDWR)
                os.write(self.fd, f"{os.getpid()}\n".encode())
                os.fsync(self.fd)
                return self
            except FileExistsError:
                # 检查是否为残留的过期锁
                if self._is_stale():
                    self._clear_stale_lock()
                    continue
                # 超时判断
                if self.timeout and (time.time() - start_time) >= self.timeout:
                    raise TimeoutError(f"无法在 {self.timeout} 秒内获取锁")
                time.sleep(0.1)
            except:
                self._cleanup()
                raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()

    def _is_stale(self) -> bool:
        """检查锁文件是否属于已终止的进程"""
        try:
            with open(self.lock_file, "r") as f:
                pid = int(f.readline().strip())
        except (FileNotFoundError, ValueError):
            return True  # 文件不存在或内容无效
        return not self._is_process_alive(pid)

    @staticmethod
    def _is_process_alive(pid: int) -> bool:
        """检查进程是否存在"""
        try:
            os.kill(pid, 0)
        except OSError as e:
            return e.errno != errno.ESRCH  # False 表示进程不存在
        return True

    def _clear_stale_lock(self):
        """清理残留的过期锁文件"""
        try:
            os.remove(self.lock_file)
        except FileNotFoundError:
            pass

    def _cleanup(self):
        """释放锁资源"""
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            os.remove(self.lock_file)
        except FileNotFoundError:
            pass
