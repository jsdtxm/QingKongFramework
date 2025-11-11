import errno
import os
import threading
import time
from types import SimpleNamespace
from typing import TYPE_CHECKING, Optional, Union

from redis.asyncio.lock import Lock as RawRedisAsyncioLock

from fastapp.cache.redis import get_redis_connection
from fastapp.conf import settings
from fastapp.utils.temp import get_temp_directory

if TYPE_CHECKING:
    from redis.asyncio import Redis, RedisCluster


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
        self,
        name: str,
        dir: Optional[str] = None,
        timeout: Optional[float] = 60,
        interval: Optional[float] = 0.1,
    ):
        """
        基于文件的锁，支持 with 语法
        :param name: 锁文件名（例如 "mylock.lock"）
        :param dir: 锁文件目录，默认为 /tmp
        :param timeout: 超时时间（秒），超时后抛出 TimeoutError
        """
        self.lock_file = os.path.join(dir or get_temp_directory(), name)
        self.timeout = timeout
        self.interval = interval
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
                time.sleep(self.interval)
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


class RedisLock(RawRedisAsyncioLock):
    def __init__(
        self,
        name: Optional[Union[str, bytes, memoryview]] = None,
        redis: Optional[Union["Redis", "RedisCluster"]] = None,
        timeout: Optional[float] = None,
        sleep: float = 0.1,
        blocking: bool = True,
        blocking_timeout: Optional[float] = None,
        thread_local: bool = True,
    ):
        """
        Create a new Lock instance named ``name`` using the Redis client
        supplied by ``redis``.

        ``timeout`` indicates a maximum life for the lock in seconds.
        By default, it will remain locked until release() is called.
        ``timeout`` can be specified as a float or integer, both representing
        the number of seconds to wait.

        ``sleep`` indicates the amount of time to sleep in seconds per loop
        iteration when the lock is in blocking mode and another client is
        currently holding the lock.

        ``blocking`` indicates whether calling ``acquire`` should block until
        the lock has been acquired or to fail immediately, causing ``acquire``
        to return False and the lock not being acquired. Defaults to True.
        Note this value can be overridden by passing a ``blocking``
        argument to ``acquire``.

        ``blocking_timeout`` indicates the maximum amount of time in seconds to
        spend trying to acquire the lock. A value of ``None`` indicates
        continue trying forever. ``blocking_timeout`` can be specified as a
        float or integer, both representing the number of seconds to wait.

        ``thread_local`` indicates whether the lock token is placed in
        thread-local storage. By default, the token is placed in thread local
        storage so that a thread only sees its token, not a token set by
        another thread. Consider the following timeline:

            time: 0, thread-1 acquires `my-lock`, with a timeout of 5 seconds.
                     thread-1 sets the token to "abc"
            time: 1, thread-2 blocks trying to acquire `my-lock` using the
                     Lock instance.
            time: 5, thread-1 has not yet completed. redis expires the lock
                     key.
            time: 5, thread-2 acquired `my-lock` now that it's available.
                     thread-2 sets the token to "xyz"
            time: 6, thread-1 finishes its work and calls release(). if the
                     token is *not* stored in thread local storage, then
                     thread-1 would see the token value as "xyz" and would be
                     able to successfully release the thread-2's lock.

        In some use cases it's necessary to disable thread local storage. For
        example, if you have code where one thread acquires a lock and passes
        that lock instance to a worker thread to release later. If thread
        local storage isn't disabled in this case, the worker thread won't see
        the token set by the thread that acquired the lock. Our assumption
        is that these cases aren't common and as such default to using
        thread local storage.
        """
        self.redis = redis or get_redis_connection()
        self.name = name or settings.PROJECT_NAME
        if not self.name:
            raise ValueError("RedisLock name must be set")
        self.timeout = timeout
        self.sleep = sleep
        self.blocking = blocking
        self.blocking_timeout = blocking_timeout
        self.thread_local = bool(thread_local)
        self.local = threading.local() if self.thread_local else SimpleNamespace()
        self.local.token = None
        self.register_scripts()
