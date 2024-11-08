from pathlib import Path
from typing import Final

from pydantic_settings import BaseSettings, SettingsConfigDict


class BasicAuthCredentials(BaseSettings):
    MIN_LINES: Final[int] = 2
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="basicauth_",
    )

    username: str
    password: str

    @classmethod
    def from_file(cls, path: str | Path) -> "BasicAuthCredentials":
        path = Path(path)
        if not path.exists():
            raise ValueError(f"file not found at {path}")
        with path.open() as readfile:
            lines = readfile.readlines()
        if len(lines) < cls.MIN_LINES:
            raise ValueError("invalid credentials for basic auth")
        username = lines[0].strip()
        password = lines[1].strip()
        return cls(username=username, password=password)
