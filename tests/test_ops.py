"""Tests for progress and status operations."""

from unittest.mock import MagicMock, patch

from rich.progress import Progress

from az_pim_cli.ops import progress_bar, show_progress, status


class TestStatus:
    """Tests for status context manager."""

    @patch("az_pim_cli.ops.console")
    def test_status_default_spinner(self, mock_console):
        """Test status with default spinner."""
        mock_context = MagicMock()
        mock_console.status.return_value.__enter__ = MagicMock(return_value=mock_context)
        mock_console.status.return_value.__exit__ = MagicMock(return_value=None)

        with status("Test message"):
            pass

        mock_console.status.assert_called_once()
        call_args = mock_console.status.call_args
        assert "Test message" in call_args[0][0]
        assert call_args[1]["spinner"] == "dots"

    @patch("az_pim_cli.ops.console")
    def test_status_custom_spinner(self, mock_console):
        """Test status with custom spinner."""
        mock_context = MagicMock()
        mock_console.status.return_value.__enter__ = MagicMock(return_value=mock_context)
        mock_console.status.return_value.__exit__ = MagicMock(return_value=None)

        with status("Test message", spinner="arc"):
            pass

        mock_console.status.assert_called_once()
        call_args = mock_console.status.call_args
        assert call_args[1]["spinner"] == "arc"


class TestProgressBar:
    """Tests for progress_bar context manager."""

    def test_progress_bar_returns_progress_instance(self):
        """Test that progress_bar returns a Progress instance."""
        with progress_bar() as prog:
            assert isinstance(prog, Progress)

    def test_progress_bar_with_description(self):
        """Test progress_bar with description."""
        with progress_bar(description="Test operation") as prog:
            assert isinstance(prog, Progress)

    def test_progress_bar_can_add_task(self):
        """Test that tasks can be added to progress bar."""
        with progress_bar() as prog:
            task = prog.add_task("Test task", total=10)
            assert task is not None


class TestShowProgress:
    """Tests for show_progress helper."""

    def test_show_progress_yields_all_items(self):
        """Test that show_progress yields all items."""
        items = [1, 2, 3, 4, 5]
        result = list(show_progress(items, "Testing"))
        assert result == items

    def test_show_progress_empty_list(self):
        """Test show_progress with empty list."""
        items = []
        result = list(show_progress(items, "Testing"))
        assert result == []

    def test_show_progress_custom_description(self):
        """Test show_progress with custom description."""
        items = [1, 2, 3]
        result = list(show_progress(items, "Custom description"))
        assert result == items
