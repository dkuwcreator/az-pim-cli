"""Tests for dashboard module."""

from unittest.mock import patch

import pytest

from az_pim_cli.dashboard import check_textual_available, run_dashboard


class TestCheckTextualAvailable:
    """Tests for check_textual_available function."""

    def test_check_textual_available_returns_bool(self):
        """Test that check_textual_available returns a boolean."""
        result = check_textual_available()
        assert isinstance(result, bool)


class TestRunDashboard:
    """Tests for run_dashboard function."""

    @patch("az_pim_cli.dashboard.check_textual_available")
    def test_run_dashboard_without_textual(self, mock_check):
        """Test that run_dashboard raises ImportError when textual is not available."""
        mock_check.return_value = False

        with pytest.raises(ImportError, match="textual package not found"):
            run_dashboard()

