from fastapi.requests import Request as Request  # noqa


class DjangoStyleRequest(Request):
    """keep no additional data"""

    @property
    def GET(self):
        return self.query_params

    @property
    def POST(self):
        return self.form()
