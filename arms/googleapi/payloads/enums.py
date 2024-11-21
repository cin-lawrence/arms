from enum import StrEnum


class MimeType(StrEnum):
    GoogleAppsFolder = "application/vnd.google-apps.folder"


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
