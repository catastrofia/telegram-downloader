"""File naming strategies for downloaded media.

Provides flexible naming: original filenames, sequential numbering,
or custom patterns with index placeholders.
"""
from enum import Enum
import re


class NamingStrategy(Enum):
    """Available file naming strategies."""

    ORIGINAL = "original"
    SEQUENTIAL = "sequential"
    CUSTOM = "custom"


def sanitize_filename(name: str) -> str:
    """Remove or replace characters unsafe for filenames.

    Replaces characters matching ``[<>:"/\\|?*\\x00-\\x1f]`` with ``_``,
    strips leading/trailing dots and spaces, and returns ``"unnamed"``
    when the result would be empty.
    """
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    cleaned = cleaned.strip(". ")
    return cleaned if cleaned else "unnamed"


def generate_filename(
    strategy: NamingStrategy,
    index: int,
    extension: str,
    prefix: str = "",
    padding: int = 3,
    original_name: str | None = None,
    pattern: str | None = None,
) -> str:
    """Generate a filename according to the chosen strategy.

    Parameters
    ----------
    strategy:
        Which naming strategy to apply.
    index:
        Numeric index of the file (used for sequential/custom).
    extension:
        File extension including the leading dot (e.g. ``".mp4"``).
    prefix:
        Optional prefix for sequential naming.
    padding:
        Zero-padding width for the index number.
    original_name:
        The original filename from the message (used by ORIGINAL strategy).
    pattern:
        A pattern string for CUSTOM strategy.  Use ``{n}`` as a placeholder
        for the padded index.
    """
    padded = str(index).zfill(padding)

    if strategy == NamingStrategy.SEQUENTIAL:
        if prefix:
            raw = f"{prefix}_{padded}{extension}"
        else:
            raw = f"{padded}{extension}"

    elif strategy == NamingStrategy.ORIGINAL:
        if original_name is not None:
            raw = original_name
        else:
            # Fall back to sequential when no original name available
            raw = f"{padded}{extension}"

    elif strategy == NamingStrategy.CUSTOM:
        if pattern and "{n}" in pattern:
            raw = pattern.replace("{n}", padded) + extension
        elif pattern:
            raw = f"{pattern}_{padded}{extension}"
        else:
            raw = f"{padded}{extension}"

    else:
        raw = f"{padded}{extension}"

    return sanitize_filename(raw)


def get_original_filename(message) -> str | None:
    """Extract the original filename from a Telethon message.

    Inspects ``message.media.document.attributes`` for an attribute
    with a ``file_name`` field.  Returns ``None`` if not found.
    """
    try:
        if message.media is None:
            return None
        if message.media.document is None:
            return None
        for attr in message.media.document.attributes:
            if hasattr(attr, "file_name") and attr.file_name:
                return attr.file_name
    except (AttributeError, TypeError):
        return None
    return None
