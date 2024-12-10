from typing import Any

import click
from uvicorn.logging import AccessFormatter, DefaultFormatter

log_config_template: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "libs.logging.QingKongDefaultFormatter",
            "fmt": "%(levelprefix)s %(app_label)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "libs.logging.QingKongAccessFormatter",
            "fmt": '%(levelprefix)s %(app_label)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}


class LoggingAppLabelMixin:
    app_label = "Default"

    def format(self, record):
        setattr(
            record, "app_label", click.style(f"[{self.app_label}]", fg="bright_black")
        )

        return super().format(record)


class QingKongDefaultFormatter(LoggingAppLabelMixin, DefaultFormatter):
    def __init__(self, app_label="Default", *args, **kwargs):
        self.app_label = app_label
        super().__init__(*args, **kwargs)


class QingKongAccessFormatter(LoggingAppLabelMixin, AccessFormatter):
    def __init__(self, app_label="Default", *args, **kwargs):
        self.app_label = app_label
        super().__init__(*args, **kwargs)
