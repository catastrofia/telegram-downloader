"""Media type detection and filtering for Telegram messages."""
from enum import Enum


class MediaType(Enum):
    """Supported media types for Telegram message classification."""

    VIDEO = "video"
    PHOTO = "photo"
    AUDIO = "audio"
    DOCUMENT = "document"


# MIME subtype normalization map for common formats.
_MIME_NORMALIZE = {
    "mpeg": "mp3",
    "quicktime": "mov",
    "x-matroska": "mkv",
    "plain": "txt",
    "jpeg": "jpg",
}


def classify_message(message) -> MediaType | None:
    """Classify a Telethon message by its media type.

    Args:
        message: A Telethon Message object.

    Returns:
        A MediaType value, or None if the message has no recognizable media.
    """
    if not message.media:
        return None

    if message.photo:
        return MediaType.PHOTO

    document = getattr(message.media, "document", None)
    if document is None:
        return None

    mime_type = getattr(document, "mime_type", "") or ""
    if mime_type.startswith("video/"):
        return MediaType.VIDEO
    if mime_type.startswith("audio/"):
        return MediaType.AUDIO
    if mime_type.startswith("image/"):
        return MediaType.PHOTO
    return MediaType.DOCUMENT


def matches_filter(media_type: MediaType | None, type_filter: list[str]) -> bool:
    """Check if a media type passes a filter list.

    Args:
        media_type: The classified MediaType, or None.
        type_filter: List of allowed type strings (e.g. ["video", "audio"])
                     or ["all"] to accept everything.

    Returns:
        True if the media type is accepted by the filter.
    """
    if media_type is None:
        return False
    if "all" in type_filter:
        return True
    return media_type.value in type_filter


def get_file_extension(message, media_type: MediaType | None) -> str:
    """Determine the file extension for a message's media.

    Args:
        message: A Telethon Message object.
        media_type: The classified MediaType.

    Returns:
        A file extension string including the leading dot (e.g. ".mp4").
    """
    if media_type == MediaType.PHOTO:
        return ".jpg"

    # Try original filename from document attributes first.
    document = getattr(getattr(message, "media", None), "document", None)
    if document is not None:
        for attr in getattr(document, "attributes", []):
            file_name = getattr(attr, "file_name", None)
            if file_name and "." in file_name:
                return "." + file_name.rsplit(".", 1)[-1].lower()

        # Fall back to MIME type.
        mime_type = getattr(document, "mime_type", None)
        if mime_type and "/" in mime_type:
            subtype = mime_type.split("/", 1)[1]
            subtype = _MIME_NORMALIZE.get(subtype, subtype)
            return f".{subtype}"

    return ".bin"


def get_file_size(message, media_type: MediaType | None) -> int:
    """Get the file size in bytes for a message's media.

    Args:
        message: A Telethon Message object.
        media_type: The classified MediaType.

    Returns:
        File size in bytes, or 0 if not available.
    """
    if media_type == MediaType.PHOTO:
        return 0

    document = getattr(getattr(message, "media", None), "document", None)
    if document is not None:
        return getattr(document, "size", 0) or 0

    return 0
