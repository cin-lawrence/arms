from __future__ import annotations

import logging
from functools import cached_property
from io import BytesIO
from mimetypes import guess_type
from pathlib import Path

from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient._apis.drive.v3 import DriveResource
from googleapiclient._apis.drive.v3.schemas import File, Permission, FileList

from .factory import GoogleServiceFactory, default_google_service_factory


class DriveHelper:
    # https://github.com/googleworkspace/python-samples/tree/main/drive/snippets/drive-v3
    def __init__(self, factory: GoogleServiceFactory):
        self.factory = factory
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    @cached_property
    def service(self) -> DriveResource:
        return self.factory.get_drive_service()

    def grant_permissions(
        self,
        file_id: str,
        perm_obj: Permission,
    ) -> Permission:
        return (
            self.service.permissions()
            .create(
                fileId=file_id,
                body=perm_obj,
            )
            .execute()
        )

    def delete_file(self, file_id: str) -> str:
        # on success, it returns an empty string
        return self.service.files().delete(fileId=file_id).execute()

    def get_metadata(self, file_id: str, fields: str = "*") -> File:
        return (
            self.service.files().get(fileId=file_id, fields=fields).execute()
        )

    def list_folder(
        self,
        folder_id: str,
        fields: str,
        pageSize: int = 100,
    ) -> FileList:
        """
        https://developers.google.com/drive/api/reference/rest/v3/files/list
        """
        return (
            self.service.files()
            .list(
                pageSize=pageSize,
                q=f"'{folder_id}' in parents",
                fields=fields,
            )
            .execute()
        )

    @staticmethod
    def to_percent(progress: float) -> str:
        return f"{round(progress * 100, 2)}%"

    def download_file(
        self,
        file_id: str,
        buffer: BytesIO,
    ) -> None:
        request = self.service.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(buffer, request)
        done: bool = False
        while not done:
            status, done = downloader.next_chunk()
            self.logger.debug(
                f"Downloading... ({self.to_percent(status.progress())})"
            )

    def upload_file_to_folder(
        self,
        filepath: Path,
        folder_id: str,
        resumable: bool = False,
    ) -> File:
        metadata: File = {
            "name": filepath.name,
            "parents": [folder_id],
        }
        mimetype, _ = guess_type(str(filepath))
        media = MediaFileUpload(
            str(filepath),
            mimetype=mimetype,
            resumable=resumable,
        )
        return (
            self.service.files()
            .create(
                body=metadata,
                media_body=media,
            )
            .execute()
        )


default_drive_helper = DriveHelper(default_google_service_factory)
