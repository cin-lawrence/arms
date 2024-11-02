import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum, auto
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from ..utils import Soup
from .base import (
    BaseUnit,
    DumpByConfigMixin,
    DumpConfig,
    Link,
    ManyResourceResponse,
    ULinks,
)


class PageBodyFormat(StrEnum):
    Storage = "storage"
    Atlas = "atlas_doc_format"


class PageStatusCreate(StrEnum):
    Current = auto()
    Draft = auto()


class PageStatus(StrEnum):
    Current = auto()
    Archived = auto()
    Deleted = auto()
    Trashed = auto()


class PageExpandable(BaseModel):
    container: Link
    metadata: str
    restrictions: Link
    history: Link
    body: str
    version: str
    descendants: str
    space: str
    childTypes: str
    schedulePublishInfo: str
    operations: str
    schedulePublishDate: str
    children: str
    ancestors: str


class PageExtensions(BaseModel):
    position: int


class Page(BaseUnit[PageExpandable]):
    id: str
    type: str
    status: str
    title: str
    macroRenderedOutput: dict[str, Any]
    extensions: PageExtensions


class PageContentVersion(BaseModel):
    number: int
    message: str
    minorEdit: bool
    authorId: str
    createdAt: datetime


class PageBodyRef(BaseModel, ABC):
    value: str
    representation: Literal[PageBodyFormat.Storage, PageBodyFormat.Atlas]

    @property
    @abstractmethod
    def content(self) -> Any:
        raise NotImplementedError


class PageBodyStorageRef(PageBodyRef):
    representation: Literal[PageBodyFormat.Storage] = PageBodyFormat.Storage

    @property
    def content(self) -> Soup:
        return Soup(self.value, "html.parser")


class PageBodyAtlasRef(PageBodyRef):
    representation: Literal[PageBodyFormat.Atlas] = PageBodyFormat.Atlas

    @property
    def content(self) -> dict[str, Any]:
        return json.loads(self.value)


class PageBodyStorage(BaseModel):
    storage: PageBodyStorageRef


class PageBodyAtlas(BaseModel):
    atlas_doc_format: PageBodyAtlasRef


class PageContent(DumpByConfigMixin, BaseModel):
    _DumnpConfig = DumpConfig(by_alias=True)

    id: int
    version: PageContentVersion
    parentType: str
    authorId: Annotated[
        str | None,
        Field(description="seen after creating page v2"),
    ] = None
    position: int
    title: str
    status: PageStatus
    body: PageBodyStorage | PageBodyAtlas | dict[str, Any]
    parentId: int
    spaceId: int
    createdAt: Annotated[
        datetime | None,
        Field(description="seen after creating page v2"),
    ] = None
    uLinks: ULinks = Field(alias="_links")


class PageCreate(BaseModel):
    spaceId: str
    status: PageStatusCreate = PageStatusCreate.Draft
    title: str
    parentId: str
    body: PageBodyStorageRef | PageBodyAtlasRef


class PageUpdateVersion(BaseModel):
    number: int
    message: str


class PageUpdate(BaseModel):
    id: str
    status: str
    title: str
    spaceId: str | None = None
    parentId: str | None = None
    body: PageBodyStorageRef | PageBodyAtlasRef
    version: PageUpdateVersion


class GetPageParams(DumpByConfigMixin, BaseModel):
    _DumpConfig = DumpConfig(by_alias=True)

    id: list[int] | None = None
    sort: str | None = None
    status: PageStatus | None = None
    title: str | None = None
    body_format: Annotated[
        PageBodyFormat | None,
        Field(alias="body-format"),
    ] = None
    cursor: str | None = None
    limit: int | None = None
    serialize_ids_as_strings: Annotated[
        bool | None,
        Field(alias="serialize-ids-as-strings"),
    ] = None


class PagesResponse(ManyResourceResponse[PageContent]):
    pass
