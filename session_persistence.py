from __future__ import annotations

import base64
import hashlib
import os
from datetime import datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from streamlit_cookies_controller import CookieController


COOKIE_NAME = "__Secure-razync_session"
COOKIE_DAYS = 30


def _secret_value() -> str:
    value = os.getenv("SESSION_COOKIE_SECRET", "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get("SESSION_COOKIE_SECRET", "")).strip()
    except Exception:
        return ""


def is_persistence_configured() -> bool:
    return len(_secret_value()) >= 32


def _fernet() -> Fernet:
    secret = _secret_value()
    if len(secret) < 32:
        raise RuntimeError("SESSION_COOKIE_SECRET precisa ter pelo menos 32 caracteres.")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def persistent_session_controller() -> CookieController | None:
    if not is_persistence_configured():
        return None
    return CookieController(key="razync_persistent_session")


def seal_refresh_token(refresh_token: str) -> str:
    return _fernet().encrypt(refresh_token.encode("utf-8")).decode("ascii")


def unseal_refresh_token(value: str) -> str | None:
    try:
        return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeError):
        return None


def read_refresh_token(controller: Any) -> str | None:
    value = controller.get(COOKIE_NAME)
    if not isinstance(value, str) or not value:
        return None
    return unseal_refresh_token(value)


def persist_refresh_token(controller: Any, refresh_token: str) -> None:
    controller.set(
        COOKIE_NAME,
        seal_refresh_token(refresh_token),
        path="/",
        expires=datetime.now() + timedelta(days=COOKIE_DAYS),
        secure=True,
        same_site="lax",
    )


def clear_persisted_session(controller: Any | None) -> None:
    if controller is None:
        return
    try:
        controller.remove(COOKIE_NAME, path="/", secure=True, same_site="lax")
    except (KeyError, ValueError):
        return
