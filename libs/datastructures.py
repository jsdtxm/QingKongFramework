import typing

from fastapi.datastructures import UploadFile as FastApiUploadFile
from starlette.datastructures import FormData
from starlette.datastructures import Headers as Headers  # noqa: F401
from starlette.datastructures import ImmutableMultiDict


class UploadFile(FastApiUploadFile):
    async def chunks(self, chunk_size=None):
        self.file.seek(0)
        yield self.read()

    @property
    def name(self):
        return self.filename


class FileFormData(ImmutableMultiDict[str, UploadFile]):
    """
    An immutable multidict, containing both file uploads and text input.
    """

    def __init__(
        self,
        *args: FormData
        | typing.Mapping[str, UploadFile]
        | list[tuple[str, UploadFile]],
        **kwargs: UploadFile,
    ) -> None:
        super().__init__(*args, **kwargs)

    async def close(self) -> None:
        for key, value in self.multi_items():
            if isinstance(value, UploadFile):
                await value.close()


class StringFormData(ImmutableMultiDict[str, str]):
    """
    An immutable multidict, containing both file uploads and text input.
    """

    def __init__(
        self,
        *args: FormData
        | typing.Mapping[str, str]
        | list[tuple[str, str]],
        **kwargs: str,
    ) -> None:
        super().__init__(*args, **kwargs)

    async def close(self) -> None:
        pass