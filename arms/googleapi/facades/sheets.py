from __future__ import annotations
from typing import Literal, TYPE_CHECKING

from googleapiclient._apis.sheets.v4.schemas import (
    BatchGetValuesResponse,
    BatchUpdateSpreadsheetResponse,
    ClearValuesResponse,
    Spreadsheet,
    SpreadsheetProperties,
    UpdateValuesResponse,
    ValueRange,
    GridRange,
)
from ..helpers.sheets import SpreadsheetsHelper, default_sheets_helper
from ..types import SheetsData

_DefaultA1Notation = "A1"
_DefaultA1NotationAll = "A1:ZZ"


class Sheet:
    def __init__(
        self,
        name: str,
        book: "Book",
        service: "GoogleSheet",
    ):
        self.name = name
        self.book = book
        self.service = service

    def ownrange(self, range: str) -> str:
        if self.name:
            return f"{self.name}!{range}"
        return range

    def write(
        self,
        data: SheetsData,
        range: str = _DefaultA1Notation,
        option: Literal[
            'INPUT_VALUE_OPTION_UNSPECIFIED', 'RAW', 'USER_ENTERED'
        ] = 'USER_ENTERED',
    ) -> UpdateValuesResponse:
        return self.service.update_values(
            self.book.id,
            data,
            self.ownrange(range),
            option=option,
        )

    def clear_all_values(
        self,
        range: str = _DefaultA1NotationAll,
    ) -> ClearValuesResponse:
        return self.book.clear_values(
            range,
        )


class Book:
    def __init__(
        self,
        id: str,
        service: "GoogleSheet",
    ):
        self.id = id
        self.service = service
        return

    def sheet(self, sheet_name: str) -> Sheet:
        return Sheet(sheet_name, self, self.service)

    def write_to_sheet(
        self,
        sheet_name: str,
        data: SheetsData,
        range: str = _DefaultA1Notation,
        option: Literal[
            'INPUT_VALUE_OPTION_UNSPECIFIED', 'RAW', 'USER_ENTERED'
        ] = 'USER_ENTERED',
    ) -> UpdateValuesResponse:
        """
        Range should be in A1 notation.
        Specifying A1 would automatically fit the corresponding range of data.
        """
        sheet = self.sheet(sheet_name)
        return sheet.write(data, range, option)

    def write(
        self,
        data: SheetsData,
        range: str = _DefaultA1Notation,
        option: Literal[
            'INPUT_VALUE_OPTION_UNSPECIFIED', 'RAW', 'USER_ENTERED'
        ] = 'USER_ENTERED',
    ) -> UpdateValuesResponse:
        return self.service.update_values(
            self.id,
            data,
            range,
            option=option,
        )

    def update_currency_format(
        self,
        range: str,
    ) -> BatchUpdateSpreadsheetResponse:
        return self.service.update_currency_format(
            self.id,
            range,
        )

    def clear_values(
        self,
        range: str = _DefaultA1NotationAll,
    ) -> ClearValuesResponse:
        return self.service.clear_values(
            self.id,
            range=range,
        )


class GoogleSheet:
    def __init__(self, helper: SpreadsheetsHelper):
        self.helper = helper

    def book(self, book_id: str | None = None) -> Book:
        if not book_id:
            response = self.helper.create_sheet("Untitled synchron sheet")
            book_id = response["spreadsheetId"]
        return Book(book_id, self)

    def update_values(
        self,
        book_id: str,
        data: SheetsData,
        range: str = _DefaultA1Notation,
        option: Literal[
            'INPUT_VALUE_OPTION_UNSPECIFIED', 'RAW', 'USER_ENTERED'
        ] = 'USER_ENTERED',
    ) -> UpdateValuesResponse:
        return self.helper.update_values_in_range(
            book_id,
            range,
            body={
                "values": data,
            },
            value_input_option=option,
        )

    def update_currency_format(
        self,
        book_id: str,
        range: str,
    ) -> BatchUpdateSpreadsheetResponse:
        return self.helper.update_currency_format(
            book_id,
            range,
        )

    def clear_values(
        self,
        book_id: str,
        range: str = _DefaultA1NotationAll,
    ) -> ClearValuesResponse:
        return self.helper.clear_values(
            book_id,
            range=range,
        )


googlesheet = GoogleSheet(default_sheets_helper)
