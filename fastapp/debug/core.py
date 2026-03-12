import json
import os
import re
import socket
import sys
from datetime import datetime
from types import TracebackType
from typing import Any, Optional, Tuple

import jinja2
from pydantic import BaseModel
from starlette.datastructures import UploadFile
from starlette.requests import Request

from fastapp.conf import settings
from fastapp.core.mail import mail_admins

SECRET_URI_PATTERN = re.compile(r"([a-zA-Z0-9_]+://)([^:@]*:)?([^@]+)@")


def pprint_filter(value: Any) -> str:
    try:
        return json.dumps(value, indent=4, ensure_ascii=False, default=str)
    except Exception:
        return repr(value)


def add_filter(value: Any, arg: Any) -> Any:
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value


def dictsort_filter(value: Any, arg: str = "0") -> list:
    # 如果传入的是 dict，先转为 (key, value) 元组列表再排序
    if isinstance(value, dict):
        items = list(value.items())
        return sorted(items, key=lambda item: str(item[0]))

    # 如果传入的是列表
    def sort_key(item):
        if isinstance(item, tuple):
            return str(item[0])
        elif isinstance(item, dict):
            return str(item.get(arg, ""))
        return ""

    return sorted(value, key=sort_key)


def date_filter(value: Any, format_string: str = "r") -> str:
    if isinstance(value, datetime):
        return value.strftime(format_string)
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return dt.strftime(format_string)
        except ValueError:
            return value
    return str(value)


def hidden_password(pair: Tuple[str, Any]):
    k, v = pair
    k = k.lower()
    if (
        "password" in k
        or "secret" in k
        or "api_key" in k
        or "token" in k
        or k in {"pwd"}
    ):
        return k, "<hidden>"

    if isinstance(v, str) and SECRET_URI_PATTERN.match(v):
        return k, SECRET_URI_PATTERN.sub(r"\g<1>\g<2><hidden>@", v)

    if v and isinstance(v, dict) and isinstance(next(iter(v.values()), None), dict):
        for _, item in v.items():
            if item.get("PASSWORD") or item.get("API_KEY"):
                item["PASSWORD"] = "<hidden>"
            elif item.get("LOCATION") and SECRET_URI_PATTERN.match(item["LOCATION"]):
                item["LOCATION"] = SECRET_URI_PATTERN.sub(
                    r"\g<1>\g<2><hidden>@", item["LOCATION"]
                )

    return k, v


class FrameInfo(BaseModel):
    filename: str
    lineno: int
    function: str
    context_line: Optional[str] = None
    pre_context: Optional[list[str]] = None
    pre_context_lineno: Optional[int] = None
    post_context: Optional[list[str]] = None
    vars: Optional[dict] = None
    id: int = 0
    tb: Optional[str] = None
    colno: Optional[int] = None
    exc_cause: Optional[str] = None
    exc_cause_explicit: bool = False
    type: str = ""


class ExceptionReportData(BaseModel):
    exception_type: Optional[str] = None
    exception_value: Optional[str] = None
    exception_notes: Optional[str] = None
    frames: list[FrameInfo] = []
    lastframe: Optional[FrameInfo] = None
    request: Optional[Any] = None
    framework_version_info: Optional[str] = None
    raising_view_name: Optional[str] = None
    sys_executable: Optional[str] = None
    sys_version_info: Optional[str] = None
    sys_path: Optional[list] = None
    hostname: Optional[str] = None
    system_user: Optional[str] = None
    server_time: Optional[datetime] = None
    unicode_hint: Optional[str] = None
    template_does_not_exist: bool = False
    postmortem: Optional[list] = None
    user_str: Optional[str] = None
    request_GET_items: Optional[list] = None
    filtered_POST_items: Optional[list] = None
    request_FILES_items: Optional[list] = None
    request_COOKIES_items: Optional[list] = None
    request_HEADERS_items: Optional[list] = None
    settings: Optional[list] = None
    is_email: bool = False


