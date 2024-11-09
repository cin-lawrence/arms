import asyncio
import logging
from pathlib import Path
from typing import TypedDict, cast
from uuid import UUID

from aiofiles.tempfile import TemporaryDirectory

from .api import ConfluenceToolkit
from .exc import ClientError
from .models.ancestor import Ancestor, AncestorType
from .models.errors import ErrorCode, ResponseError
from .models.page import (
    GetPageParams,
    PageBodyAtlas,
    PageBodyAtlasRef,
    PageBodyFormat,
    PageBodyStorageRef,
    PageCreate,
    PageStatus,
    PageStatusCreate,
    PageUpdate,
    PageUpdateVersion,
)
from .patcher import PatchMappingValue, patch
from .typedefs import PageId
from .utils import jsondumps


class AttachmentMapping(TypedDict):
    image_id: UUID
    collectionName: str


class TransferHelper:
    Comment = "created by Confluence Toolkit"

    def __init__(
        self,
        src_toolkit: ConfluenceToolkit,
        dst_toolkit: ConfluenceToolkit,
    ) -> None:
        self.st = src_toolkit
        self.dt = dst_toolkit

    async def _transfer_page_in_tempdir(
        self,
        src_page_id: PageId,
        space_id: str,
        parent_id: str,
        tempdir: Path,
        title: str | None = None,
    ) -> None:
        src_page = await self.st.get_page(
            src_page_id,
            fmt=PageBodyFormat.Atlas,
        )
        src_body: PageBodyAtlas = cast(PageBodyAtlas, src_page.body)
        src_content = src_body.atlas_doc_format.content
        src_att_response = await self.st.get_attachments_from_page(src_page_id)
        src_attachments = src_att_response.results

        if len(src_attachments):
            await self.st.download_attachments(
                src_attachments,
                parent_folder=tempdir,
            )

        title = title or f"{src_page.title} (cloned)"
        page_created = await self.dt.create_page(
            PageCreate(
                spaceId=space_id,
                status=PageStatusCreate.Current,
                title=title,
                parentId=parent_id,
                body=PageBodyStorageRef(
                    representation=PageBodyFormat.Storage,
                    value="",
                ),
            ),
        )

        new_content = src_content
        if len(src_attachments):
            tasks = []
            for att in src_attachments:
                task = self.dt.create_attachment(
                    str(page_created.id),
                    tempdir / att.extensions.filename,
                    comment=self.Comment,
                    content_type=att.extensions.suffix,
                    filename=att.title,
                )
                tasks.append(task)
            responses = await asyncio.gather(*tasks)
            mp_att: dict[UUID, PatchMappingValue] = {
                att_req.extensions.fileId: {
                    "image_id": str(att_resp.first.extensions.fileId),
                    "collection": att_resp.first.extensions.collectionName,
                }
                for att_req, att_resp in zip(
                    src_attachments,
                    responses,
                    strict=False,
                )
                if att_req.extensions and att_resp.first
            }

            new_content = {}
            patch(src_content, new_content, mp_att)

        await self.dt.update_page(
            page_created.id,
            PageUpdate(
                id=str(page_created.id),
                status=PageStatus.Current,
                title=page_created.title,
                body=PageBodyAtlasRef.model_validate(
                    {
                        "value": jsondumps(new_content),
                    },
                ),
                version=PageUpdateVersion.model_validate(
                    {
                        "number": page_created.version.number + 1,
                        "message": self.Comment,
                    },
                ),
            ),
        )

    async def transfer_ancestors(
        self,
        space_id: str,
        parent_id: str,
        ancestors: list[Ancestor],
    ) -> str:
        current_parent_id: str = parent_id
        for ancestor in ancestors:
            logging.warning(
                "Creating %s in %s",
                ancestor.id,
                current_parent_id,
            )
            if ancestor.type != AncestorType.Page:
                continue
            src_page = await self.st.get_page(ancestor.id)
            try:
                dst_page = await self.dt.create_page(
                    PageCreate(
                        spaceId=space_id,
                        status=PageStatusCreate.Current,
                        title=src_page.title,
                        parentId=current_parent_id,
                        body=PageBodyStorageRef(value=""),
                    ),
                )
            except ClientError as err:
                if not (
                    isinstance(err.payload, ResponseError)
                    and err.payload.code == ErrorCode.InvalidRequestParameter
                    and "already exists" in err.payload.title
                ):
                    raise
                dst_page = None

            if dst_page is None:
                response = await self.dt.get_pages(
                    GetPageParams(title=src_page.title),
                )
                dst_page = response.first

            if dst_page is None:
                raise RuntimeError(
                    "Couldn't either create or get page {src_page.title}",
                )

            current_parent_id = str(dst_page.id)
        return current_parent_id

    async def transfer_page(
        self,
        src_page_id: PageId,
        space_id: str,
        parent_id: str,
        title: str | None = None,
        *,
        transfer_ancestors: bool = False,
    ) -> None:
        if transfer_ancestors:
            resp = await self.st.get_ancestors(src_page_id)
            ancestors = resp.results[1:]
            parent_id = await self.transfer_ancestors(
                space_id,
                parent_id,
                ancestors,
            )

        async with TemporaryDirectory(prefix="arms-confluence") as tempdir:
            return await self._transfer_page_in_tempdir(
                src_page_id,
                space_id,
                parent_id,
                Path(tempdir),
                title=title,
            )
