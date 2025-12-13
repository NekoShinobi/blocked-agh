"""Pytest configuration and shared fixtures."""

import os

import pytest

# Set environment variables before any imports
os.environ.setdefault("ADGUARDHOME_URL", "http://test-adguard:3000")
os.environ.setdefault("ADGUARDHOME_USER", "test_admin")
os.environ.setdefault("ADGUARDHOME_PASS", "test_password")
os.environ.setdefault("NTFY_TOKEN", "test_token")
os.environ.setdefault("NTFY_TOPIC", "TestTopic")
os.environ.setdefault("BLOCKED_AGH_URL", "http://test-blocked-agh:8000")
os.environ.setdefault("BACKGROUND_IMAGE_URL", "http://test.com/image.jpg")


@pytest.fixture(autouse=True)
def reset_env_vars(monkeypatch):
    """Reset environment variables for each test to ensure isolation."""
    monkeypatch.setenv("ADGUARDHOME_URL", "http://test-adguard:3000")
    monkeypatch.setenv("ADGUARDHOME_USER", "test_admin")
    monkeypatch.setenv("ADGUARDHOME_PASS", "test_password")
    monkeypatch.setenv("NTFY_TOKEN", "test_token")
    monkeypatch.setenv("NTFY_TOPIC", "TestTopic")
    monkeypatch.setenv("BLOCKED_AGH_URL", "http://test-blocked-agh:8000")
    monkeypatch.setenv("BACKGROUND_IMAGE_URL", "http://test.com/image.jpg")
