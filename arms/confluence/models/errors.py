from enum import StrEnum

from pydantic import BaseModel, ValidationError


class ErrorCode(StrEnum):
    InvalidRequestParameter = "INVALID_REQUEST_PARAMETER"


class Error(BaseModel):
    status: int
    code: ErrorCode
    title: str
    detail: str | None = None


class ErrorResponse(BaseModel):
    errors: list[Error]

    @classmethod
    def try_validate_json(cls, text: str) -> "ErrorResponse" | str:
        try:
            return cls.model_validate_json(text)
        except ValidationError:
            return text
