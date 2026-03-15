"""Configuration loading from .env files and environment variables."""
import os
from dotenv import load_dotenv


def load_env_config(env_path: str = ".env") -> dict:
    """Load configuration from .env file and environment variables.

    Reads API credentials and optional settings from a .env file
    (or environment variables). Required: API_ID, API_HASH.

    Args:
        env_path: Path to the .env file. Defaults to ".env" in cwd.

    Returns:
        dict with keys: api_id (int), api_hash (str), session_name (str),
        download_dir (str).

    Raises:
        ValueError: If required variables are missing or invalid.
    """
    load_dotenv(env_path, override=False)

    # --- Required ---
    api_id_raw = os.environ.get("API_ID")
    if not api_id_raw:
        raise ValueError(
            "API_ID is required. Set it in your .env file or as an "
            "environment variable. Get yours at https://my.telegram.org/apps"
        )
    try:
        api_id = int(api_id_raw)
    except ValueError:
        raise ValueError(
            f"API_ID must be a numeric integer, got: '{api_id_raw}'"
        )

    api_hash = os.environ.get("API_HASH")
    if not api_hash:
        raise ValueError(
            "API_HASH is required. Set it in your .env file or as an "
            "environment variable. Get yours at https://my.telegram.org/apps"
        )

    # --- Optional with defaults ---
    session_name = os.environ.get("SESSION_NAME", "telegram_media_session")
    download_dir = os.environ.get("DOWNLOAD_DIR", "downloads")

    return {
        "api_id": api_id,
        "api_hash": api_hash,
        "session_name": session_name,
        "download_dir": download_dir,
    }
