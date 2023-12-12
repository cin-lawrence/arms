from datetime import datetime

from .base import BaseModel, BaseUnit, Link, ManyResourceResponse


class SpaceExpandable(BaseModel):
    settings: Link
    metadata: str
    operations: str
    lookAndFeel: Link
    identifiers: str
    permissions: str
    icon: str
    description: str
    theme: Link
    history: str
    homepage: Link


class Space(BaseUnit[SpaceExpandable]):
    id: int
    key: str
    name: str
    type: str
    status: str


class SpaceResponseV2(BaseModel):
    name: str
    key: str
    id: int
    type: str
    homepageId: int
    icon: str | None = None
    description: str | None = None
    status: str
    createdAt: datetime


class SpacesResponse(ManyResourceResponse[Space]):
    pass
