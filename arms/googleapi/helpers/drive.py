from functools import cached_property

from googleapiclient.discovery import Resource

from ..payloads.drive import (
    PermissionsCreateRequest,
    PermissionsCreateResponse,
)
from .factory import GoogleServiceFactory, default_google_service_factory


class DriveHelper:
    # https://github.com/googleworkspace/python-samples/tree/main/drive/snippets/drive-v3
    def __init__(self, factory: GoogleServiceFactory):
        self.factory = factory

    @cached_property
    def service(self) -> Resource:
        return self.factory.get_drive_service()

    def grant_permissions(
        self,
        res_id: str,
        perm_obj: PermissionsCreateRequest,
    ) -> PermissionsCreateResponse:
        return (
            self.service.permissions()
            .create(
                fileId=res_id,
                body=perm_obj,
            )
            .execute()
        )

    def delete_file(self, file_id: str) -> str:
        # on success, it returns an empty string
        return self.service.files().delete(fileId=file_id).execute()


default_drive_helper = DriveHelper(default_google_service_factory)
