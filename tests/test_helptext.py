"""Tests for helptext module."""

from unittest.mock import patch

from az_pim_cli.helptext import (
    CHANGELOG_HIGHLIGHTS,
    TIPS_CONTENT,
    render_markdown,
    show_changelog_highlights,
    show_tips,
)


class TestRenderMarkdown:
    """Tests for render_markdown function."""

    @patch("az_pim_cli.helptext.console")
    def test_render_markdown_basic(self, mock_console):
        """Test rendering basic markdown."""
        content = "# Test\n\nThis is a test."
        render_markdown(content)

        # Should be called at least twice (markdown + newline)
        assert mock_console.print.call_count >= 2

    @patch("az_pim_cli.helptext.console")
    def test_render_markdown_with_title(self, mock_console):
        """Test rendering markdown with title."""
        content = "Test content"
        render_markdown(content, title="Test Title")

        # Should be called for title, markdown, and newline
        assert mock_console.print.call_count >= 3

    @patch("az_pim_cli.helptext.console")
    def test_render_markdown_empty(self, mock_console):
        """Test rendering empty markdown."""
        render_markdown("")

        # Should still be called for markdown + newline
        assert mock_console.print.call_count >= 2


class TestShowTips:
    """Tests for show_tips function."""

    @patch("az_pim_cli.helptext.console")
    def test_show_tips_renders_content(self, mock_console):
        """Test that show_tips renders the tips content."""
        show_tips()

        # Should call print multiple times
        assert mock_console.print.call_count >= 2

    def test_tips_content_not_empty(self):
        """Test that tips content is not empty."""
        assert TIPS_CONTENT
        assert len(TIPS_CONTENT) > 0
        assert "Tips" in TIPS_CONTENT or "tips" in TIPS_CONTENT


class TestShowChangelogHighlights:
    """Tests for show_changelog_highlights function."""

    @patch("az_pim_cli.helptext.console")
    def test_show_changelog_highlights_renders_content(self, mock_console):
        """Test that show_changelog_highlights renders the changelog."""
        show_changelog_highlights()

        # Should call print multiple times
        assert mock_console.print.call_count >= 2

    def test_changelog_content_not_empty(self):
        """Test that changelog content is not empty."""
        assert CHANGELOG_HIGHLIGHTS
        assert len(CHANGELOG_HIGHLIGHTS) > 0
        assert "Version" in CHANGELOG_HIGHLIGHTS or "version" in CHANGELOG_HIGHLIGHTS
