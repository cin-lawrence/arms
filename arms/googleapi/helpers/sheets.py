import re
import string
from functools import cached_property
from typing import Any, Literal, cast, TYPE_CHECKING

from googleapiclient.discovery import Resource
from googleapiclient._apis.sheets.v4.schemas import (
    BatchGetValuesResponse,
    BatchUpdateSpreadsheetResponse,
    ClearValuesResponse,
    Spreadsheet,
    SpreadsheetProperties,
    UpdateValuesResponse,
    ValueRange,
    GridRange,
    Sheet,
)
from .factory import GoogleServiceFactory, default_google_service_factory

if TYPE_CHECKING:
    from googleapiclient._apis.sheets.v4.resources import SheetsResource


_PatternA1Notation = re.compile(r"^(?:(.+)!)*(\D+)(\d*):(\D+)(\d*)$")
_DefaultA1NotationAll = "A1:ZZ"


def col2num(col: str) -> int:
    num = 0
    for c in col:
        if c in string.ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord("A")) + 1
    return num


class SpreadsheetsHelper:
    # https://github.com/googleworkspace/python-samples/tree/main/sheets/snippets
    def __init__(self, factory: GoogleServiceFactory):
        self.factory = factory

    @cached_property
    def service(self) -> 'SheetsResource.SpreadsheetsResource':
        return self.factory.get_spreadsheet_service()

    def _a1notation_to_gridrange(
        self,
        spreadsheet_id: str,
        a1: str,
        sheet_title: str = "",
        sheet_index: int | None = None,
    ) -> GridRange:
        # https://gist.github.com/tanaikech/95c7cd650837f33a564babcaf013cae0
        match = _PatternA1Notation.match(a1)
        if not match:
            raise ValueError(f"invalid a1 notation: {a1}")
        title, scol, srow, ecol, erow = match.groups()

        if not scol:
            raise ValueError(f"start column required in {a1}")

        sheet_title = title or sheet_title
        sheet_id = 0

        spreadsheet: Spreadsheet = (
            self.service.get(spreadsheetId=spreadsheet_id).execute()
        )
        if sheet_title:
            sheets = filter(
                lambda sh: (
                    sh.get("properties", {}).get("title", "") == sheet_title
                ),
                spreadsheet.get("sheets", []),
            )
            first_sheet = next(iter(sheets), None)
            if not first_sheet:
                raise ValueError(f"sheet titled {sheet_title} not found")
            sheet_id = first_sheet["properties"]["sheetId"]
        elif sheet_index:
            sheet: Sheet = spreadsheet.get("sheets", [])[sheet_index]
            sheet_id = sheet["properties"]["sheetId"]

        gridrange = {
            "sheetId": sheet_id,
            "startRowIndex": int(srow) - 1 if srow else None,
            "endRowIndex": int(erow) - 1 if erow else None,
            "startColumnIndex": col2num(scol) - 1,
            "endColumnIndex": col2num(ecol) if ecol else None,
        }

        return cast(
            GridRange, {k: v for k, v in gridrange.items() if v is not None}
        )

    def create_sheet(
        self,
        title: str,
        config: Spreadsheet | None = None,
    ) -> Spreadsheet:
        config = config or {}
        properties: SpreadsheetProperties = {
            **config.get("properties", {}),
            "title": title,
        }
        spreadsheet_config: Spreadsheet = {
            **(config or {}),
            "properties": properties,
        }
        return self.service.create(
            body=spreadsheet_config,
            fields="spreadsheetId",
        ).execute()

    def get_values_in_ranges(
        self,
        sheet_id: str,
        ranges: list[str],
    ) -> BatchGetValuesResponse:
        # https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/batchGet
        return (
            self.service.values()
            .batchGet(
                spreadsheetId=sheet_id,
                ranges=ranges,
            )
            .execute()
        )

    def update_values_in_range(
        self,
        sheet_id: str,
        range: str,
        body: ValueRange,
        value_input_option: Literal[
            'INPUT_VALUE_OPTION_UNSPECIFIED', 'RAW', 'USER_ENTERED'
        ] = 'USER_ENTERED',
    ) -> UpdateValuesResponse:
        return (
            self.service.values()
            .update(
                spreadsheetId=sheet_id,
                range=range,  # the A1 notation
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )

    def update_currency_format(
        self,
        sheet_id: str,
        range: str | GridRange,
    ) -> BatchUpdateSpreadsheetResponse:
        if isinstance(range, str):
            range = self._a1notation_to_gridrange(sheet_id, range)

        return self.service.batchUpdate(
            spreadsheetId=sheet_id,
            body={
                "requests": [
                    {
                        "repeatCell": {
                            "range": range,
                            "cell": {
                                "userEnteredFormat": {
                                    "numberFormat": {
                                        "type": "CURRENCY",
                                        "pattern": "#,##0.00",
                                    }
                                }
                            },
                            "fields": "userEnteredFormat.numberFormat",
                        }
                    }
                ]
            },
        ).execute()

    def clear_values(
        self,
        sheet_id: str,
        range: str = _DefaultA1NotationAll,
    ) -> ClearValuesResponse:
        return (
            self.service.values()
            .clear(
                spreadsheetId=sheet_id,
                range=range,
                body={},
            )
            .execute()
        )


default_sheets_helper = SpreadsheetsHelper(default_google_service_factory)
