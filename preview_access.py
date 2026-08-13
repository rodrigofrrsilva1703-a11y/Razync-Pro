from __future__ import annotations

from database import authenticate, create_user

PREVIEW_EMAIL = "preview@razync.local"
PREVIEW_PASSWORD = "RazyncPreview2026!"


def get_preview_user() -> dict:
    """Retorna um usuário técnico único para o modo de desenvolvimento/preview."""
    user = authenticate(PREVIEW_EMAIL, PREVIEW_PASSWORD)
    if user:
        return user

    create_user("Razync Preview", PREVIEW_EMAIL, PREVIEW_PASSWORD)
    user = authenticate(PREVIEW_EMAIL, PREVIEW_PASSWORD)
    if not user:
        raise RuntimeError("Não foi possível inicializar o acesso de preview do Razync Pro.")
    return user
