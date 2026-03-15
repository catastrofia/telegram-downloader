"""Tests for config module."""
import os
import pytest
from unittest.mock import patch


class TestLoadEnvConfig:
    """Tests for load_env_config()."""

    def test_loads_api_id_from_env(self):
        """API_ID is read from environment and cast to int."""
        from src.config import load_env_config

        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123",
        }):
            config = load_env_config()
            assert config["api_id"] == 12345

    def test_loads_api_hash_from_env(self):
        """API_HASH is read from environment as string."""
        from src.config import load_env_config

        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123hash",
        }):
            config = load_env_config()
            assert config["api_hash"] == "abc123hash"

    def test_default_session_name(self):
        """SESSION_NAME defaults to 'telegram_media_session'."""
        from src.config import load_env_config

        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123",
        }, clear=False):
            os.environ.pop("SESSION_NAME", None)
            config = load_env_config()
            assert config["session_name"] == "telegram_media_session"

    def test_custom_session_name(self):
        """SESSION_NAME can be overridden via env."""
        from src.config import load_env_config

        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123",
            "SESSION_NAME": "my_session",
        }):
            config = load_env_config()
            assert config["session_name"] == "my_session"

    def test_default_download_dir(self):
        """DOWNLOAD_DIR defaults to 'downloads'."""
        from src.config import load_env_config

        with patch.dict(os.environ, {
            "API_ID": "12345",
            "API_HASH": "abc123",
        }, clear=False):
            os.environ.pop("DOWNLOAD_DIR", None)
            config = load_env_config()
            assert config["download_dir"] == "downloads"

    def test_missing_api_id_raises(self):
        """Missing API_ID raises ValueError."""
        from src.config import load_env_config

        with patch.dict(os.environ, {"API_HASH": "abc123"}, clear=True):
            with pytest.raises(ValueError, match="API_ID"):
                load_env_config()

    def test_missing_api_hash_raises(self):
        """Missing API_HASH raises ValueError."""
        from src.config import load_env_config

        with patch.dict(os.environ, {"API_ID": "12345"}, clear=True):
            with pytest.raises(ValueError, match="API_HASH"):
                load_env_config()

    def test_non_numeric_api_id_raises(self):
        """Non-numeric API_ID raises ValueError."""
        from src.config import load_env_config

        with patch.dict(os.environ, {
            "API_ID": "not_a_number",
            "API_HASH": "abc123",
        }):
            with pytest.raises(ValueError, match="API_ID"):
                load_env_config()
