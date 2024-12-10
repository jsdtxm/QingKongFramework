from socket import socket
from typing import Callable

from uvicorn.config import Config

def subprocess_started(
    config: Config,
    target: Callable[..., None],
    sockets: list[socket],
    stdin_fileno: int | None,
) -> None:
    """
    Called when the child process starts.

    * config - The Uvicorn configuration instance.
    * target - A callable that accepts a list of sockets. In practice this will
               be the `Server.run()` method.
    * sockets - A list of sockets to pass to the server. Sockets are bound once
                by the parent process, and then passed to the child processes.
    * stdin_fileno - The file number of sys.stdin, so that it can be reattached
                     to the child process.
    """
    # Re-open stdin.
    # if stdin_fileno is not None:
    #     sys.stdin = os.fdopen(stdin_fileno)  # pragma: full coverage

    # Logging needs to be setup again for each child.
    config.configure_logging()

    try:
        # Now we can call into `Server.run(sockets=sockets)`
        target(sockets=sockets)
    except KeyboardInterrupt:  # pragma: no cover
        # supress the exception to avoid a traceback from subprocess.Popen
        # the parent already expects us to end, so no vital information is lost
        pass
