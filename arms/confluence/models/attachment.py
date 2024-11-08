from datetime import datetime
from mimetypes import guess_extension
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field

from .base import (
    BaseUnit,
    DumpConfig,
    Link,
    ManyResourceResponse,
    ResourceCreateResponse,
    _BaseUnitPartial,
)
from .page import Page
from .user import User


class VersionExpandable(BaseModel):
    collaborators: str
    content: Link


class Version(BaseUnit[VersionExpandable]):
    by: User
    when: datetime
    friendlyWhen: str
    message: (
        Annotated[
            str,
            Field(
                description=(
                    "will present if `comment` is present in attachment create"
                ),
            ),
        ]
        | None
    ) = None
    number: int
    minorEdit: bool
    contentTypeModified: bool


class MetadataExpandable(BaseModel):
    currentuser: str
    comments: str
    sourceTemplateEntityId: str
    simple: str
    properties: str
    frontend: str
    likes: str


class _MetadataPartial(_BaseUnitPartial[MetadataExpandable]):
    _DumpConfig = DumpConfig(
        by_alias=True,
        exclude_unset=True,
        exclude_none=True,
    )

    mediaType: str
    comment: str | None = None
    labels: dict[str, Any] | None = None


class MetadataBase(_MetadataPartial):
    uExpandable: MetadataExpandable


class AttachmentMetadata(_MetadataPartial):
    pass


class AttachmentExtensions(BaseModel):
    mediaType: str
    fileSize: int
    comment: (
        Annotated[
            str,
            Field(
                description=(
                    "will present if `comment` is present in attachment create"
                ),
            ),
        ]
        | None
    ) = None
    mediaTypeDescription: str | None = None
    fileId: UUID
    collectionName: str

    @property
    def suffix(self) -> str | None:
        return guess_extension(self.mediaType)

    @property
    def filename(self) -> str:
        return f"{self.fileId}{self.suffix}"


class AttachmentExpandable(BaseModel):
    childTypes: str
    schedulePublishInfo: str
    operations: str
    schedulePublishDate: str
    children: Link
    restrictions: Link
    history: Link
    ancestors: str
    body: str
    descendants: Link
    space: str


class _AttachmentPartial(BaseUnit[AttachmentExpandable]):
    id: str
    type: str
    status: str
    title: str
    version: Version | None = None
    container: Page | None = None
    macroRenderedOutput: dict[str, Any]
    extensions: AttachmentExtensions | None = None


class AttachmentCreate(_AttachmentPartial):
    version: Version
    container: Page
    metadata: MetadataBase


class Attachment(_AttachmentPartial):
    metadata: AttachmentMetadata
    extensions: AttachmentExtensions


class AttachmentCreateResponse(ResourceCreateResponse[Attachment]):
    pass


class AttachmentsResponse(ManyResourceResponse[Attachment]):
    pass
