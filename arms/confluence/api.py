import asyncio
import json
import logging
from enum import StrEnum
from mimetypes import guess_extension, guess_type
from pathlib import Path
from typing import Any
from uuid import UUID

import aiofiles
from aiohttp import BasicAuth, ClientSession, FormData
from aiohttp.client_exceptions import ClientResponseError
from pydantic_settings import BaseSettings, SettingsConfigDict

from .creds import BasicAuthCredentials
from .endpoints import V1Endpoints as V1EndpointsSettings
from .endpoints import V2Endpoints as V2EndpointsSettings
from .exc import ClientError, ClientInternalError, ClientNotAuthenticated
from .models.ancestor import AncestorsResponse
from .models.attachment import (
    Attachment,
    AttachmentCreateResponse,
    AttachmentsResponse,
)
from .models.page import (
    GetPageParams,
    PageBodyFormat,
    PageContent,
    PageCreate,
    PagesResponse,
    PageUpdate,
)
from .models.space import SpacesResponse

_4KB_In_Bytes = 4 * 1024


class RequestMethod(StrEnum):
    Get = "GET"
    Post = "POST"
    Put = "PUT"


class ToolkitSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="api_",
    )

    root: str


class ConfluenceToolkit:
    V1Endpoints = V1EndpointsSettings
    V2Endpoints = V2EndpointsSettings

    def __init__(
        self,
        credentials: BasicAuthCredentials,
        root: str,
        v1urls: V1EndpointsSettings | None = None,
        v2urls: V2EndpointsSettings | None = None,
    ):
        self.root = root
        self.v1urls = v1urls or self.V1Endpoints()
        self.v2urls = v2urls or self.V2Endpoints()

        self.session = None
        self.credentials = BasicAuth(
            credentials.username, credentials.password
        )

    @classmethod
    def from_env(cls, env_path: str | Path = ".env") -> "ConfluenceToolkit":
        return cls(
            BasicAuthCredentials(_env_file=env_path),
            ToolkitSettings(_env_file=env_path).root,
            cls.V1Endpoints(),
            cls.V2Endpoints(),
        )

    def construct_url(self, suffix: str) -> str:
        return f"{self.root}{suffix}"

    async def req_in_session(
        self,
        method: RequestMethod,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession
        """
        async with ClientSession() as session:
            async with session.request(
                method,
                self.construct_url(path),
                auth=self.credentials,
                **kwargs,
            ) as response:
                text = await response.text()
                try:
                    response.raise_for_status()
                except ClientResponseError as e:
                    logging.error(text)
                    logging.exception(e)
                    if e.status >= 500:
                        raise ClientInternalError(e, text)
                    elif e.status == 401:
                        raise ClientNotAuthenticated(e, text)
                    raise ClientError(e, text)
                return await response.json()

    async def get_spaces(self) -> SpacesResponse:
        """V1"""
        response = await self.req_in_session(
            RequestMethod.Get,
            self.v1urls.Spaces,
        )
        return SpacesResponse.model_validate(response)

    async def get_attachments_from_page(
        self,
        page_id: int | str,
    ) -> AttachmentsResponse:
        """V1"""
        response = await self.req_in_session(
            RequestMethod.Get,
            self.v1urls.Attachments.format(page_id=str(page_id)),
        )
        return AttachmentsResponse.model_validate(response)

    async def create_attachment(
        self,
        page_id: int | str,
        filepath: Path,
        comment: str | None = None,
        content_type: str | None = None,
        filename: str | None = None,
    ) -> AttachmentCreateResponse:
        """V1"""
        if not filepath.exists():
            raise FileNotFoundError(filepath)
        async with aiofiles.open(filepath, "rb") as asyncfile:
            content_type = content_type or guess_type(filepath)[0]
            filename = filename or filepath.name
            formdata = FormData()
            formdata.add_field("minorEdit", "true")
            formdata.add_field("comment", comment)
            formdata.add_field(
                "file",
                await asyncfile.read(),
                content_type=content_type,
                filename=filename,
            )
            response = await self.req_in_session(
                RequestMethod.Post,
                self.v1urls.Attachments.format(page_id=page_id),
                headers={
                    "X-Atlassian-Token": "nocheck",
                },
                data=formdata,
            )
            return AttachmentCreateResponse.model_validate(response)

    async def download_file(
        self,
        url: str,
        file_id: UUID | str | None = None,
        media_type: str | None = None,
        file_name: str | None = None,
        parent_folder: Path | None = None,
        chunk_size: int = _4KB_In_Bytes,
    ) -> None:
        """Downloads the file at the given URL.
        The method tries to name the file following its file ID and media type.
        The file name can be specified directly and take precedence.
        The parent folder could also be specified.
        """
        if not file_name and not all([file_id, media_type]):
            raise ValueError("either file info or file name is required")

        if parent_folder:
            Path(parent_folder).mkdir(parents=True, exist_ok=True)

        async with ClientSession() as session:
            async with session.get(
                self.construct_url(url),
                auth=self.credentials,
            ) as resp:
                ext = guess_extension(media_type or "") or ""
                dst_suffix = file_name or f"{str(file_id)}{ext}"
                dst = Path(parent_folder or "", dst_suffix)
                async with aiofiles.open(dst, "wb+") as asyncfile:
                    async for chunk in resp.content.iter_chunked(chunk_size):
                        await asyncfile.write(chunk)

    async def download_attachments(
        self,
        attachments: list[Attachment],
        parent_folder: Path | None = None,
    ) -> None:
        """Downloads all files in the get attachments from page request."""
        if not attachments:
            return

        valid_attachments = filter(
            lambda att: att.uLinks.download, attachments
        )

        if parent_folder:
            Path(parent_folder).mkdir(parents=True, exist_ok=True)

        tasks = [
            self.download_file(
                str(attachment.uLinks.download),
                file_id=attachment.extensions.fileId,
                media_type=attachment.extensions.mediaType,
                parent_folder=parent_folder,
            )
            for attachment in valid_attachments
            if attachment.uLinks.download
        ]
        await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    async def download_attachment(self) -> None:
        """V1"""

    async def get_page(
        self,
        page_id: int | str,
        fmt: PageBodyFormat = PageBodyFormat.Storage,
    ) -> PageContent:
        """V2"""
        response = await self.req_in_session(
            RequestMethod.Get,
            self.v2urls.Page.format(page_id=str(page_id)),
            params={"body-format": fmt.value},
        )
        return PageContent.model_validate(response)

    async def get_pages(
        self,
        query_params: GetPageParams | dict[str, Any],
    ) -> PagesResponse:
        """V2"""
        if isinstance(query_params, dict):
            query_params = GetPageParams.model_validate(query_params)
        response = await self.req_in_session(
            RequestMethod.Get,
            self.v2urls.Pages,
            params=json.loads(
                query_params.model_dump_json(exclude_unset=True)
            ),
        )
        return PagesResponse.model_validate(response)

    async def create_page(self, page: PageCreate) -> PageContent:
        """V2"""
        response = await self.req_in_session(
            RequestMethod.Post,
            self.v2urls.Pages,
            json=page.model_dump(),
        )
        return PageContent.model_validate(response)

    async def update_page(
        self,
        page_id: int | str,
        page: PageUpdate,
    ) -> PageContent:
        """V2"""
        response = await self.req_in_session(
            RequestMethod.Put,
            self.v2urls.Page.format(page_id=page_id),
            json=page.model_dump(),
        )
        return PageContent.model_validate(response)

    async def get_ancestors(
        self,
        page_id: int | str,
    ) -> AncestorsResponse:
        response = await self.req_in_session(
            RequestMethod.Get,
            self.v2urls.Ancestors.format(page_id=str(page_id)),
        )
        return AncestorsResponse.model_validate(response)
