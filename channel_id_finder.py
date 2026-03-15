#!/usr/bin/env python3
"""
Channel ID Finder — List all Telegram channels and groups with their IDs.

Usage:
    python channel_id_finder.py [--env .env]

Useful for finding the numeric channel ID to pass to the main downloader.
"""
import argparse
import asyncio
import sys

from telethon import TelegramClient
from src.config import load_env_config


def parse_args(argv=None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="channel_id_finder",
        description="List all Telegram channels and groups with their IDs.",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Path to .env file (default: .env).",
    )
    return parser.parse_args(argv)


async def find_channels(config: dict) -> None:
    """Connect to Telegram and list all channels/groups.

    Args:
        config: Configuration dict from load_env_config().
    """
    client = TelegramClient(
        config["session_name"],
        config["api_id"],
        config["api_hash"],
    )

    try:
        await client.start()
    except Exception as e:
        print(f"❌ FATAL ERROR during client start: {e}")
        print("Please verify your API_ID and API_HASH in your .env file.")
        return

    print("--- ✅ Authenticated successfully ---")
    print("Fetching dialogs (chats, channels, groups)...\n")

    dialogs = await client.get_dialogs()

    print(f"{'Chat Name':<55} {'Channel ID':<20}")
    print("-" * 75)

    for dialog in dialogs:
        entity = dialog.entity

        # Only show channels and groups
        if not (hasattr(entity, "megagroup") or hasattr(entity, "broadcast")):
            continue

        chat_id = entity.id

        # Channel/Supergroup IDs need -100 prefix for Telethon
        if hasattr(entity, "broadcast") and entity.broadcast:
            full_id = f"-100{chat_id}"
        elif hasattr(entity, "megagroup") and entity.megagroup:
            full_id = f"-100{chat_id}"
        else:
            full_id = f"-{chat_id}"

        print(f"{entity.title:<55} {full_id:<20}")

    print("-" * 75)
    print("\nUse these IDs with: python telegram_media_downloader.py --channel <ID>")

    await client.disconnect()


def main():
    """CLI entry point."""
    args = parse_args()

    try:
        config = load_env_config(args.env)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

    asyncio.run(find_channels(config))


if __name__ == "__main__":
    main()
