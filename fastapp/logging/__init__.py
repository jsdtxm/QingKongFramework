from copy import deepcopy
from typing import Any

import click
from uvicorn.logging import AccessFormatter, DefaultFormatter

from common.settings import settings

log_config_template: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "fastapp.logging.QingKongDefaultFormatter",
            "fmt": "%(levelprefix)s %(app_label)s %(asctime)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "fastapp.logging.QingKongAccessFormatter",
            "fmt": '%(levelprefix)s %(app_label)s %(asctime)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
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
        "qingkong": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "qingkong.error": {"level": "INFO"},
        "qingkong.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


def get_log_config_template():
    if settings.LOGGING_CONFIG:
        return deepcopy(settings.LOGGING_CONFIG)
    return deepcopy(log_config_template)


class LoggingAppLabelMixin:
    app_label = "Default"

    def format(self, record):
        setattr(
            record, "app_label", click.style(f"[{self.app_label}]", fg="bright_black")
        )

        return super().format(record)


class QingKongDefaultFormatter(LoggingAppLabelMixin, DefaultFormatter):
    def __init__(
        self, app_label="Default", *args, datefmt="%Y-%m-%d %H:%M:%S", **kwargs
    ):
        self.app_label = app_label
        super().__init__(*args, datefmt=datefmt, **kwargs)


class QingKongAccessFormatter(LoggingAppLabelMixin, AccessFormatter):
    def __init__(
        self, app_label="Default", *args, datefmt="%Y-%m-%d %H:%M:%S", **kwargs
    ):
        self.app_label = app_label
        super().__init__(*args, datefmt=datefmt, **kwargs)


def generate_app_logging_config(app_label):
    log_config = get_log_config_template()
    for formatter in log_config["formatters"].values():
        formatter["app_label"] = app_label

    return log_config
