#!/usr/bin/env python3
"""Telegram Media Downloader — CLI entry point.

Downloads media (video, photo, audio, documents) from Telegram channels
with flexible naming strategies and filtering options.
"""
import argparse
import asyncio
import os
import sys

from telethon import TelegramClient

from src.config import load_env_config
from src.media import MediaType
from src.naming import NamingStrategy
from src.downloader import (
    check_cryptg,
    build_media_list,
    print_scan_summary,
    print_file_listing,
    download_media_list,
)


def parse_args(argv=None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed argparse.Namespace with all CLI options.
    """
    epilog = """\
examples:
  # Download all media from a channel
  python telegram_media_downloader.py -c my_channel

  # Download only videos and photos, limit to 50 files
  python telegram_media_downloader.py -c my_channel -t video photo --limit 50

  # Dry run with sequential naming and a prefix
  python telegram_media_downloader.py -c my_channel -n sequential --prefix vacation --dry-run

  # Custom naming pattern with 4-digit padding
  python telegram_media_downloader.py -c my_channel -n custom --pattern "clip_{n}" --padding 4

  # Use a specific output directory and skip confirmation
  python telegram_media_downloader.py -c my_channel -o ./my_downloads -y

  # Download from a channel by numeric ID
  python telegram_media_downloader.py -c -1001234567890 -t video
"""

    parser = argparse.ArgumentParser(
        prog="telegram_media_downloader",
        description="Download media from Telegram channels with flexible options.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--channel", "-c",
        required=True,
        help="Channel name or numeric ID",
    )
    parser.add_argument(
        "--type", "-t",
        nargs="+",
        default=["all"],
        choices=["all", "video", "photo", "audio", "document"],
        dest="type",
        help='Media types to download (default: all)',
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Download directory (overrides .env DOWNLOAD_DIR)",
    )
    parser.add_argument(
        "--naming", "-n",
        default="sequential",
        choices=["original", "sequential", "custom"],
        help="Naming strategy (default: sequential)",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Prefix for sequential naming (default: none)",
    )
    parser.add_argument(
        "--pattern",
        default=None,
        help="Custom pattern with {n} placeholder (e.g. 'clip_{n}')",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=3,
        help="Zero-padding width for file numbering (default: 3)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of files to download",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan only — list files without downloading",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip download confirmation prompt",
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Path to .env file (default: .env)",
    )

    return parser.parse_args(argv)


async def resolve_channel(client, channel_identifier):
    """Resolve a channel by name or numeric ID.

    Tries parsing the identifier as an integer first (numeric Telegram ID).
    On failure, searches the user's dialog titles for an exact match.

    Args:
        client: A connected TelegramClient.
        channel_identifier: Channel name string or numeric ID string.

    Returns:
        The resolved Telethon entity, or None if not found.
    """
    # Try numeric ID first
    try:
        channel_id = int(channel_identifier)
        try:
            entity = await client.get_entity(channel_id)
            return entity
        except Exception:
            pass
    except ValueError:
        pass

    # Fall back to searching dialog titles for exact match
    try:
        async for dialog in client.iter_dialogs():
            if dialog.name == channel_identifier:
                return dialog.entity
    except Exception:
        pass

    return None


async def main(args) -> int:
    """Main application logic.

    Orchestrates config loading, channel resolution, media scanning,
    and downloading.

    Args:
        args: Parsed argparse.Namespace from :func:`parse_args`.

    Returns:
        Exit code: 0 for success, 1 for error.
    """
    # Load configuration
    try:
        config = load_env_config(args.env)
    except ValueError as exc:
        print(f"❌ Configuration error: {exc}")
        return 1

    # Determine download directory (CLI flag overrides .env)
    download_dir = args.output if args.output else config["download_dir"]

    # Check for cryptg acceleration
    check_cryptg()

    # Create and start Telegram client
    client = TelegramClient(
        config["session_name"],
        config["api_id"],
        config["api_hash"],
    )

    try:
        await client.start()
        print("✅ Connected to Telegram.\n")
    except Exception as exc:
        print(f"❌ Failed to connect to Telegram: {exc}")
        return 1

    try:
        # Resolve channel
        print(f"🔍 Resolving channel: {args.channel}")
        entity = await resolve_channel(client, args.channel)
        if entity is None:
            print(f"❌ Could not find channel: {args.channel}")
            return 1

        channel_title = getattr(entity, "title", args.channel)
        print(f"✅ Found channel: {channel_title}\n")

        # PASS 1: Fetch all messages, reverse to oldest-first
        print("📡 Fetching messages...")
        messages = []
        async for message in client.iter_messages(entity):
            messages.append(message)
        messages.reverse()  # oldest first
        print(f"   Retrieved {len(messages)} messages.\n")

        # Build filtered media list
        media_list = build_media_list(messages, args.type)

        # Apply --limit if set
        if args.limit is not None and args.limit < len(media_list):
            media_list = media_list[: args.limit]

        # Print scan results
        print_scan_summary(media_list)
        print_file_listing(media_list)

        if not media_list:
            print("\nNothing to download.")
            return 0

        # Dry run stops here
        if args.dry_run:
            print("\n🏁 Dry run complete — no files downloaded.")
            return 0

        # Confirmation prompt
        if not args.yes:
            print(f"\n📂 Download directory: {os.path.abspath(download_dir)}")
            answer = input("Proceed with download? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("Aborted.")
                return 0

        # PASS 2: Download
        naming_strategy = NamingStrategy(args.naming)
        print(f"\n⬇️  Downloading {len(media_list)} files...\n")

        stats = await download_media_list(
            client=client,
            media_list=media_list,
            download_dir=download_dir,
            naming_strategy=naming_strategy,
            prefix=args.prefix,
            padding=args.padding,
            pattern=args.pattern,
        )

        # Final stats
        print(f"\n{'='*50}")
        print(f"🏁 Download complete!")
        print(f"   ✅ Downloaded: {stats['downloaded']}")
        print(f"   ⏭️  Skipped:    {stats['skipped']}")
        print(f"   ❌ Failed:     {stats['failed']}")
        print(f"   📂 Location:   {os.path.abspath(download_dir)}")
        print(f"{'='*50}")

        return 1 if stats["failed"] > 0 else 0

    finally:
        await client.disconnect()


def cli():
    """Entry point: parse arguments, run main, and exit."""
    args = parse_args()
    exit_code = asyncio.run(main(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
