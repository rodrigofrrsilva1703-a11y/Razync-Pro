from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from auth_service import DEFAULT_SUPABASE_PUBLISHABLE_KEY, DEFAULT_SUPABASE_URL


class AccountDeletionError(RuntimeError):
    pass


def _secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def delete_account(access_token: str) -> None:
    """Delete the authenticated Supabase account through the protected Edge Function."""
    if not access_token:
        raise AccountDeletionError("Sua sessão precisa ser validada novamente antes da exclusão.")

    base_url = (_secret("SUPABASE_URL") or DEFAULT_SUPABASE_URL).rstrip("/")
    publishable_key = _secret("SUPABASE_PUBLISHABLE_KEY") or DEFAULT_SUPABASE_PUBLISHABLE_KEY
    request = Request(
        f"{base_url}/functions/v1/delete-account",
        data=b"{}",
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "apikey": publishable_key,
            "Content-Type": "application/json",
            "User-Agent": "Razync-Pro",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8") or "{}")
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8") or "{}")
            message = str(payload.get("error") or "")
        except Exception:
            message = ""
        raise AccountDeletionError(message or "Não foi possível excluir a conta agora.") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise AccountDeletionError("Não foi possível concluir a exclusão agora. Tente novamente mais tarde.") from exc

    if not payload.get("deleted"):
        raise AccountDeletionError("A exclusão não foi confirmada pelo servidor.")
