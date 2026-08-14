from __future__ import annotations

from pathlib import PurePath
import re
import uuid

from auth_service import authenticated_client


BUCKET = "documents"


def _safe_filename(filename: str) -> str:
    name = PurePath(filename.replace("\\\\", "/")).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return name[:180] or "documento"


def upload_document(
    auth_user_id: str,
    access_token: str,
    refresh_token: str,
    filename: str,
    content: bytes,
    mime_type: str,
) -> str:
    path = f"{auth_user_id}/{uuid.uuid4().hex}-{_safe_filename(filename)}"
    client = authenticated_client(access_token, refresh_token)
    client.storage.from_(BUCKET).upload(
        path,
        content,
        {"content-type": mime_type or "application/octet-stream", "upsert": "false"},
    )
    return path


def download_document(
    access_token: str,
    refresh_token: str,
    storage_path: str,
) -> bytes:
    client = authenticated_client(access_token, refresh_token)
    return client.storage.from_(BUCKET).download(storage_path)


def remove_document(
    access_token: str,
    refresh_token: str,
    storage_path: str,
) -> None:
    client = authenticated_client(access_token, refresh_token)
    client.storage.from_(BUCKET).remove([storage_path])
