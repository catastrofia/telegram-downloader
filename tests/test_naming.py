"""Tests for file naming strategies module."""
from unittest.mock import MagicMock

from src.naming import NamingStrategy, sanitize_filename, generate_filename, get_original_filename


class TestNamingStrategyEnum:
    """Tests for NamingStrategy enum values."""

    def test_original_value(self):
        assert NamingStrategy.ORIGINAL.value == "original"

    def test_sequential_value(self):
        assert NamingStrategy.SEQUENTIAL.value == "sequential"

    def test_custom_value(self):
        assert NamingStrategy.CUSTOM.value == "custom"


class TestSanitizeFilename:
    """Tests for sanitize_filename() function."""

    def test_replaces_unsafe_characters(self):
        result = sanitize_filename('file<>:"/\\|?*name')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_strips_leading_trailing_dots_and_spaces(self):
        assert sanitize_filename("...file...") == "file"
        assert sanitize_filename("  file  ") == "file"
        assert sanitize_filename(". .file. .") == "file"

    def test_returns_unnamed_for_empty_result(self):
        assert sanitize_filename("") == "unnamed"
        assert sanitize_filename("...") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"

    def test_preserves_safe_characters(self):
        assert sanitize_filename("my_video-2024.mp4") == "my_video-2024.mp4"


class TestGenerateFilename:
    """Tests for generate_filename() function."""

    def test_sequential_default_padding(self):
        """index=5, ext='.mp4' → '005.mp4'"""
        result = generate_filename(NamingStrategy.SEQUENTIAL, index=5, extension=".mp4")
        assert result == "005.mp4"

    def test_sequential_custom_prefix(self):
        """prefix='Episode', index=12 → 'Episode_012.mp4'"""
        result = generate_filename(
            NamingStrategy.SEQUENTIAL, index=12, extension=".mp4", prefix="Episode"
        )
        assert result == "Episode_012.mp4"

    def test_sequential_custom_padding(self):
        """padding=5, index=3 → '00003.mkv'"""
        result = generate_filename(
            NamingStrategy.SEQUENTIAL, index=3, extension=".mkv", padding=5
        )
        assert result == "00003.mkv"

    def test_original_with_known_name(self):
        """original_name='my_video.mp4' → 'my_video.mp4'"""
        result = generate_filename(
            NamingStrategy.ORIGINAL, index=1, extension=".mp4", original_name="my_video.mp4"
        )
        assert result == "my_video.mp4"

    def test_original_fallback_to_sequential(self):
        """original_name=None, index=7 → '007.mp4'"""
        result = generate_filename(
            NamingStrategy.ORIGINAL, index=7, extension=".mp4", original_name=None
        )
        assert result == "007.mp4"

    def test_custom_pattern(self):
        """pattern='MyShow_CAP{n}', index=42 → 'MyShow_CAP042.mp4'"""
        result = generate_filename(
            NamingStrategy.CUSTOM, index=42, extension=".mp4", pattern="MyShow_CAP{n}"
        )
        assert result == "MyShow_CAP042.mp4"

    def test_custom_pattern_no_placeholder(self):
        """pattern='download', index=1 → 'download_001.mp4'"""
        result = generate_filename(
            NamingStrategy.CUSTOM, index=1, extension=".mp4", pattern="download"
        )
        assert result == "download_001.mp4"

    def test_sanitizes_unsafe_characters(self):
        """original_name with unsafe chars → all replaced with _"""
        result = generate_filename(
            NamingStrategy.ORIGINAL,
            index=1,
            extension=".mp4",
            original_name='my<video>:file|"test?.mp4',
        )
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "|" not in result
        assert '"' not in result
        assert "?" not in result


class TestGetOriginalFilename:
    """Tests for get_original_filename() function."""

    def test_extracts_filename_from_document_attributes(self):
        """Returns file_name from document attributes."""
        attr = MagicMock()
        attr.file_name = "original_video.mp4"
        msg = MagicMock()
        msg.media.document.attributes = [attr]
        assert get_original_filename(msg) == "original_video.mp4"

    def test_returns_none_when_no_file_name_attribute(self):
        """Returns None when attributes lack file_name."""
        attr = MagicMock(spec=[])  # no file_name attribute
        msg = MagicMock()
        msg.media.document.attributes = [attr]
        assert get_original_filename(msg) is None

    def test_returns_none_when_no_document(self):
        """Returns None when message has no document."""
        msg = MagicMock()
        msg.media.document = None
        assert get_original_filename(msg) is None

    def test_returns_none_when_no_media(self):
        """Returns None when message has no media."""
        msg = MagicMock()
        msg.media = None
        assert get_original_filename(msg) is None

    def test_returns_none_when_file_name_is_empty_string(self):
        """Returns None when file_name attribute is empty string."""
        attr = MagicMock()
        attr.file_name = ""
        msg = MagicMock()
        msg.media.document.attributes = [attr]
        assert get_original_filename(msg) is None