def get_traceback_frames(
    exc_value: BaseException,
    tb: Optional[TracebackType],
    context_lines: int = 10,
    include_packages: Optional[list[str]] = None,
    project_root: Optional[str] = None,
) -> list[FrameInfo]:
    frames: list[FrameInfo] = []
    exc_cause: Optional[BaseException] = None
    exc_cause_explicit: bool = False

    # Default include packages if not provided
    if include_packages is None:
        include_packages = []

    # Get project root if not provided
    if project_root is None:
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    def should_include_frame(filename: str) -> bool:
        # Include if file is in project root
        if filename.startswith(project_root):
            return True
        # Include if file is in any of the specified packages
        for package in include_packages:
            if f"/{package}/" in filename or filename.endswith(f"/{package}.py"):
                return True
        # Exclude otherwise (library code)
        return False

    while tb is not None:
        frame = tb.tb_frame
        filename = frame.f_code.co_filename
        lineno = tb.tb_lineno
        function = frame.f_code.co_name

        # Skip frames that should not be included
        if not should_include_frame(filename):
            tb = tb.tb_next
            continue

        pre_context_lineno = max(1, lineno - context_lines)
        post_context_lineno = lineno + context_lines + 1

        source_lines: list[str] = []
        try:
            with open(filename, "r") as f:
                for i, line in enumerate(f, start=1):
                    if pre_context_lineno <= i <= post_context_lineno:
                        source_lines.append(line.rstrip())
        except (OSError, IOError):
            pass

        context_line = None
        pre_context: list[str] = []
        post_context: list[str] = []

        for i, line in enumerate(source_lines):
            line_no = pre_context_lineno + i
            if line_no == lineno:
                context_line = line
            elif line_no < lineno:
                pre_context.append(line)
            else:
                post_context.append(line)

        vars_dict: dict = {}
        for key, value in frame.f_locals.items():
            try:
                vars_dict[key] = repr(value)
            except Exception:
                vars_dict[key] = "<unable to repr>"

        frames.append(
            FrameInfo(
                filename=filename,
                lineno=lineno,
                function=function,
                context_line=context_line,
                pre_context=pre_context,
                pre_context_lineno=pre_context_lineno,
                post_context=post_context,
                vars=vars_dict if vars_dict else None,
                id=len(frames),
                tb=str(tb),
            )
        )

        tb = tb.tb_next

    if exc_value and exc_value.__cause__:
        exc_cause = exc_value.__cause__
        exc_cause_explicit = True
    elif exc_value and exc_value.__context__:
        exc_cause = exc_value.__context__
        exc_cause_explicit = False

    if exc_cause:
        for frame in frames:
            frame.exc_cause = str(exc_cause)
            frame.exc_cause_explicit = exc_cause_explicit

    return frames


def get_last_frame(frames: list[FrameInfo]) -> Optional[FrameInfo]:
    if frames:
        return frames[-1]
    return None


def get_caller_frame(frames: list[FrameInfo]) -> Optional[FrameInfo]:
    if len(frames) >= 2:
        return frames[-2]
    return None


def get_system_info() -> dict:
    try:
        system_user = os.getlogin()
    except Exception:
        system_user = os.getuid()

    return {
        "sys_executable": sys.executable,
        "sys_version_info": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "sys_path": sys.path,
        "hostname": socket.gethostname(),
        "system_user": system_user,
    }


def get_framework_info() -> dict:
    return {
        "framework_version_info": "latest",
    }


