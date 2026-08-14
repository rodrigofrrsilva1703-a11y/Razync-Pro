from __future__ import annotations

import os
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, uuid5

from supabase import Client, create_client


DEFAULT_SUPABASE_URL = "https://etimfgenlludorrftapb.supabase.co"
# Publishable keys are designed for public clients; authorization is enforced by RLS.
DEFAULT_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_NYDzyw9J-lH9dMDuVOnLsg_m7B1H3mF"
DEFAULT_APP_URL = "https://razync-pro-je8appbtpfqcrg33nn6u5r8.streamlit.app/"
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"


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


def is_developer_github_configured() -> bool:
    """Return True only when every server-side developer OAuth secret exists."""
    return all(
        _secret(name)
        for name in ("GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "DEVELOPER_GITHUB_USER")
    )


def _app_url() -> str:
    value = _secret("APP_URL") or DEFAULT_APP_URL
    return value.rstrip("/") + "/"


def _github_state(now: int | None = None) -> str:
    issued_at = int(time.time() if now is None else now)
    payload = f"rzgh.{issued_at}.{secrets.token_urlsafe(24)}"
    signature = hmac.new(
        _secret("GITHUB_CLIENT_SECRET").encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{signature}"


def _validate_github_state(state: str, now: int | None = None) -> None:
    try:
        prefix, issued_at, nonce, signature = state.split(".", 3)
        timestamp = int(issued_at)
    except (AttributeError, TypeError, ValueError) as exc:
        raise AuthServiceError("A validação do acesso pelo GitHub expirou.") from exc

    payload = f"{prefix}.{issued_at}.{nonce}"
    expected = hmac.new(
        _secret("GITHUB_CLIENT_SECRET").encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    current_time = int(time.time() if now is None else now)
    if (
        prefix != "rzgh"
        or not hmac.compare_digest(signature, expected)
        or timestamp > current_time + 60
        or current_time - timestamp > 600
    ):
        raise AuthServiceError("A validação do acesso pelo GitHub expirou.")


def github_authorization_url() -> str:
    if not is_developer_github_configured():
        raise AuthConfigurationError("O acesso de desenvolvedor não está configurado.")
    query = urlencode(
        {
            "client_id": _secret("GITHUB_CLIENT_ID"),
            "redirect_uri": _app_url(),
            "scope": "read:user user:email",
            "state": _github_state(),
            "allow_signup": "false",
        }
    )
    return f"{GITHUB_AUTHORIZE_URL}?{query}"


def _github_json_request(
    url: str, *, data: dict[str, str] | None = None, token: str = ""
) -> Any:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Razync-Pro",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = None
    if data is not None:
        body = urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, data=body, headers=headers), timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise AuthServiceError("Não foi possível validar o acesso pelo GitHub agora.") from exc


def github_sign_in(code: str, state: str) -> dict[str, Any]:
    """Exchange an OAuth code and allow only the configured developer account."""
    if not is_developer_github_configured():
        raise AuthConfigurationError("O acesso de desenvolvedor não está configurado.")
    if not code:
        raise AuthServiceError("O GitHub não retornou um código de acesso válido.")
    _validate_github_state(state)

    token_data = _github_json_request(
        GITHUB_TOKEN_URL,
        data={
            "client_id": _secret("GITHUB_CLIENT_ID"),
            "client_secret": _secret("GITHUB_CLIENT_SECRET"),
            "code": code,
        },
    )
    access_token = str(token_data.get("access_token") or "")
    if not access_token:
        error_code = str(token_data.get("error") or "")
        safe_messages = {
            "bad_verification_code": (
                "O código retornado pelo GitHub expirou ou já foi usado. "
                "Volte à tela inicial e tente entrar novamente."
            ),
            "incorrect_client_credentials": (
                "O Client ID ou Client Secret do GitHub não corresponde ao OAuth App."
            ),
            "redirect_uri_mismatch": (
                "A URL de retorno do GitHub não corresponde à URL cadastrada no OAuth App."
            ),
        }
        raise AuthServiceError(
            safe_messages.get(error_code, "O GitHub não autorizou este acesso.")
        )

    profile = _github_json_request(f"{GITHUB_API_URL}/user", token=access_token)
    login = str(profile.get("login") or "")
    allowed_login = _secret("DEVELOPER_GITHUB_USER")
    if not login or not hmac.compare_digest(login.casefold(), allowed_login.casefold()):
        raise AuthServiceError("Esta conta do GitHub não possui acesso de desenvolvedor.")

    email = str(profile.get("email") or "")
    if not email:
        emails = _github_json_request(
            f"{GITHUB_API_URL}/user/emails", token=access_token
        )
        verified = [item for item in emails if item.get("verified")]
        primary = next((item for item in verified if item.get("primary")), None)
        if primary or verified:
            email = str((primary or verified[0]).get("email") or "")
    github_id = str(profile.get("id") or login)
    return {
        "auth_user_id": str(uuid5(NAMESPACE_URL, f"https://github.com/id/{github_id}")),
        "email": email or f"{github_id}+{login}@users.noreply.github.com",
        "name": str(profile.get("name") or login),
        "github_login": login,
        "provider": "github",
    }


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


def update_password(access_token: str, refresh_token: str, new_password: str) -> None:
    """Change the password only after restoring the authenticated session."""
    if len(new_password) < 8:
        raise AuthServiceError("A nova senha deve ter pelo menos 8 caracteres.")
    client = _client()
    try:
        client.auth.set_session(access_token, refresh_token)
        response = client.auth.update_user({"password": new_password})
    except Exception as exc:
        raise AuthServiceError("Não foi possível alterar a senha agora.") from exc
    if response.user is None:
        raise AuthServiceError("Não foi possível validar a alteração da senha.")


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
