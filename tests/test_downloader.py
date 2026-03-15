"""Tests for download engine module."""
from unittest.mock import MagicMock, patch

from src.media import MediaType


class TestCheckCryptg:
    """Tests for check_cryptg() function."""

    def test_returns_true_when_installed(self):
        """Returns True when cryptg can be imported."""
        with patch.dict("sys.modules", {"cryptg": MagicMock()}):
            from src.downloader import check_cryptg

            result = check_cryptg()
            assert result is True

    def test_returns_false_when_not_installed(self):
        """Returns False when cryptg import raises ImportError."""
        import sys

        # Ensure cryptg is not importable by temporarily removing it
        saved = sys.modules.pop("cryptg", None)
        try:
            with patch("builtins.__import__", side_effect=_make_import_raiser("cryptg")):
                from src.downloader import check_cryptg

                result = check_cryptg()
                assert result is False
        finally:
            if saved is not None:
                sys.modules["cryptg"] = saved


def _make_import_raiser(blocked_module):
    """Create an __import__ replacement that blocks a specific module."""
    real_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def _import(name, *args, **kwargs):
        if name == blocked_module:
            raise ImportError(f"No module named '{blocked_module}'")
        return real_import(name, *args, **kwargs)

    return _import


class TestFormatSize:
    """Tests for format_size() function."""

    def test_bytes(self):
        """500 bytes → '500.0 B'"""
        from src.downloader import format_size

        assert format_size(500) == "500.0 B"

    def test_kilobytes(self):
        """1536 bytes → '1.5 KB'"""
        from src.downloader import format_size

        assert format_size(1536) == "1.5 KB"

    def test_megabytes(self):
        """10 * 1024 * 1024 → '10.0 MB'"""
        from src.downloader import format_size

        assert format_size(10 * 1024 * 1024) == "10.0 MB"

    def test_gigabytes(self):
        """2.5 * 1024^3 → '2.5 GB'"""
        from src.downloader import format_size

        assert format_size(int(2.5 * 1024 * 1024 * 1024)) == "2.5 GB"

    def test_zero(self):
        """0 → '0.0 B'"""
        from src.downloader import format_size

        assert format_size(0) == "0.0 B"


class TestBuildMediaList:
    """Tests for build_media_list() function."""

    def _make_video_message(self):
        """Create a mock message classified as VIDEO."""
        msg = MagicMock()
        msg.photo = None
        msg.media = MagicMock()
        msg.media.document = MagicMock()
        msg.media.document.mime_type = "video/mp4"
        msg.media.document.size = 5_000_000
        attr = MagicMock()
        attr.file_name = "clip.mp4"
        msg.media.document.attributes = [attr]
        return msg

    def _make_photo_message(self):
        """Create a mock message classified as PHOTO."""
        msg = MagicMock()
        msg.photo = MagicMock()  # truthy → PHOTO
        msg.media = MagicMock()
        msg.media.document = None
        return msg

    def _make_empty_message(self):
        """Create a mock message with no media."""
        msg = MagicMock()
        msg.media = None
        msg.photo = None
        return msg

    def test_filters_by_media_type(self):
        """Only video messages returned when filter=['video']."""
        from src.downloader import build_media_list

        video_msg = self._make_video_message()
        photo_msg = self._make_photo_message()
        messages = [video_msg, photo_msg]

        result = build_media_list(messages, ["video"])

        assert len(result) == 1
        msg, media_type, ext, size = result[0]
        assert msg is video_msg
        assert media_type == MediaType.VIDEO

    def test_all_filter_includes_all_media(self):
        """Both video and photo returned when filter=['all']."""
        from src.downloader import build_media_list

        video_msg = self._make_video_message()
        photo_msg = self._make_photo_message()
        messages = [video_msg, photo_msg]

        result = build_media_list(messages, ["all"])

        assert len(result) == 2
        types = {item[1] for item in result}
        assert MediaType.VIDEO in types
        assert MediaType.PHOTO in types

    def test_empty_messages_returns_empty(self):
        """Empty message list → empty result."""
        from src.downloader import build_media_list

        result = build_media_list([], ["all"])
        assert result == []
