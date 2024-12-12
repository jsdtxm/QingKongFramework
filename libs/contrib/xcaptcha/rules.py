class RateLimitRule:
    limit: int
    seconds: int
    action: str
    block_duration: int
    passthrough_duration: int

    def __init__(
        self, limit, seconds, action="block", block_duration=300, passthrough_duration=300
    ):
        """ """
        self.limit = limit
        self.seconds = seconds
        self.action = action
        self.block_duration = block_duration
        self.passthrough_duration = passthrough_duration

    def to_dict(self):
        return {
            "limit": self.limit,
            "seconds": self.seconds,
            "action": self.action,
            "block_duration": self.block_duration,
            "passthrough_duration": self.passthrough_duration,
        }
