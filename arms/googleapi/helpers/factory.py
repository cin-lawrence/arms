from __future__ import annotations

import os
from functools import cached_property
from typing import TYPE_CHECKING, ClassVar

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

if TYPE_CHECKING:
    from googleapiclient._apis.drive.v3.resources import DriveResource
    from googleapiclient._apis.sheets.v4.resources import SheetsResource


class GoogleServiceFactory:
    DefaultEnvVar: str = "GOOGLEAPI_SERVICE_ACCOUNT_PATH"
    mp_perm_scopes: ClassVar[dict[str, list[str]]] = {
        "drive": [
            "https://www.googleapis.com/auth/drive",
        ],
        "spreadsheets": [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    }

    def __init__(self, service_account_path: str | None = None) -> None:
        self._service_account_path = (
            service_account_path or self.default_service_account_path
        )
        self._permissions = self.mp_perm_scopes.keys()

    @property
    def default_service_account_path(self) -> str:
        return os.getenv(self.DefaultEnvVar, "")

    @property
    def service_account_path(self) -> str:
        return self._service_account_path or self.default_service_account_path

    def get_credentials(self, scopes: list[str]) -> Credentials:
        if not self.service_account_path:
            raise RuntimeError(
                "GoogleAPI service account path not set, "
                f"set it in env var {self.DefaultEnvVar} "
                "or explicitly pass it in the constructor.",
            )
        return Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
            self.service_account_path,
            scopes=scopes,
        )

    def get_scopes(self, permission: str) -> list[str]:
        if permission not in self.mp_perm_scopes:
            raise ValueError(
                f"Unknown permission: {permission}, "
                f"must be one of {', '.join(self._permissions)}",
            )
        return self.mp_perm_scopes[permission]

    @cached_property
    def spreadsheets(self) -> SheetsResource.SpreadsheetsResource:
        credentials = self.get_credentials(self.get_scopes("spreadsheets"))
        svc: SheetsResource = build("sheets", "v4", credentials=credentials)
        return svc.spreadsheets()

    @cached_property
    def drive(self) -> DriveResource:
        credentials = self.get_credentials(self.get_scopes("drive"))
        return build("drive", "v3", credentials=credentials)


default_google_service_factory = GoogleServiceFactory()
