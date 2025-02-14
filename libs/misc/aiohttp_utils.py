import logging

access_logger = logging.getLogger("qingkong.access")
error_logger = logging.getLogger("qingkong.error")


def aiohttp_print_override(*args, **kwargs):
    error_logger.info("Application startup complete.")
