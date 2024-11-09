import asyncio
import json
from collections.abc import Coroutine
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter


class MyEncoder(json.JSONEncoder):
    def default(self, o: Any) -> str:
        if isinstance(o, Path):
            return str(o)
        if isinstance(o, datetime):
            return f"{o.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]}Z"
        if isinstance(o, UUID):
            return str(o)

        return super().default(o)


def jsondump(obj: Any, path: Path | str, indent: int = 4) -> None:
    with Path(path).open("w+") as writefile:
        return json.dump(
            obj,
            writefile,
            indent=indent,
            ensure_ascii=False,
            cls=MyEncoder,
        )


def jsondumps(obj: Any, indent: int = 4) -> str:
    return json.dumps(
        obj,
        indent=indent,
        ensure_ascii=False,
        cls=MyEncoder,
    )


class Soup(BeautifulSoup):
    def prettify(
        self,
        encoding: str | None = None,
        formatter: HTMLFormatter | None = None,
        indent: int = 4,
    ) -> str:
        formatter = formatter or HTMLFormatter(indent=indent)
        return super().prettify(encoding=encoding, formatter=formatter)


def loadhtml(content: str) -> BeautifulSoup:
    return BeautifulSoup(content, "html.parser")


def run_async(fn: Coroutine[Any, Any, Any]) -> None:
    return asyncio.run(fn)
