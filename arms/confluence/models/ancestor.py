from enum import StrEnum, auto
from typing import Literal

from .base import BaseModel, ManyResourceResponse


class AncestorType(StrEnum):
    Page = auto()
    Space = auto()


class Ancestor(BaseModel):
    id: str
    type: Literal["page", "space"]


class AncestorsResponse(ManyResourceResponse[Ancestor]):
    pass
