from pydantic_settings import BaseSettings, SettingsConfigDict


class V1Endpoints(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="v1endpoints",
    )

    Page: str = "/rest/api/content/{page_id}"
    Spaces: str = "/rest/api/space"
    Attachments: str = "/rest/api/content/{page_id}/child/attachment"
    Download: str = (
        "/download/attachments/{filename}"
        "?version={version}"
        "&modificationDate={modification_date}"
        "&cacheVersion=1"
        "&api=v2"
    )


class V2Endpoints(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_prefix="v2endpoints",
    )

    Page: str = "/api/v2/pages/{page_id}"
    Ancestors: str = "/api/v2/pages/{page_id}/ancestors"
    Pages: str = "/api/v2/pages"
    Spaces: str = "/api/v2/spaces"
