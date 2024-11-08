from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ..helpers.sheets import SpreadsheetsHelper, default_sheets_helper

if TYPE_CHECKING:
    from googleapiclient._apis.sheets.v4.schemas import (
        BatchUpdateSpreadsheetResponse,
        ClearValuesResponse,
        UpdateValuesResponse,
    )

    from ..types import SheetsData

_DefaultA1Notation = "A1"
_DefaultA1NotationAll = "A1:ZZ"


class Sheet:
    def __init__(
        self,
        name: str,
        book: Book,
        service: GoogleSheet,
    ) -> None:
        self.name = name
        self.book = book
        self.service = service

    def ownrange(self, range_: str) -> str:
        if self.name:
            return f"{self.name}!{range_}"
        return range_

    def write(
        self,
        data: SheetsData,
        range_: str = _DefaultA1Notation,
        option: Literal[
            "INPUT_VALUE_OPTION_UNSPECIFIED",
            "RAW",
            "USER_ENTERED",
        ] = "USER_ENTERED",
    ) -> UpdateValuesResponse:
        return self.service.update_values(
            self.book.id_,
            data,
            self.ownrange(range_),
            option=option,
        )

    def clear_all_values(
        self,
        range_: str = _DefaultA1NotationAll,
    ) -> ClearValuesResponse:
        return self.book.clear_values(
            range_,
        )


class Book:
    def __init__(
        self,
        id_: str,
        service: GoogleSheet,
    ) -> None:
        self.id_ = id_
        self.service = service

    def sheet(self, sheet_name: str) -> Sheet:
        return Sheet(sheet_name, self, self.service)

    def write_to_sheet(
        self,
        sheet_name: str,
        data: SheetsData,
        range_: str = _DefaultA1Notation,
        option: Literal[
            "INPUT_VALUE_OPTION_UNSPECIFIED",
            "RAW",
            "USER_ENTERED",
        ] = "USER_ENTERED",
    ) -> UpdateValuesResponse:
        """Write data into sheet.

        `range` should be in A1 notation.
        Specifying A1 would automatically fit the corresponding range of data.
        """
        sheet = self.sheet(sheet_name)
        return sheet.write(data, range_, option)

    def write(
        self,
        data: SheetsData,
        range_: str = _DefaultA1Notation,
        option: Literal[
            "INPUT_VALUE_OPTION_UNSPECIFIED",
            "RAW",
            "USER_ENTERED",
        ] = "USER_ENTERED",
    ) -> UpdateValuesResponse:
        return self.service.update_values(
            self.id_,
            data,
            range_,
            option=option,
        )

    def update_currency_format(
        self,
        range_: str,
    ) -> BatchUpdateSpreadsheetResponse:
        return self.service.update_currency_format(
            self.id_,
            range_,
        )

    def clear_values(
        self,
        range_: str = _DefaultA1NotationAll,
    ) -> ClearValuesResponse:
        return self.service.clear_values(
            self.id_,
            range_=range_,
        )


class GoogleSheet:
    def __init__(self, helper: SpreadsheetsHelper) -> None:
        self.helper = helper

    def book(self, book_id: str | None = None) -> Book:
        if book_id is None:
            response = self.helper.create_sheet("Untitled synchron sheet")
            book_id = response["spreadsheetId"]
        return Book(book_id, self)

    def update_values(
        self,
        book_id: str,
        data: SheetsData,
        range_: str = _DefaultA1Notation,
        option: Literal[
            "INPUT_VALUE_OPTION_UNSPECIFIED",
            "RAW",
            "USER_ENTERED",
        ] = "USER_ENTERED",
    ) -> UpdateValuesResponse:
        return self.helper.update_values_in_range(
            book_id,
            range_,
            body={
                "values": data,
            },
            value_input_option=option,
        )

    def update_currency_format(
        self,
        book_id: str,
        range_: str,
    ) -> BatchUpdateSpreadsheetResponse:
        return self.helper.update_currency_format(
            book_id,
            range_,
        )

    def clear_values(
        self,
        book_id: str,
        range_: str = _DefaultA1NotationAll,
    ) -> ClearValuesResponse:
        return self.helper.clear_values(
            book_id,
            range_=range_,
        )


googlesheet = GoogleSheet(default_sheets_helper)
