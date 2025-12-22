"""Tests for console module."""

from unittest.mock import patch

from rich.console import Console

from az_pim_cli.console import console, install_traceback


class TestConsole:
    """Tests for shared console instance."""

    def test_console_is_console_instance(self):
        """Test that console is a Rich Console instance."""
        assert isinstance(console, Console)

    def test_console_is_singleton(self):
        """Test that multiple imports get the same console instance."""
        from az_pim_cli.console import console as console2

        assert console is console2


class TestInstallTraceback:
    """Tests for install_traceback function."""

    @patch("az_pim_cli.console.install_rich_traceback")
    def test_install_traceback_default(self, mock_install):
        """Test install_traceback with default parameters."""
        install_traceback()

        mock_install.assert_called_once()
        call_kwargs = mock_install.call_args[1]
        assert call_kwargs["show_locals"] is False
        assert "width" in call_kwargs
        assert "extra_lines" in call_kwargs
        assert "theme" in call_kwargs
        assert "word_wrap" in call_kwargs
        assert "suppress" in call_kwargs

    @patch("az_pim_cli.console.install_rich_traceback")
    def test_install_traceback_with_locals(self, mock_install):
        """Test install_traceback with show_locals=True."""
        install_traceback(show_locals=True)

        mock_install.assert_called_once()
        call_kwargs = mock_install.call_args[1]
        assert call_kwargs["show_locals"] is True

    @patch("az_pim_cli.console.install_rich_traceback")
    def test_install_traceback_suppresses_frameworks(self, mock_install):
        """Test that framework internals are suppressed in tracebacks."""
        install_traceback()

        mock_install.assert_called_once()
        call_kwargs = mock_install.call_args[1]
        assert "typer" in call_kwargs["suppress"]
        assert "click" in call_kwargs["suppress"]
