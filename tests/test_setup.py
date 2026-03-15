"""Tests for the interactive .env setup module."""
import os
import pytest
from unittest.mock import patch

from src.setup import run_setup
from telegram_media_downloader import parse_args, cli


@pytest.fixture
def env_path(tmp_path):
    """Return a path to a .env file in a temporary directory."""
    return str(tmp_path / ".env")


class TestRunSetupWritesEnvFile:
    """run_setup() prompts for values and writes a valid .env file."""

    def test_writes_env_with_all_values(self, env_path):
        """All four values are written to the .env file."""
        inputs = iter(["12345", "abc123hash", "my_session", "my_downloads"])
        with patch("builtins.input", side_effect=inputs):
            run_setup(env_path)

        content = open(env_path).read()
        assert "API_ID=12345" in content
        assert "API_HASH=abc123hash" in content
        assert "SESSION_NAME=my_session" in content
        assert "DOWNLOAD_DIR=my_downloads" in content

    def test_uses_defaults_for_optional_values(self, env_path):
        """Pressing Enter for optional values uses defaults."""
        # API_ID, API_HASH are required; SESSION_NAME and DOWNLOAD_DIR get defaults
        inputs = iter(["12345", "abc123hash", "", ""])
        with patch("builtins.input", side_effect=inputs):
            run_setup(env_path)

        content = open(env_path).read()
        assert "API_ID=12345" in content
        assert "API_HASH=abc123hash" in content
        assert "SESSION_NAME=telegram_media_session" in content
        assert "DOWNLOAD_DIR=downloads" in content

    def test_env_file_has_comments(self, env_path):
        """The generated .env file includes helpful comments."""
        inputs = iter(["12345", "abc123hash", "", ""])
        with patch("builtins.input", side_effect=inputs):
            run_setup(env_path)

        content = open(env_path).read()
        assert "# Telegram API credentials" in content


class TestRunSetupValidation:
    """run_setup() validates user input before writing."""

    def test_rejects_non_numeric_api_id_then_accepts_valid(self, env_path):
        """Non-numeric API_ID is rejected; user is re-prompted."""
        inputs = iter(["not_a_number", "12345", "abc123hash", "", ""])
        with patch("builtins.input", side_effect=inputs):
            run_setup(env_path)

        content = open(env_path).read()
        assert "API_ID=12345" in content

    def test_rejects_empty_api_id_then_accepts_valid(self, env_path):
        """Empty API_ID is rejected; user is re-prompted."""
        inputs = iter(["", "12345", "abc123hash", "", ""])
        with patch("builtins.input", side_effect=inputs):
            run_setup(env_path)

        content = open(env_path).read()
        assert "API_ID=12345" in content

    def test_rejects_empty_api_hash_then_accepts_valid(self, env_path):
        """Empty API_HASH is rejected; user is re-prompted."""
        inputs = iter(["12345", "", "abc123hash", "", ""])
        with patch("builtins.input", side_effect=inputs):
            run_setup(env_path)

        content = open(env_path).read()
        assert "API_HASH=abc123hash" in content


class TestRunSetupExistingFile:
    """run_setup() handles an existing .env file gracefully."""

    def test_warns_and_overwrites_when_confirmed(self, env_path):
        """If .env exists and user confirms, it is overwritten."""
        # Create an existing .env
        with open(env_path, "w") as f:
            f.write("OLD_CONTENT=old\n")

        # "y" to confirm overwrite, then the 4 config values
        inputs = iter(["y", "12345", "abc123hash", "", ""])
        with patch("builtins.input", side_effect=inputs):
            run_setup(env_path)

        content = open(env_path).read()
        assert "OLD_CONTENT" not in content
        assert "API_ID=12345" in content

    def test_aborts_when_user_declines_overwrite(self, env_path):
        """If .env exists and user declines, file is not modified."""
        original = "OLD_CONTENT=old\n"
        with open(env_path, "w") as f:
            f.write(original)

        inputs = iter(["n"])
        with patch("builtins.input", side_effect=inputs):
            result = run_setup(env_path)

        # File unchanged
        assert open(env_path).read() == original
        # Function signals abort
        assert result is False


class TestRunSetupReturnValue:
    """run_setup() returns True on success, False on abort."""

    def test_returns_true_on_success(self, env_path):
        """Successful setup returns True."""
        inputs = iter(["12345", "abc123hash", "", ""])
        with patch("builtins.input", side_effect=inputs):
            result = run_setup(env_path)

        assert result is True

    def test_returns_false_on_abort(self, env_path):
        """Aborted setup returns False."""
        with open(env_path, "w") as f:
            f.write("existing\n")

        inputs = iter(["n"])
        with patch("builtins.input", side_effect=inputs):
            result = run_setup(env_path)

        assert result is False


class TestRunSetupOutput:
    """run_setup() prints helpful guidance to the user."""

    def test_prints_telegram_url(self, env_path, capsys):
        """Setup prints the URL where users get API credentials."""
        inputs = iter(["12345", "abc123hash", "", ""])
        with patch("builtins.input", side_effect=inputs):
            run_setup(env_path)

        output = capsys.readouterr().out
        assert "https://my.telegram.org/apps" in output

    def test_prints_success_message(self, env_path, capsys):
        """Setup prints a success message after writing."""
        inputs = iter(["12345", "abc123hash", "", ""])
        with patch("builtins.input", side_effect=inputs):
            run_setup(env_path)

        output = capsys.readouterr().out
        assert ".env" in output


def _argparse_ns(**kwargs):
    """Create a minimal argparse.Namespace with given attributes."""
    import argparse
    return argparse.Namespace(**kwargs)


class TestSetupCLIArgument:
    """--setup CLI argument is accepted and triggers interactive setup."""

    def test_parse_args_accepts_setup_without_channel(self):
        """--setup does not require --channel."""
        args = parse_args(["--setup"])
        assert args.setup is True

    def test_parse_args_setup_with_custom_env(self):
        """--setup respects --env flag."""
        args = parse_args(["--setup", "--env", "custom.env"])
        assert args.setup is True
        assert args.env == "custom.env"

    def test_setup_takes_precedence_over_channel(self):
        """--setup runs setup even if --channel is also provided."""
        args = parse_args(["--setup", "--channel", "my_channel"])
        assert args.setup is True

    def test_cli_calls_run_setup_and_exits(self):
        """cli() calls run_setup() when --setup is passed and exits 0."""
        with patch("telegram_media_downloader.parse_args") as mock_parse:
            mock_parse.return_value = _argparse_ns(setup=True, env=".env")
            with patch("telegram_media_downloader.run_setup", return_value=True) as mock_run:
                with pytest.raises(SystemExit) as exc_info:
                    cli()
                mock_run.assert_called_once_with(".env")
        assert exc_info.value.code == 0

    def test_cli_exits_1_when_setup_aborted(self):
        """cli() exits 1 when run_setup() returns False (user aborted)."""
        with patch("telegram_media_downloader.parse_args") as mock_parse:
            mock_parse.return_value = _argparse_ns(setup=True, env=".env")
            with patch("telegram_media_downloader.run_setup", return_value=False):
                with pytest.raises(SystemExit) as exc_info:
                    cli()
        assert exc_info.value.code == 1
