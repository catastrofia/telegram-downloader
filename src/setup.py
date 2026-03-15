"""Interactive .env file setup for Telegram Media Downloader."""
import os

# Defaults matching .env.example and src/config.py
_DEFAULT_SESSION_NAME = "telegram_media_session"
_DEFAULT_DOWNLOAD_DIR = "downloads"


def _prompt_api_id() -> str:
    """Prompt for API_ID until a valid numeric value is entered."""
    while True:
        value = input("API_ID (numeric, from https://my.telegram.org/apps): ").strip()
        if not value:
            print("  ⚠️  API_ID is required and cannot be empty.")
            continue
        try:
            int(value)
        except ValueError:
            print(f"  ⚠️  API_ID must be a number, got: '{value}'")
            continue
        return value


def _prompt_api_hash() -> str:
    """Prompt for API_HASH until a non-empty value is entered."""
    while True:
        value = input("API_HASH (from https://my.telegram.org/apps): ").strip()
        if not value:
            print("  ⚠️  API_HASH is required and cannot be empty.")
            continue
        return value


def run_setup(env_path: str = ".env") -> bool:
    """Interactively prompt for configuration values and write a .env file.

    Args:
        env_path: Path where the .env file will be written.

    Returns:
        True if setup completed successfully, False if aborted.
    """
    print("\n🔧 Telegram Media Downloader — Setup")
    print("=" * 42)
    print("Get your API credentials at: https://my.telegram.org/apps\n")

    # Check for existing file
    if os.path.exists(env_path):
        answer = input(
            f"⚠️  {env_path} already exists. Overwrite? [y/N] "
        ).strip().lower()
        if answer not in ("y", "yes"):
            print("Setup aborted.")
            return False

    # Prompt for values
    api_id = _prompt_api_id()
    api_hash = _prompt_api_hash()

    session_name = input(
        f"SESSION_NAME [{_DEFAULT_SESSION_NAME}]: "
    ).strip() or _DEFAULT_SESSION_NAME

    download_dir = input(
        f"DOWNLOAD_DIR [{_DEFAULT_DOWNLOAD_DIR}]: "
    ).strip() or _DEFAULT_DOWNLOAD_DIR

    # Write .env file
    content = (
        "# Telegram API credentials — get yours at https://my.telegram.org/apps\n"
        f"API_ID={api_id}\n"
        f"API_HASH={api_hash}\n"
        "\n"
        "# Session name (used for the .session file that stores your login)\n"
        f"SESSION_NAME={session_name}\n"
        "\n"
        "# Default download directory (can be overridden via CLI --output)\n"
        f"DOWNLOAD_DIR={download_dir}\n"
    )

    with open(env_path, "w") as f:
        f.write(content)

    print(f"\n✅ .env file written to: {env_path}")
    print("You can now run: python telegram_media_downloader.py --login")
    return True
