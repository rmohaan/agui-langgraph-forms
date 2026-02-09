from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import UploadFile

UPLOAD_DIR = Path(os.environ.get("AGUI_UPLOAD_DIR", Path(__file__).resolve().parent / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
    "image/tiff",
    "application/pdf",
    "application/x-pdf",
}

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff", ".pdf"}


@dataclass
class UploadRecord:
    file_id: str
    filename: str
    content_type: str
    size: int
    path: Path

    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
            "path": str(self.path),
        }


def _safe_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def _metadata_path(file_id: str) -> Path:
    return UPLOAD_DIR / f"{file_id}.json"


def save_upload(file: UploadFile) -> UploadRecord:
    filename = file.filename or "uploaded-file"
    extension = _safe_extension(filename)
    content_type = (file.content_type or "application/octet-stream").lower()

    if content_type not in ALLOWED_CONTENT_TYPES and extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")

    file_id = uuid4().hex
    target_extension = extension if extension else ".bin"
    target_path = UPLOAD_DIR / f"{file_id}{target_extension}"

    data = file.file.read()
    target_path.write_bytes(data)

    record = UploadRecord(
        file_id=file_id,
        filename=filename,
        content_type=content_type,
        size=len(data),
        path=target_path,
    )

    _metadata_path(file_id).write_text(json.dumps(record.to_dict(), indent=2))
    return record


def get_upload(file_id: str) -> Optional[UploadRecord]:
    meta_path = _metadata_path(file_id)
    if not meta_path.exists():
        return None
    payload = json.loads(meta_path.read_text())
    path = Path(payload["path"])
    if not path.exists():
        return None
    return UploadRecord(
        file_id=payload["file_id"],
        filename=payload["filename"],
        content_type=payload["content_type"],
        size=int(payload["size"]),
        path=path,
    )
