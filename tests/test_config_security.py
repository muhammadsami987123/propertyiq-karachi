import pytest

from app.config import DEFAULT_ADMIN_TOKEN_PLACEHOLDER, Settings


def test_placeholder_admin_token_rejected_outside_debug():
    settings = Settings(ADMIN_TOKEN=DEFAULT_ADMIN_TOKEN_PLACEHOLDER, DEBUG=False)
    with pytest.raises(RuntimeError):
        settings.require_production_admin_token()


def test_placeholder_admin_token_allowed_in_debug():
    settings = Settings(ADMIN_TOKEN=DEFAULT_ADMIN_TOKEN_PLACEHOLDER, DEBUG=True)
    settings.require_production_admin_token()  # should not raise


def test_real_admin_token_allowed_outside_debug():
    settings = Settings(ADMIN_TOKEN="a-real-generated-secret", DEBUG=False)
    settings.require_production_admin_token()  # should not raise


def test_wildcard_cors_disables_credentials():
    settings = Settings(CORS_ORIGINS="*")
    assert settings.cors_origins_list == ["*"]
    assert settings.cors_allow_credentials is False


def test_explicit_origins_allow_credentials():
    settings = Settings(CORS_ORIGINS="https://example.com,https://app.example.com")
    assert settings.cors_allow_credentials is True