class ExceptionReporter:
    template_path: str = os.path.join(
        os.path.dirname(__file__), "template", "technical_500_jinja2.html"
    )

    def __init__(
        self,
        exc_type: Optional[type] = None,
        exc_value: Optional[BaseException] = None,
        tb: Optional[TracebackType] = None,
        request: Optional[Request] = None,
        is_email: bool = False,
        include_packages: Optional[list[str]] = None,
        project_root: Optional[str] = None,
    ):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.tb = tb
        self.request = request
        self.is_email = is_email
        self.include_packages = include_packages
        self.project_root = project_root

    def get_traceback_frames(self) -> list[FrameInfo]:
        return get_traceback_frames(
            self.exc_value,
            self.tb,
            include_packages=self.include_packages,
            project_root=self.project_root,
        )

    async def get_exception_data(self) -> ExceptionReportData:
        frames = self.get_traceback_frames()
        lastframe = get_last_frame(frames)

        system_info = get_system_info()
        framework_info = get_framework_info()

        user_str = None
        request_GET_items = None
        filtered_POST_items = None
        request_FILES_items = None
        request_COOKIES_items = None
        request_HEADERS_items = None

        if self.request:
            try:
                if hasattr(self.request, "user"):
                    user = self.request.user
                    if user and user.is_authenticated:
                        user_str = str(user)
            except Exception:
                pass

            try:
                request_GET_items = list(self.request.query_params.items())
            except Exception:
                pass

            try:
                json_data = json.loads(self.request.state.cache_body)
                filtered_POST_items = list(map(hidden_password, json_data.items()))
            except Exception:
                pass

            try:
                request_FILES_items = [
                    (
                        k,
                        f"<UploadFile '{v.filename}' size={v.size} content_type='{v.content_type}'>",
                    )
                    for k, v in self.request.state.cache_form.multi_items()
                    if isinstance(v, UploadFile)
                ]

            except Exception:
                pass

            try:
                request_COOKIES_items = list(self.request.cookies.items())
            except Exception:
                pass

            try:
                request_HEADERS_items = list(
                    filter(lambda x: x[0] != "cookie", self.request.headers.items())
                )
            except Exception:
                pass

        settings_items = {}
        try:
            settings_items = list(map(hidden_password, settings.model_dump().items()))
        except Exception as e:
            raise e
            pass

        return ExceptionReportData(
            exception_type=self.exc_type.__name__ if self.exc_type else None,
            exception_value=str(self.exc_value) if self.exc_value else None,
            frames=frames,
            lastframe=lastframe,
            request=self.request,
            framework_version_info=framework_info.get("framework_version_info"),
            raising_view_name=None,
            sys_executable=system_info.get("sys_executable"),
            sys_version_info=system_info.get("sys_version_info"),
            sys_path=system_info.get("sys_path"),
            hostname=system_info.get("hostname"),
            system_user=system_info.get("system_user"),
            server_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_str=user_str,
            request_GET_items=request_GET_items,
            filtered_POST_items=filtered_POST_items,
            request_FILES_items=request_FILES_items,
            request_COOKIES_items=request_COOKIES_items,
            request_HEADERS_items=request_HEADERS_items,
            settings=settings_items,
            is_email=self.is_email,
        )

    async def get_html(self) -> str:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.dirname(self.template_path)),
            autoescape=jinja2.select_autoescape(
                enabled_extensions=("html", "xml"),
                default_for_string=True,
            ),
        )

        env.filters["pprint"] = pprint_filter
        env.filters["add"] = add_filter
        env.filters["dictsort"] = dictsort_filter
        env.filters["date"] = date_filter

        template = env.get_template(os.path.basename(self.template_path))

        context = await self.get_exception_data()
        context_dict = context.model_dump()

        if context_dict.get("sys_path"):
            context_dict["sys_path"] = pprint_filter(context_dict["sys_path"])

        return template.render(**context_dict)


async def handler_adapter(request, exc):
    exc_type, exc_value, tb = sys.exc_info()
    exc_type, exc_value = exc_type or type(exc), exc_value or exc

    html = await exception_report_html(
        exc_type=exc_type,
        exc_value=exc_value,
        tb=tb,
        request=request,
    )

    await mail_admins(
        subject=str(exc_value) if exc_type else "Exception Report",
        message="Exception Report",
        html_message=html,
    )


async def exception_report_html(
    exc_type: Optional[type],
    exc_value: Optional[BaseException],
    tb: Optional[TracebackType],
    request: Optional[Any] = None,
    is_email: bool = False,
    include_packages: Optional[list[str]] = None,
    project_root: Optional[str] = None,
) -> str:
    reporter = ExceptionReporter(
        exc_type=exc_type,
        exc_value=exc_value,
        tb=tb,
        request=request,
        is_email=is_email,
        include_packages=include_packages,
        project_root=project_root,
    )
    return await reporter.get_html()
