from __future__ import annotations

from socket import socket
from typing import Callable

from uvicorn.config import Config
from uvicorn.supervisors.basereload import BaseReload
from uvicorn.supervisors.watchfilesreload import FileFilter
from watchfiles import watch


def WatchFilesReload_init(
    self,
    config: Config,
    target: Callable[[list[socket] | None], None],
    sockets: list[socket],
) -> None:
    BaseReload.__init__(self, config, target, sockets)
    self.reloader_name = "WatchFiles"
    self.reload_dirs = []

    for directory in config.reload_dirs:
        self.reload_dirs.append(directory)

    self.watch_filter = FileFilter(config)

    self.watcher = watch(
        *self.reload_dirs,
        watch_filter=None,
        stop_event=self.should_exit,
        # using yield_on_timeout here mostly to make sure tests don't
        # hang forever, won't affect the class's behavior
        yield_on_timeout=True,
    )
