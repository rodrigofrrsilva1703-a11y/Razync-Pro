from unittest.mock import patch

import session_persistence


class FakeController:
    def __init__(self):
        self.values = {}

    def get(self, name):
        return self.values.get(name)

    def set(self, name, value, **options):
        self.values[name] = value
        self.set_options = options

    def remove(self, name, **options):
        self.values.pop(name, None)
        self.remove_options = options


def test_refresh_token_cookie_is_encrypted_and_secure():
    controller = FakeController()
    secret = "a" * 40

    with patch("session_persistence._secret_value", return_value=secret):
        session_persistence.persist_refresh_token(controller, "refresh-token-value")
        stored = controller.values[session_persistence.COOKIE_NAME]
        assert "refresh-token-value" not in stored
        assert session_persistence.read_refresh_token(controller) == "refresh-token-value"

    assert controller.set_options["secure"] is True
    assert controller.set_options["same_site"] == "lax"


def test_invalid_cookie_is_rejected_and_logout_clears_it():
    controller = FakeController()
    controller.values[session_persistence.COOKIE_NAME] = "invalid"

    with patch("session_persistence._secret_value", return_value="b" * 40):
        assert session_persistence.read_refresh_token(controller) is None
        session_persistence.clear_persisted_session(controller)

    assert session_persistence.COOKIE_NAME not in controller.values
