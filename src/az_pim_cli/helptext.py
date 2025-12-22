"""Markdown-based help and documentation for az-pim-cli.

This module provides helpers for rendering Markdown content as rich terminal output
for extended help, tips, and documentation without cluttering --help.

Reference:
- https://rich.readthedocs.io/en/stable/markdown.html
"""

from rich.markdown import Markdown

from az_pim_cli.console import console


def render_markdown(content: str, *, title: str | None = None) -> None:
    """
    Render Markdown content to the console.

    Args:
        content: Markdown content to render
        title: Optional title to display before the content
    """
    if title:
        console.print(f"\n[bold cyan]{title}[/bold cyan]\n")

    md = Markdown(content)
    console.print(md)
    console.print()


# Tips and best practices
TIPS_CONTENT = """
# Azure PIM CLI Tips & Best Practices

## Quick Start

### List Your Roles
```bash
# List Azure AD roles
az-pim list

# List resource roles for your subscription
az-pim list --resource

# Interactive selection
az-pim list --select
```

### Activate a Role
```bash
# Activate by name
az-pim activate "Owner" --duration 4 --justification "Production deployment"

# Activate by number (from list)
az-pim activate 1 --duration 2

# Interactive mode (guided prompts)
az-pim activate --interactive
```

## Using Aliases

Create shortcuts for frequently used roles:

```bash
# Add an alias
az-pim alias add prod-admin "Owner" \\
  --duration "PT4H" \\
  --justification "Production access" \\
  --scope subscription

# Use the alias
az-pim activate prod-admin
```

## Interactive Mode

Use `--interactive` or `-i` for guided prompts:

```bash
# Guided activation with validation
az-pim activate --interactive

# Works in TTY automatically, or force with flag
az-pim activate "Owner" -i
```

## Configuration

Edit `~/.az-pim-cli/config.yml` to set defaults:

```yaml
defaults:
  duration: "PT8H"
  justification: "Requested via az-pim-cli"
  fuzzy_matching: true
  fuzzy_threshold: 0.8
```

## Troubleshooting

### DNS Issues
If you see network errors:
```bash
export AZ_PIM_IPV4_ONLY=1
az-pim list
```

### Authentication
Refresh your Azure CLI login:
```bash
az login
az account show
```

### Verbose Output
For debugging:
```bash
az-pim list --verbose
az-pim whoami --verbose
```

## Pro Tips

1. **Use numbers for quick activation**: `az-pim activate 1`
2. **Set up aliases** for common roles
3. **Use `--select`** in list command for interactive selection
4. **Keep config updated** with your preferences
5. **Check history** regularly: `az-pim history`

For more information, see the README or use `az-pim [command] --help`.
"""


CHANGELOG_HIGHLIGHTS = """
# Recent Changes

## Version 0.1.0

### New Features
- ✨ **Rich UI**: Beautiful terminal output with colors, tables, and panels
- 🎯 **Interactive Mode**: Guided prompts with `--interactive/-i` flag
- 📊 **Progress Indicators**: Status spinners and progress bars for long operations
- 🎨 **Enhanced Tables**: Consistent, readable table formatting
- 📝 **Smart Prompts**: Input validation and helpful error messages
- 🔍 **Fuzzy Matching**: Intelligent role name matching
- ⚡ **Aliases**: Quick shortcuts for common roles

### Improvements
- Better error messages with suggestions
- Auto-wrapping text to terminal width
- Clean logs for CI/CD (transient progress bars)
- Backward-compatible: existing scripts work unchanged

For complete changelog, see CHANGELOG.md
"""


def show_tips() -> None:
    """Display tips and best practices."""
    render_markdown(TIPS_CONTENT, title="💡 Tips & Best Practices")


def show_changelog_highlights() -> None:
    """Display recent changelog highlights."""
    render_markdown(CHANGELOG_HIGHLIGHTS, title="📋 Recent Changes")
