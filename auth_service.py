from __future__ import annotations

import os
from typing import Any

from supabase import Client, create_client


DEFAULT_SUPABASE_URL = "https://etimfgenlludorrftapb.supabase.co"
# Publishable keys are designed for public clients; authorization is enforced by RLS.
DEFAULT_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_NYDzyw9J-lH9dMDuVOnLsg_m7B1H3mF"


class AuthConfigurationError(RuntimeError):
    pass


class AuthServiceError(RuntimeError):
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


def is_supabase_auth_configured() -> bool:
    return bool(
        (_secret("SUPABASE_URL") or DEFAULT_SUPABASE_URL)
        and (_secret("SUPABASE_PUBLISHABLE_KEY") or DEFAULT_SUPABASE_PUBLISHABLE_KEY)
    )


def _client() -> Client:
    url = _secret("SUPABASE_URL") or DEFAULT_SUPABASE_URL
    key = _secret("SUPABASE_PUBLISHABLE_KEY") or DEFAULT_SUPABASE_PUBLISHABLE_KEY
    if not url or not key:
        raise AuthConfigurationError(
            "SUPABASE_URL e SUPABASE_PUBLISHABLE_KEY não estão configurados."
        )
    return create_client(url, key)


def sign_in(email: str, password: str) -> dict[str, Any]:
    client = _client()
    try:
        response = client.auth.sign_in_with_password(
            {"email": email.strip().lower(), "password": password}
        )
    except Exception as exc:
        raise AuthServiceError("E-mail ou senha inválidos.") from exc

    if response.user is None or response.session is None:
        raise AuthServiceError("Confirme seu e-mail antes de entrar.")

    return {
        "auth_user_id": str(response.user.id),
        "email": response.user.email or email.strip().lower(),
        "name": (response.user.user_metadata or {}).get("name", ""),
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
    }



def restore_session(refresh_token: str) -> dict[str, Any]:
    """Exchange a persisted refresh token and validate the remote Auth user."""
    client = _client()
    try:
        response = client.auth.refresh_session(refresh_token)
    except Exception as exc:
        raise AuthServiceError("A sessão salva expirou.") from exc

    if response.user is None or response.session is None:
        raise AuthServiceError("A sessão salva expirou.")

    return {
        "auth_user_id": str(response.user.id),
        "email": response.user.email or "",
        "name": (response.user.user_metadata or {}).get("name", ""),
        "access_token": response.session.access_token,
        "refresh_token": response.session.refresh_token,
    }

def sign_up(name: str, email: str, password: str) -> dict[str, Any]:
    client = _client()
    try:
        response = client.auth.sign_up(
            {
                "email": email.strip().lower(),
                "password": password,
                "options": {"data": {"name": name.strip()}},
            }
        )
    except Exception as exc:
        raise AuthServiceError(
            "Não foi possível criar a conta. Verifique os dados ou tente novamente."
        ) from exc

    if response.user is None:
        raise AuthServiceError("Não foi possível criar a conta.")

    result = {
        "auth_user_id": str(response.user.id),
        "email": response.user.email or email.strip().lower(),
        "name": name.strip(),
        "confirmed": response.session is not None,
    }
    if response.session is not None:
        result.update(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
        )
    return result


def reset_password(email: str) -> None:
    client = _client()
    try:
        client.auth.reset_password_email(email.strip().lower())
    except Exception as exc:
        raise AuthServiceError(
            "Não foi possível enviar a recuperação agora."
        ) from exc


def sign_out(access_token: str, refresh_token: str) -> None:
    if not access_token or not refresh_token:
        return
    client = _client()
    try:
        client.auth.set_session(access_token, refresh_token)
        client.auth.sign_out()
    except Exception:
        # Local session must still be cleared if the remote request is unavailable.
        return


def authenticated_client(access_token: str, refresh_token: str) -> Client:
    client = _client()
    client.auth.set_session(access_token, refresh_token)
    return client
