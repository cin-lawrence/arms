from enum import StrEnum
from typing import TypedDict

from .enums import MimeType


class PermissionsTypes(StrEnum):
    User = "user"
    Group = "group"
    Domain = "domain"
    Anyone = "anyone"


class PermissionsRoles(StrEnum):
    Owner = "owner"
    Organizer = "organizer"
    FileOrganizer = "fileOrganizer"
    Writer = "writer"
    Commenter = "commenter"
    Reader = "reader"


class PermissionsCreateRequest(TypedDict):
    type: PermissionsTypes
    role: PermissionsRoles
    emailAddress: str


class PermissionsCreateResponse(TypedDict):
    kind: str
    id: str
    type: PermissionsTypes
    role: PermissionsRoles


# https://developers.google.com/drive/api/reference/rest/v3/files#File
class File(TypedDict):
    kind: str
    id: str
    name: str
    size: str
    mimeType: MimeType
    md5Checksum: str

    createdTime: str


class FilesListResponse(TypedDict):
    nextPageToken: str
    kind: str
    incompleteSearch: bool
    files: list[File]
