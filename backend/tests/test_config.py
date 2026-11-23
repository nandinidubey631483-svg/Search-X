"""
Unit tests for SearchX Configuration and Production Security Guards.
Verifies that production startup strictly rejects missing or default SEARCHX_ADMIN_KEY,
while local development and testing environments seamlessly allow standard defaults.
"""
import pytest
from backend.app.config import Settings


def test_development_allows_default_admin_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("SEARCHX_ADMIN_KEY", raising=False)
    s = Settings()
    assert s.ADMIN_API_KEY == "searchx-admin-secret"
    assert s.ENVIRONMENT == "development"


def test_development_allows_custom_admin_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("SEARCHX_ADMIN_KEY", "custom-dev-secret")
    s = Settings()
    assert s.ADMIN_API_KEY == "custom-dev-secret"


def test_production_fails_when_key_is_missing(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SEARCHX_ADMIN_KEY", raising=False)
    with pytest.raises(RuntimeError, match="FATAL SECURITY VIOLATION"):
        Settings()


def test_production_fails_when_key_is_empty_or_whitespace(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SEARCHX_ADMIN_KEY", "   ")
    with pytest.raises(RuntimeError, match="FATAL SECURITY VIOLATION"):
        Settings()


def test_production_fails_when_key_equals_default_secret(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SEARCHX_ADMIN_KEY", "searchx-admin-secret")
    with pytest.raises(RuntimeError, match="cannot be missing or equal to the default 'searchx-admin-secret'"):
        Settings()


def test_production_succeeds_with_secure_unique_key(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SEARCHX_ADMIN_KEY", "prod-super-secure-key-998877")
    s = Settings()
    assert s.ADMIN_API_KEY == "prod-super-secure-key-998877"
    assert s.ENVIRONMENT == "production"
