import hashlib
import json
import logging
import os
import shutil
from collections.abc import Generator, Sequence
from io import BytesIO
from pathlib import Path
from typing import Annotated, Any, Literal, NotRequired, TypedDict, cast

from googleapiclient.errors import HttpError

from ..helpers.drive import DriveHelper
from ..payloads.drive import (
    File,
    PermissionsCreateRequest,
    PermissionsCreateResponse,
)
from ..payloads.enums import MimeType


def md5(filepath: Path) -> str:
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as readfile:
        for chunk in iter(lambda: readfile.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class OperationalError(Exception):
    ...


class DiffObj(TypedDict):
    side: Literal["local", "remote", "both"]
    path: str
    type: NotRequired[Literal["file", "folder"]]
    comment: NotRequired[str]


class DownloadOptions(TypedDict):
    ignore_existing: Annotated[
        bool, "should ignore existing files when downloading, default to True"
    ]


DefaultDownloadOptions = DownloadOptions(ignore_existing=True)


class GoogleDrive:
    DefaultFieldsListFolder: str = (
        "nextPageToken, " "files(kind, id, name, mimeType, size, md5CheckSum)"
    )

    def __init__(self, helper: DriveHelper):
        self.helper = helper
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    def grant_permissions(
        self,
        file_id: str,
        perm_obj: PermissionsCreateRequest,
    ) -> PermissionsCreateResponse:
        return self.helper.grant_permissions(file_id, perm_obj)

    def delete_file(self, file_id: str) -> str:
        return self.helper.delete_file(file_id)

    def get_metadata(
        self, file_id: str, fields: list[str] | None = None
    ) -> File:
        fields_str: str = (
            f"nextPageToken, files({', '.join(fields)})"
            if fields and len(fields) > 0
            else "*"
        )
        return self.helper.get_metadata(file_id, fields=fields_str)

    def dump_metadata(
        self,
        file_id: str,
        path: Path | str,
        fields: list[str] | None = None,
        indent: int = 2,
    ) -> None:
        with open(path, "w+", encoding="utf8") as writefile:
            json.dump(
                self.get_metadata(file_id, fields=fields),
                writefile,
                indent=indent,
                ensure_ascii=False,
            )

    @staticmethod
    def is_downloadable(mimetype: str) -> bool:
        return not mimetype.startswith("application/vnd.google-apps")

    @staticmethod
    def is_remote_folder(file: File) -> bool:
        return file.get("mimeType") == MimeType.GoogleAppsFolder

    def list_folder(
        self,
        folder_id: str,
        fields: list[str] | None = None,
        pageSize: int = 100,
    ) -> list[File]:
        fields_str: str = (
            f"nextPageToken, files({', '.join(fields)})"
            if fields and len(fields) > 0
            else self.DefaultFieldsListFolder
        )
        try:
            response = self.helper.list_folder(folder_id, fields_str, pageSize)
            return response["files"]
        except HttpError as httperr:
            self.logger.error(httperr)
            raise OperationalError(httperr)

    def create_empty_file(self, path: Path, name: str) -> None:
        filepath = path / name
        if filepath.exists():
            if filepath.is_dir():
                raise ValueError("target path is folder")
            filepath.unlink()
        open(filepath, "wb").close()

    def get_filename_from_metadata(self, file_id: str) -> str:
        metadata = self.helper.get_metadata(file_id)
        if not metadata or not metadata.get("name"):
            raise ValueError("file name unspecified")
        return metadata["name"]

    def download_and_save_file(
        self,
        file_id: str,
        path: Path,
        name: str | None = None,
    ) -> None:
        filename = name or self.get_filename_from_metadata(file_id)
        with BytesIO() as buffer:
            self.helper.download_file(file_id, buffer)
            filepath = path / filename
            with open(filepath, "wb") as writefile:
                writefile.write(buffer.read())

    def download_file(
        self,
        file: File,
        path: Path,
        options: DownloadOptions | None = None,
    ) -> None:
        size: int = int(file["size"])
        filename: str = file["name"]
        filepath: Path = path / filename
        options = options or DefaultDownloadOptions

        if size == 0:
            self.logger.warning(f"file <{filename}> is empty")
            return self.create_empty_file(path, filename)

        file_id: str = file["id"]
        src_md5: str = file["md5Checksum"]
        if filepath.is_file():
            if options.get("ignore_existing"):
                return
            dst_md5 = md5(filepath)
            if dst_md5 == src_md5:
                self.logger.info(f"file <{filename}>: MD5 match")
                return
            self.logger.warning(
                f"file <{filename}> corrupted or changed, downloading..."
            )
            return self.download_and_save_file(file_id, path, filename)

        return self.download_and_save_file(file_id, path, filename)

    def create_folder(self, path: Path, exist_ok: bool = True) -> None:
        if not path.exists():
            return path.mkdir(parents=True)
        if path.is_file():
            raise ValueError("destination is file")
        if exist_ok:
            self.logger.warning(f"{path} already exists, skipped it")
            return

        def handle_exc(func: Any, path: str, exc_info: Any) -> None:
            self.logger.error(f"error when deleting {path}: {exc_info}")

        shutil.rmtree(path, onerror=handle_exc)

    def download_folder(
        self,
        folder_id: str,
        path: Path | None = None,
        name: str | None = None,
        options: DownloadOptions | None = None,
    ) -> None:
        options = options or DefaultDownloadOptions
        folder_name = name or self.get_filename_from_metadata(folder_id)
        folder_path = (path or Path()) / folder_name

        self.logger.info(f"Downloading folder {folder_name}...")
        self.create_folder(folder_path)

        files: list[File] = self.list_folder(folder_id)
        num_processed: int = 0
        total: int = len(files)
        for file in files:
            filename = file["name"]
            mimetype = file["mimeType"]
            if mimetype == MimeType.GoogleAppsFolder:
                folder_id = file["id"]
                self.download_folder(
                    folder_id,
                    folder_path,
                    filename,
                    options=options,
                )
            elif self.is_downloadable(mimetype):
                self.download_file(file, folder_path, options=options)
            else:
                self.logger.warning(f"Undownloadable: {file}")
            num_processed += 1
            self.logger.info(
                f"[{folder_path}] Processed {num_processed}/{total}"
            )

    def mkdiff(
        self,
        side: Literal["local", "remote", "both"],
        path: Path,
        type: Literal["file", "folder"] | None = None,
        comment: str | None = None,
    ) -> DiffObj:
        diff = {side: side, path: str(path), type: type, comment: comment}
        return cast(DiffObj, {key: val for key, val in diff.items() if val})

    @staticmethod
    def compare_files(path: Path, remote_file: File) -> bool:
        return md5(path) == remote_file["md5Checksum"]

    def _compare_folders(
        self,
        path: Path,
        folder_id: str,
        remote_path: Path | None = None,
    ) -> Generator[DiffObj, Any, Any]:
        if not path.exists():
            raise ValueError(f"local path does not exist: {path}")

        if len(children := os.listdir(path)) == 0:
            raise ValueError(f"local path {path} is empty")

        if (remote_children := self.list_folder(folder_id)) is None:
            raise ValueError(f"remote path does not exist: {remote_path}")

        mp_remote_name: dict[str, File] = {
            file["name"]: file for file in remote_children
        }
        for filename in children:
            local_child_path = path / filename
            remote_child_path = (remote_path or Path()) / filename
            if local_child_path.is_dir():
                if filename not in mp_remote_name:
                    yield self.mkdiff("local", local_child_path, type="folder")
                    continue
                if not self.is_remote_folder(mp_remote_name[filename]):
                    yield self.mkdiff("both", local_child_path)
                    continue
                yield from self._compare_folders(
                    local_child_path,
                    mp_remote_name[filename]["id"],
                    remote_child_path,
                )
                continue
            elif local_child_path.is_file():
                if filename not in mp_remote_name:
                    yield self.mkdiff("local", local_child_path, type="file")
                    continue
                if self.is_remote_folder(mp_remote_name[filename]):
                    yield self.mkdiff("both", local_child_path)
                    continue
                if not self.compare_files(
                    local_child_path, mp_remote_name[filename]
                ):
                    yield self.mkdiff("both", local_child_path, type="file")
                    continue

        for filename in mp_remote_name:
            if filename not in children:
                remote_child_path = (remote_path or Path()) / filename
                yield self.mkdiff("remote", remote_child_path)

    def compare_folders(self, path: Path, folder_id: str) -> Sequence[DiffObj]:
        return list(self._compare_folders(path, folder_id) or [])
