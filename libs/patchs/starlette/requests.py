from starlette.requests import HTTPConnection, cookie_parser


@property
def cookies(self: HTTPConnection) -> dict[str, str]:
    if not hasattr(self, "_cookies"):
        cookies: dict[str, str] = {}
        cookie_header = self.headers.getlist("cookie")
        if len(cookie_header) > 1:
            cookie_header = "; ".join(cookie_header)
        elif len(cookie_header) == 1:
            cookie_header = cookie_header[0]

        if cookie_header:
            cookies = cookie_parser(cookie_header)
        self._cookies = cookies
    return self._cookies


HTTPConnection.cookies = cookies
