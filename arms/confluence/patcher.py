import logging
from collections.abc import Callable
from copy import deepcopy
from typing import (
    Annotated,
    Any,
    Final,
    TypedDict,
    TypeVar,
)
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator

type Attrs = dict[str, UUID | int | str]
logger = logging.getLogger(__name__)


def ensure_array(value: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return value or []


class Slice(BaseModel):
    type: str
    text: str | None = None
    attrs: Attrs | None = None
    content: Annotated[list["Slice"], BeforeValidator(ensure_array)] = []


class MediaSingleSlice(Slice):
    MIN_CONTENT_LENGTH: Final[int] = 2
    type: str = "mediaSingle"
    attrs: Attrs = {"layout": "center"}

    @property
    def content_attrs(self) -> Attrs | None:
        first_slice = next(iter(self.content), None)
        if not first_slice:
            return {}
        return first_slice.attrs

    @property
    def caption(self) -> str | None:
        if len(self.content) < self.MIN_CONTENT_LENGTH:
            return None
        second_slice: Slice = self.content[1]
        if len(second_slice.content) == 0:
            return None
        return second_slice.content[0].text


class Image(BaseModel):
    id: UUID
    width: int | None = None
    height: int | None = None
    caption: str | None = None
    collection: Annotated[
        str,
        Field(description="should starts with `contentId-`"),
    ]
    type: str


type TransformMapper = dict[str, Callable[[Any], Any]]
DictOrList = TypeVar("DictOrList", dict[str, Any], list[Any])


def alter_media_single(
    mss: MediaSingleSlice,
    image_id: UUID,
    collection: str,
) -> dict[str, Any]:
    """Alter the identity fields of a media payload.

    Explicitly specify width and height would inflate the space occupied
    by the image unexpectedly, hence they are commented and left as options.
    """
    content_attrs = mss.content_attrs or {}
    image = Image.model_validate(
        {
            "id": image_id,
            "caption": mss.caption,
            "collection": collection,
            "type": content_attrs.get("type", ""),
        },
    )
    slice_media = Slice.model_validate(
        {
            "type": "media",
            "attrs": image.model_dump(exclude={"caption"}, exclude_unset=True),
        },
    )
    slice_caption = Slice.model_validate(
        {
            "type": "caption",
            "content": [
                Slice(text=image.caption, type="text"),
            ],
        },
    )
    return MediaSingleSlice.model_validate(
        {"content": [slice_media, slice_caption]},
    ).model_dump(exclude_unset=True)


class PatchMappingValue(TypedDict):
    image_id: str
    collection: str


def patch(
    obj: DictOrList,
    patchobj: DictOrList,
    mp_att: dict[UUID, PatchMappingValue],
    level: int = 0,
    path: str = "#root",
) -> DictOrList:
    if not isinstance(obj, list | dict):
        logger.debug("[Level@%d | %s]: %s", level, path, obj)
        return None

    if isinstance(obj, list):
        mp_idx_child = dict(enumerate(obj))
        for key in mp_idx_child:
            try:
                patchobj[key]
            except (IndexError, KeyError):
                patchobj[key] = deepcopy(obj[key])

            patch(
                obj[key],
                patchobj[key],
                mp_att,
                level=level + 1,
                path=f"{path} > {key}",
            )
    elif isinstance(obj, dict):
        obj_dict = obj
        for key in obj_dict:
            try:
                patchobj[key]
            except (IndexError, KeyError):
                patchobj[key] = deepcopy(obj[key])

            if obj_dict.get("type") == "mediaSingle":
                media_slice = MediaSingleSlice.model_validate(obj)
                original_image_id = (media_slice.content_attrs or {}).get("id")
                if not isinstance(original_image_id, str):
                    continue
                original_image_uuid = UUID(original_image_id)
                if original_image_uuid in mp_att:
                    value = mp_att[original_image_uuid]
                    altered = alter_media_single(
                        media_slice,
                        UUID(value["image_id"]),
                        value["collection"],
                    )
                    patchobj["content"] = altered["content"]
                continue

            patch(
                obj[key],
                patchobj[key],
                mp_att,
                level=level + 1,
                path=f"{path} > {key}",
            )
    return patchobj
