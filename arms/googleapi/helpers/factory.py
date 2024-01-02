import os
from functools import lru_cache

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import Resource, build


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

    mp_svc_buildparams: dict[str, tuple[str, str]] = {
        "sheets": ("sheets", "v4"),
        "drive": ("drive", "v3"),
    }

    def __init__(self, service_account_path: str | None = None):
        self._service_account_path = (
            service_account_path or self.default_service_account_path
        )
        self._permissions = self.mp_perm_scopes.keys()
        self._services = self.mp_svc_buildparams.keys()

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
        return Credentials.from_service_account_file(
            self.service_account_path,
            scopes=scopes,
        )

    @lru_cache
    def get_service(self, service_name: str, permission: str) -> Resource:
        """Creates the service in the most intuitive and simplest way.

        >>> get_service('sheets', 'sheets_drive')
        """
        if permission not in self.mp_perm_scopes:
            raise ValueError(
                f"unknown permission: {permission}, "
                f"must be one of {self._permissions}"
            )

        if service_name not in self.mp_svc_buildparams:
            raise ValueError(
                f"unknown service: {service_name}, "
                f"must be one of {self._services}"
            )

        credentials = self.get_credentials(self.mp_perm_scopes[permission])
        svc, version = self.mp_svc_buildparams[service_name]
        return build(svc, version, credentials=credentials)

    def get_sheet_service(self) -> Resource:
        svc = self.get_service("sheets", "sheets_drive")
        return svc.spreadsheets()

    def get_drive_service(self) -> Resource:
        return self.get_service("drive", "sheets_drive")


default_google_service_factory = GoogleServiceFactory()
