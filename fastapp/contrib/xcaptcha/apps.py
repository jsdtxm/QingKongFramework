from common.settings import settings
from fastapp.apps.config import AppConfig


class XcaptchaConfig(AppConfig):
    port = settings.XCAPTCHA_SERVICE_PORT
    prefix = "xcaptcha"
