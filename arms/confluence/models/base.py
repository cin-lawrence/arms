from pathlib import Path
from typing import Annotated, Any, Callable, Generic, TypeAlias, TypeVar

from pydantic import AnyHttpUrl, BaseModel, Field, model_serializer

Link: TypeAlias = AnyHttpUrl | Path | str
ExpandableType = TypeVar("ExpandableType", bound=BaseModel)
ResourceType = TypeVar("ResourceType", bound=BaseModel)


class DumpConfig(BaseModel):
    by_alias: bool | None = None
    exclude_unset: bool | None = None
    exclude_defaults: bool | None = None
    exclude_none: bool | None = None


class DumpByConfigMixin(BaseModel):
    _DumpConfig: DumpConfig = DumpConfig.model_validate({})

    def _gen_key(self, key: str) -> str:
        if self._DumpConfig.by_alias:
            return self.model_fields[key].alias or key
        return key

    def _is_value_qualified(self, key: str, value: Any) -> bool:
        qual: bool = True
        if self._DumpConfig.exclude_none:
            qual = qual and (value is not None)
        if self._DumpConfig.exclude_defaults:
            qual = qual and (value != self.model_fields[key].default)
        if self._DumpConfig.exclude_unset:
            qual = qual and (key in self.model_fields_set)
        return qual

    def _dump_by_config(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            self._gen_key(key): value
            for key, value in data.items()
            if self._is_value_qualified(key, value)
        }

    @model_serializer(mode="wrap")
    def serialize(
        self,
        handler: Callable[[Any], dict[str, Any]],
    ) -> dict[str, Any]:
        return self._dump_by_config(handler(self))  # type: ignore[arg-type,call-arg]


class _ULinks(DumpByConfigMixin, BaseModel):
    _DumpConfig = DumpConfig(exclude_none=True)

    self: Link | None = None
    base: Link | None = None
    content: Link | None = None
    context: Link | None = None
    download: Link | None = None
    next: Link | None = None
    tinyui: Link | None = None
    editui: Link | None = None
    webui: Link | None = None


UExpandable = Annotated[ExpandableType, Field(alias="_expandable")]
ULinks = Annotated[_ULinks, Field(alias="_links")]

"""Specifying uLinks in BaseUnit would fail if annotating like below:
    ```
        uLinks: ULinks | None = None
    ```
    however, using OptionalULinks a.k.a moving None inside the Annotated worked
"""
OptionalULinks = Annotated[_ULinks | None, Field(alias="_links")]


class _BaseUnitPartial(DumpByConfigMixin, BaseModel, Generic[ExpandableType]):
    _DumpConfig = DumpConfig(by_alias=True)

    uExpandable: Annotated[
        ExpandableType | None,
        Field(alias="_expandable"),
    ] = None
    uLinks: OptionalULinks = None


class BaseUnit(_BaseUnitPartial[ExpandableType], Generic[ExpandableType]):
    uExpandable: Annotated[ExpandableType, Field(alias="_expandable")]


class ResourceCreateResponse(
    DumpByConfigMixin,
    BaseModel,
    Generic[ResourceType],
):
    _DumpConfig = DumpConfig(by_alias=True)

    results: Annotated[
        list[ResourceType],
        Field(description="often has only 1"),
    ] = []
    size: int | None = None
    uLinks: ULinks | None = None

    @property
    def first(self) -> ResourceType | None:
        return next(iter(self.results), None)


class ManyResourceResponse(
    ResourceCreateResponse[ResourceType],
    Generic[ResourceType],
):
    start: int | None = None
    limit: int | None = None
