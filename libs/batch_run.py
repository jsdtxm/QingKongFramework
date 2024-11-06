import subprocess

PORT_CONFIG = {
    "main": 18001,
    "user": 18002,
}


def start_uvicorn(app_module, port, host="127.0.0.1", workers=1, reload=False):
    command = [
        "uvicorn",
        f"apps.{app_module}.main:app",
        "--port",
        str(port),
        "--host",
        host,
        "--workers",
        str(workers),
        "--loop",
        "uvloop"
    ]

    if reload:
        command.append("--reload")

    process = subprocess.Popen(command)

    return process


def batch_run(host="127.0.0.1", workers=1, reload=False):
    processes = []
    for app, port in PORT_CONFIG.items():
        p = start_uvicorn(app, port, host, workers, reload)
        processes.append(p)

    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("Interrupted, stopping all servers...")
        for p in processes:
            if p.poll() is None:
                p.terminate()
                p.wait()


if __name__ == "__main__":
    batch_run()
