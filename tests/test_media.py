"""Tests for media type detection and filtering module."""
from unittest.mock import MagicMock

from src.media import MediaType, classify_message, matches_filter, get_file_extension, get_file_size


class TestMediaType:
    """Tests for MediaType enum values."""

    def test_video_value(self):
        assert MediaType.VIDEO.value == "video"

    def test_photo_value(self):
        assert MediaType.PHOTO.value == "photo"

    def test_audio_value(self):
        assert MediaType.AUDIO.value == "audio"

    def test_document_value(self):
        assert MediaType.DOCUMENT.value == "document"


class TestClassifyMessage:
    """Tests for classify_message() function."""

    def _make_document_message(self, mime_type, attributes=None):
        """Create a mock Telethon message with a document media."""
        msg = MagicMock()
        msg.photo = None
        msg.media = MagicMock()
        msg.media.document = MagicMock()
        msg.media.document.mime_type = mime_type
        msg.media.document.size = 1024
        msg.media.document.attributes = attributes if attributes is not None else []
        return msg

    def _make_photo_message(self):
        """Create a mock Telethon message with a photo."""
        msg = MagicMock()
        msg.photo = MagicMock()  # truthy
        msg.media = MagicMock()
        msg.media.document = None
        return msg

    def _make_empty_message(self):
        """Create a mock Telethon message with no media."""
        msg = MagicMock()
        msg.media = None
        msg.photo = None
        return msg

    def test_photo_message_classified_as_photo(self):
        msg = self._make_photo_message()
        assert classify_message(msg) == MediaType.PHOTO

    def test_video_mime_classified_as_video(self):
        msg = self._make_document_message("video/mp4")
        assert classify_message(msg) == MediaType.VIDEO

    def test_audio_mime_classified_as_audio(self):
        msg = self._make_document_message("audio/mpeg")
        assert classify_message(msg) == MediaType.AUDIO

    def test_generic_document_classified_as_document(self):
        msg = self._make_document_message("application/pdf")
        assert classify_message(msg) == MediaType.DOCUMENT

    def test_no_media_returns_none(self):
        msg = self._make_empty_message()
        assert classify_message(msg) is None

    def test_video_webm_classified_as_video(self):
        msg = self._make_document_message("video/webm")
        assert classify_message(msg) == MediaType.VIDEO

    def test_audio_ogg_classified_as_audio(self):
        msg = self._make_document_message("audio/ogg")
        assert classify_message(msg) == MediaType.AUDIO

    def test_image_mime_with_document_classified_as_photo(self):
        msg = self._make_document_message("image/png")
        assert classify_message(msg) == MediaType.PHOTO


class TestMatchesFilter:
    """Tests for matches_filter() function."""

    def test_all_filter_matches_everything(self):
        assert matches_filter(MediaType.VIDEO, ["all"]) is True

    def test_specific_filter_matches(self):
        assert matches_filter(MediaType.VIDEO, ["video"]) is True

    def test_specific_filter_rejects(self):
        assert matches_filter(MediaType.AUDIO, ["video"]) is False

    def test_multi_filter_matches(self):
        assert matches_filter(MediaType.AUDIO, ["video", "audio"]) is True

    def test_none_media_type_never_matches(self):
        assert matches_filter(None, ["all"]) is False


class TestGetFileExtension:
    """Tests for get_file_extension() function."""

    def test_photo_returns_jpg(self):
        msg = MagicMock()
        assert get_file_extension(msg, MediaType.PHOTO) == ".jpg"

    def test_document_with_filename_attribute(self):
        """Uses original filename extension from document attributes."""
        msg = MagicMock()
        attr = MagicMock()
        attr.file_name = "report.pdf"
        msg.media.document.attributes = [attr]
        msg.media.document.mime_type = "application/pdf"
        assert get_file_extension(msg, MediaType.DOCUMENT) == ".pdf"

    def test_document_falls_back_to_mime_type(self):
        """Falls back to MIME subtype when no filename attribute."""
        msg = MagicMock()
        msg.media.document.attributes = []
        msg.media.document.mime_type = "video/mp4"
        assert get_file_extension(msg, MediaType.VIDEO) == ".mp4"

    def test_mime_mpeg_normalized_to_mp3(self):
        msg = MagicMock()
        msg.media.document.attributes = []
        msg.media.document.mime_type = "audio/mpeg"
        assert get_file_extension(msg, MediaType.AUDIO) == ".mp3"

    def test_mime_quicktime_normalized_to_mov(self):
        msg = MagicMock()
        msg.media.document.attributes = []
        msg.media.document.mime_type = "video/quicktime"
        assert get_file_extension(msg, MediaType.VIDEO) == ".mov"

    def test_mime_x_matroska_normalized_to_mkv(self):
        msg = MagicMock()
        msg.media.document.attributes = []
        msg.media.document.mime_type = "video/x-matroska"
        assert get_file_extension(msg, MediaType.VIDEO) == ".mkv"

    def test_mime_plain_normalized_to_txt(self):
        msg = MagicMock()
        msg.media.document.attributes = []
        msg.media.document.mime_type = "text/plain"
        assert get_file_extension(msg, MediaType.DOCUMENT) == ".txt"

    def test_mime_jpeg_normalized_to_jpg(self):
        msg = MagicMock()
        msg.media.document.attributes = []
        msg.media.document.mime_type = "image/jpeg"
        assert get_file_extension(msg, MediaType.PHOTO) == ".jpg"

    def test_filename_extension_normalized_to_lowercase(self):
        """Mixed-case extensions from filenames are lowercased."""
        msg = MagicMock()
        attr = MagicMock()
        attr.file_name = "Report.PDF"
        msg.media.document.attributes = [attr]
        msg.media.document.mime_type = "application/pdf"
        assert get_file_extension(msg, MediaType.DOCUMENT) == ".pdf"

    def test_default_extension_is_bin(self):
        """When no filename and no mime_type, returns .bin."""
        msg = MagicMock()
        msg.media.document.attributes = []
        msg.media.document.mime_type = None
        assert get_file_extension(msg, MediaType.DOCUMENT) == ".bin"


class TestGetFileSize:
    """Tests for get_file_size() function."""

    def test_photo_returns_zero(self):
        msg = MagicMock()
        assert get_file_size(msg, MediaType.PHOTO) == 0

    def test_document_returns_size(self):
        msg = MagicMock()
        msg.media.document.size = 5242880
        assert get_file_size(msg, MediaType.DOCUMENT) == 5242880

    def test_document_no_size_returns_zero(self):
        msg = MagicMock()
        msg.media.document.size = None
        assert get_file_size(msg, MediaType.DOCUMENT) == 0
