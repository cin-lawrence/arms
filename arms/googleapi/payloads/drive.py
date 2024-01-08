from enum import StrEnum
from typing import TypedDict


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
