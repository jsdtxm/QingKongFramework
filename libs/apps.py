from pydantic import BaseModel


class AppConfig(BaseModel):
    name: str = "app"
    prefix: str = name
    port: int = 18000
