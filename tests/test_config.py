"""Tests for config module."""
import os
import pytest
from unittest.mock import patch

from src.config import load_env_config


@pytest.fixture(autouse=True)
def _mock_dotenv():
    """Prevent load_dotenv from reading real .env files during tests."""
    with patch("src.config.load_dotenv"):
        yield


class TestLoadEnvConfig:
    """Tests for load_env_config()."""

    def test_loads_api_id_from_env(self):
        """API_ID is read from environment and cast to int."""
        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123",
        }, clear=True):
            config = load_env_config()
            assert config["api_id"] == 12345

    def test_loads_api_hash_from_env(self):
        """API_HASH is read from environment as string."""
        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123hash",
        }, clear=True):
            config = load_env_config()
            assert config["api_hash"] == "abc123hash"

    def test_default_session_name(self):
        """SESSION_NAME defaults to 'telegram_media_session'."""
        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123",
        }, clear=True):
            config = load_env_config()
            assert config["session_name"] == "telegram_media_session"

    def test_custom_session_name(self):
        """SESSION_NAME can be overridden via env."""
        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123",
            "SESSION_NAME": "my_session",
        }, clear=True):
            config = load_env_config()
            assert config["session_name"] == "my_session"

    def test_default_download_dir(self):
        """DOWNLOAD_DIR defaults to 'downloads'."""
        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123",
        }, clear=True):
            config = load_env_config()
            assert config["download_dir"] == "downloads"

    def test_missing_api_id_raises(self):
        """Missing API_ID raises ValueError."""
        with patch.dict(os.environ, {"API_HASH": "abc123"}, clear=True):
            with pytest.raises(ValueError, match="API_ID"):
                load_env_config()

    def test_missing_api_hash_raises(self):
        """Missing API_HASH raises ValueError."""
        with patch.dict(os.environ, {"API_ID": "12345"}, clear=True):
            with pytest.raises(ValueError, match="API_HASH"):
                load_env_config()

    def test_non_numeric_api_id_raises(self):
        """Non-numeric API_ID raises ValueError."""
        with patch.dict(os.environ, {
            "API_ID": "not_a_number",
            "API_HASH": "abc123",
        }, clear=True):
            with pytest.raises(ValueError, match="API_ID"):
                load_env_config()
