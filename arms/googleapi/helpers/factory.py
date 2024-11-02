from __future__ import annotations

import os
from functools import lru_cache

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient._apis.sheets.v4.resources import SheetsResource
from googleapiclient._apis.drive.v3.resources import DriveResource


class GoogleServiceFactory:
    DefaultEnvVar: str = "GOOGLEAPI_SERVICE_ACCOUNT_PATH"
    mp_perm_scopes: dict[str, list[str]] = {
        "sheets_drive": [
            "https://www.googleapis.com/auth/drive",
        ],
        "sheets_only": [
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    }

    def __init__(self, service_account_path: str | None = None):
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
                "or explicitly pass it in the constructor."
            )
        return Credentials.from_service_account_file(  # type: ignore[no-untyped-call] # noqa
            self.service_account_path,
            scopes=scopes,
        )

    def get_scopes(self, permission: str) -> list[str]:
        if permission not in self.mp_perm_scopes:
            raise ValueError(
                "Unknown permission: %s, must be one of %s"
                % (
                    permission,
                    ", ".join(self._permissions),
                )
            )
        return self.mp_perm_scopes[permission]

    @lru_cache
    def get_spreadsheet_service(self) -> SheetsResource.SpreadsheetsResource:
        credentials = self.get_credentials(self.get_scopes("sheets_drive"))
        svc: "SheetsResource" = build("sheets", "v4", credentials=credentials)
        return svc.spreadsheets()

    @lru_cache
    def get_drive_service(self) -> DriveResource:
        credentials = self.get_credentials(self.get_scopes("sheets_drive"))
        return build("drive", "v3", credentials=credentials)


default_google_service_factory = GoogleServiceFactory()
