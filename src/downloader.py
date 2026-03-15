"""Download engine with progress bars, media scanning, and file management."""
import os

from tqdm import tqdm

from src.media import MediaType, classify_message, matches_filter, get_file_extension, get_file_size
from src.naming import NamingStrategy, generate_filename, get_original_filename


# Type icon mapping for display functions.
_TYPE_ICONS = {
    MediaType.VIDEO: "🎬",
    MediaType.PHOTO: "🖼️",
    MediaType.AUDIO: "🎵",
    MediaType.DOCUMENT: "📄",
}


def check_cryptg() -> bool:
    """Check if cryptg (C-based crypto acceleration) is installed.

    Returns:
        True if cryptg is available, False otherwise.
    """
    try:
        import cryptg  # noqa: F401

        print("✅ cryptg (C-based crypto) is installed. Maximum speed potential.")
        return True
    except ImportError:
        print("⚠️ cryptg (C-based crypto) NOT found.")
        print("To maximize download speed, run: pip install cryptg")
        return False


def format_size(size_bytes: int) -> str:
    """Format a byte count as a human-readable string.

    Args:
        size_bytes: Number of bytes.

    Returns:
        Formatted string like ``"1.5 KB"`` or ``"10.0 MB"``.
    """
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024.0 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024.0
    # Unreachable, but satisfies type checkers.
    return f"{size:.1f} TB"


def build_media_list(messages, type_filter: list[str]) -> list[tuple]:
    """Scan messages and build a filtered list of media items.

    Args:
        messages: Iterable of Telethon Message objects.
        type_filter: List of type strings (e.g. ``["video"]``) or ``["all"]``.

    Returns:
        List of ``(message, media_type, extension, file_size)`` tuples.
    """
    result = []
    for message in messages:
        media_type = classify_message(message)
        if not matches_filter(media_type, type_filter):
            continue
        extension = get_file_extension(message, media_type)
        file_size = get_file_size(message, media_type)
        result.append((message, media_type, extension, file_size))
    return result


def print_scan_summary(media_list: list[tuple]) -> None:
    """Print a summary of scanned media grouped by type.

    Args:
        media_list: Output from :func:`build_media_list`.
    """
    if not media_list:
        print("No media found.")
        return

    counts: dict[MediaType, int] = {}
    total_size = 0
    for _, media_type, _, file_size in media_list:
        counts[media_type] = counts.get(media_type, 0) + 1
        total_size += file_size

    print(f"\n--- ✅ SCAN COMPLETE: {len(media_list)} files detected ---")
    for mtype, count in counts.items():
        icon = _TYPE_ICONS.get(mtype, "📦")
        print(f"  {icon} {mtype.value.capitalize()}: {count}")
    print(f"  📊 Total size: {format_size(total_size)}")


def print_file_listing(media_list: list[tuple]) -> None:
    """Print a numbered listing of media files.

    Args:
        media_list: Output from :func:`build_media_list`.
    """
    total = len(media_list)
    for i, (message, media_type, extension, file_size) in enumerate(media_list, start=1):
        icon = _TYPE_ICONS.get(media_type, "📦")
        caption = ""
        if hasattr(message, "message") and message.message:
            caption = message.message.strip()[:70].replace("\n", " ")
        size_str = format_size(file_size)
        print(
            f"  [{i}/{total}] {icon} {media_type.value.upper()} "
            f"| {extension} | {size_str} | {caption}"
        )


async def download_media_list(
    client,
    media_list: list[tuple],
    download_dir: str,
    naming_strategy: NamingStrategy,
    prefix: str = "",
    padding: int = 3,
    pattern: str | None = None,
) -> dict:
    """Download all media in the list with progress bars.

    Args:
        client: A connected Telethon client.
        media_list: Output from :func:`build_media_list`.
        download_dir: Directory to save files into.
        naming_strategy: How to name downloaded files.
        prefix: Prefix for sequential naming.
        padding: Zero-padding width for index numbers.
        pattern: Custom pattern string (for CUSTOM strategy).

    Returns:
        Stats dict with keys ``"downloaded"``, ``"skipped"``, ``"failed"``.
    """
    os.makedirs(download_dir, exist_ok=True)

    stats = {"downloaded": 0, "skipped": 0, "failed": 0}
    total = len(media_list)

    # Use nonlocal for progress callback instead of global.
    file_progress_bar = None

    def progress_callback(current_bytes, total_bytes):
        nonlocal file_progress_bar
        if file_progress_bar is not None:
            downloaded = current_bytes - file_progress_bar.n
            file_progress_bar.update(downloaded)

    with tqdm(total=total, desc="Queue", unit="file", position=0, leave=True) as queue_bar:
        for index, (message, media_type, extension, file_size) in enumerate(
            media_list, start=1
        ):
            original_name = get_original_filename(message)
            filename = generate_filename(
                strategy=naming_strategy,
                index=index,
                extension=extension,
                prefix=prefix,
                padding=padding,
                original_name=original_name,
                pattern=pattern,
            )
            full_path = os.path.join(download_dir, filename)

            if os.path.exists(full_path):
                stats["skipped"] += 1
                queue_bar.update(1)
                continue

            try:
                file_progress_bar = tqdm(
                    total=file_size,
                    desc=f"  {filename}",
                    unit="B",
                    unit_scale=True,
                    position=1,
                    leave=False,
                )

                await client.download_media(
                    message,
                    file=full_path,
                    progress_callback=progress_callback,
                )

                file_progress_bar.close()
                file_progress_bar = None
                stats["downloaded"] += 1
                queue_bar.update(1)

            except Exception as exc:
                if file_progress_bar is not None:
                    file_progress_bar.close()
                    file_progress_bar = None
                stats["failed"] += 1
                queue_bar.update(1)
                print(f"\n  ❌ Error downloading {filename}: {exc}")

    return stats
