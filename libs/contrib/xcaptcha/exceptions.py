from libs.exceptions import PermissionDenied


class ThrottledException(PermissionDenied):
    action = "throttled"
    default_message = "error"

    def __init__(self, track_id=None, message=None):
        self.message = message or self.default_message
        self.track_id = track_id

    def get_json(self):
        return {"track_id": self.track_id}


class Ratelimited(ThrottledException):
    action = "block"
    default_message = (
        "Request was throttled. Please reduce your request rate and try again."
    )


class CaptchaRequired(ThrottledException):
    action = "captcha"
    default_message = (
        "Suspicious activity detected. Please complete the verification challenge."
    )
