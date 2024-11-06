import multiprocessing

import fire
import uvicorn

class Command:
    def runserver(
        self, host="0.0.0.0", port=8000, workers=1, reload=False, log_level="debug"
    ):
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            workers=workers,
            reload=reload,
            log_level=log_level,
        )

if __name__ == "__main__":
    multiprocessing.freeze_support()
    fire.Fire(Command)
