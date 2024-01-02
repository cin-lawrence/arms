from enum import StrEnum
from typing import Annotated, Any, NotRequired, TypedDict


class ValueInputOption(StrEnum):
    Raw = "RAW"
    UserEntered = "USER_ENTERED"


class Dimension(StrEnum):
    DimensionUnspecified = "DIMENSION_UNSPECIFIED"
    Rows = "ROWS"
    Columns = "COLUMNS"


class ValueRange(TypedDict):
    range: NotRequired[str]
    majorDimension: NotRequired[Dimension]
    values: list[list[str]]


class CreateResponse(TypedDict):
    spreadsheetId: str


class ValuesBatchGetResponse(TypedDict):
    spreadsheetId: str
    valueRanges: list[ValueRange]


class ValuesUpdateResponse(TypedDict):
    spreadsheetId: str
    updatedRange: Annotated[str, "Sheet1!A1:D5 (A1 notation)"]
    updatedRows: int
    updatedColumns: int
    updatedCells: int


class BatchUpdateResponse(TypedDict):
    spreadsheetId: str
    replies: list[dict[str, Any]]


class GridRange(TypedDict):
    # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#GridRange
    sheetId: int
    startRowIndex: NotRequired[int]
    endRowIndex: NotRequired[int]
    startColumnIndex: NotRequired[int]
    endColumnIndex: NotRequired[int]


class ValuesClearResponse(TypedDict):
    spreadsheetId: str
    clearedRange: str
