from pydantic import BaseModel
from .base import BaseUnit


class ProfilePicture(BaseModel):
    path: str
    width: int
    height: int
    isDefault: bool


class UserExpandable(BaseModel):
    operations: str
    personalSpace: str


class User(BaseUnit[UserExpandable]):
    type: str
    accountId: str
    accountType: str
    email: str
    publicName: str
    profilePicture: ProfilePicture
    displayName: str
    isExternalCollaborator: bool
