"""Tests for CLI commands."""

from typer.testing import CliRunner

from az_pim_cli.cli import app

runner = CliRunner()


def test_version_command() -> None:
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "az-pim-cli" in result.stdout
    assert "0.1.0" in result.stdout


def test_whoami_command(monkeypatch) -> None:
    """Test whoami command."""
    import az_pim_cli.cli as cli

    class FakeAuth:
        def get_tenant_id(self) -> str:
            return "test-tenant-id"

        def get_user_object_id(self) -> str:
            return "test-user-id"

        def get_subscription_id(self) -> str:
            return "test-subscription-id"

        def get_token(self, scope: str) -> str:
            return "fake-token"

    monkeypatch.setattr(cli, "AzureAuth", FakeAuth)

    result = runner.invoke(app, ["whoami"])
    assert result.exit_code == 0
    assert "test-tenant-id" in result.stdout
    assert "test-user-id" in result.stdout
    assert "test-subscription-id" in result.stdout


def test_whoami_command_verbose(monkeypatch) -> None:
    """Test whoami command with verbose flag."""
    import az_pim_cli.cli as cli

    class FakeAuth:
        def get_tenant_id(self) -> str:
            return "test-tenant-id"

        def get_user_object_id(self) -> str:
            return "test-user-id"

        def get_subscription_id(self) -> str:
            return "test-subscription-id"

        def get_token(self, scope: str) -> str:
            return "fake-token"

    monkeypatch.setattr(cli, "AzureAuth", FakeAuth)

    result = runner.invoke(app, ["whoami", "--verbose"])
    assert result.exit_code == 0
    assert "test-tenant-id" in result.stdout
    assert "Token Validation" in result.stdout or "token available" in result.stdout


def test_whoami_command_auth_error(monkeypatch) -> None:
    """Test whoami command with authentication initialization error."""
    import az_pim_cli.cli as cli
    from az_pim_cli.exceptions import AuthenticationError

    class FakeAuth:
        def __init__(self):
            raise AuthenticationError("Auth failed", suggestion="Run az login")

    monkeypatch.setattr(cli, "AzureAuth", FakeAuth)

    result = runner.invoke(app, ["whoami"])
    assert result.exit_code == 1
    assert "Authentication failed" in result.stdout


def test_whoami_command_partial_failure(monkeypatch) -> None:
    """Test whoami command with partial failures."""
    import az_pim_cli.cli as cli

    class FakeAuth:
        def get_tenant_id(self) -> str:
            return "test-tenant-id"

        def get_user_object_id(self) -> str:
            return "test-user-id"

        def get_subscription_id(self) -> str:
            raise RuntimeError("No subscription")

        def get_token(self, scope: str) -> str:
            return "fake-token"

    monkeypatch.setattr(cli, "AzureAuth", FakeAuth)

    result = runner.invoke(app, ["whoami"])
    assert result.exit_code == 0
    assert "test-tenant-id" in result.stdout
    assert "test-user-id" in result.stdout
    assert "Not available" in result.stdout or "No subscription" in result.stdout


def test_alias_list_command() -> None:
    """Test alias list command."""
    result = runner.invoke(app, ["alias", "list"])
    # Should succeed even with no aliases
    assert result.exit_code == 0


def test_help_command() -> None:
    """Test help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Azure PIM CLI" in result.stdout


def test_list_help_shows_select_option() -> None:
    """Test that list help shows the --select option."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0
    # Check without colors (strip ANSI codes)
    assert "select" in result.stdout.lower()
    assert "interactive" in result.stdout.lower() or "activate a role" in result.stdout.lower()


def test_activate_help_shows_number_format() -> None:
    """Test that activate help shows role number format."""
    result = runner.invoke(app, ["activate", "--help"])
    assert result.exit_code == 0
    assert "number from list" in result.stdout.lower() or "#n" in result.stdout.lower()


def test_alias_list_shows_description_column() -> None:
    """Test that alias list command shows description column."""
    result = runner.invoke(app, ["alias", "list"])
    assert result.exit_code == 0
    # Check that the Description column is present in the output
    # (should appear even if no aliases are configured)
    assert "Description" in result.stdout or "No aliases configured" in result.stdout


def test_activate_alias_missing_role_non_tty(monkeypatch) -> None:
    """Missing alias role errors without prompting when not a TTY."""
    import types

    import az_pim_cli.cli as cli

    class FakeConfig:
        def __init__(self) -> None:
            pass

        def get_alias(self, name: str):
            if name == "alias-missing-role":
                return {"scope": "directory"}
            return None

        def get_default(self, key: str):
            return None

    class FakeAuth:
        def __init__(self) -> None:
            pass

        def get_subscription_id(self) -> str:
            return "sub-id"

    class FakeClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

    monkeypatch.setattr(cli, "Config", FakeConfig)
    monkeypatch.setattr(cli, "AzureAuth", FakeAuth)
    monkeypatch.setattr(cli, "PIMClient", FakeClient)
    monkeypatch.setattr(
        cli, "sys", types.SimpleNamespace(stdin=types.SimpleNamespace(isatty=lambda: False))
    )

    result = runner.invoke(cli.app, ["activate", "alias-missing-role"])
    assert result.exit_code != 0
    assert "Role name or ID is required" in result.stdout


def test_activate_prompts_defaults_when_tty(monkeypatch) -> None:
    """Interactive mode prompts for duration/justification and applies defaults."""
    import types

    import az_pim_cli.cli as cli

    captured = {}

    class FakeConfig:
        def __init__(self) -> None:
            pass

        def get_alias(self, _name: str):
            return None

        def get_default(self, key: str):
            if key == "duration":
                return "PT4H"
            if key == "justification":
                return "Default just"
            return None

    class FakeAuth:
        def __init__(self) -> None:
            pass

        def get_subscription_id(self) -> str:
            return "sub-id"

    class FakeClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def request_role_activation(
            self,
            role_definition_id: str,
            duration: str,
            justification: str,
            ticket_number,
            ticket_system,
        ):
            captured["payload"] = {
                "role_definition_id": role_definition_id,
                "duration": duration,
                "justification": justification,
                "ticket_number": ticket_number,
                "ticket_system": ticket_system,
            }
            return {"id": "req-123"}

    monkeypatch.setattr(cli, "Config", FakeConfig)
    monkeypatch.setattr(cli, "AzureAuth", FakeAuth)
    monkeypatch.setattr(cli, "PIMClient", FakeClient)
    monkeypatch.setattr(
        cli, "sys", types.SimpleNamespace(stdin=types.SimpleNamespace(isatty=lambda: True))
    )

    result = runner.invoke(
        cli.app, ["activate", "62e90394-69f5-4237-9190-012177145e10", "--interactive"], input="\n\n"
    )
    assert result.exit_code == 0
    assert captured["payload"]["duration"] == "PT4H"
    assert captured["payload"]["justification"] == "Default just"


def test_activate_no_role_non_tty_errors(monkeypatch) -> None:
    """Activation without a role should error in non-interactive mode."""
    import types

    import az_pim_cli.cli as cli

    class FakeConfig:
        def __init__(self) -> None:
            pass

        def get_alias(self, _name: str):
            return None

        def get_default(self, _key: str):
            return None

        def list_aliases(self):
            return {}

    class FakeAuth:
        def __init__(self) -> None:
            pass

        def get_subscription_id(self) -> str:
            return "sub-id"

    class FakeClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def list_role_assignments(self):
            return []

    monkeypatch.setattr(cli, "Config", FakeConfig)
    monkeypatch.setattr(cli, "AzureAuth", FakeAuth)
    monkeypatch.setattr(cli, "PIMClient", FakeClient)
    monkeypatch.setattr(
        cli,
        "sys",
        types.SimpleNamespace(stdin=types.SimpleNamespace(isatty=lambda: False)),
    )

    result = runner.invoke(cli.app, ["activate"])
    assert result.exit_code != 0
    assert "Role name or ID is required" in result.stdout


def test_activate_no_role_interactive_search(monkeypatch) -> None:
    """Interactive no-arg activation searches with fuzzy support and activates."""
    import types

    import az_pim_cli.cli as cli
    from az_pim_cli.domain.models import NormalizedRole, RoleSource

    captured = {}

    class FakeConfig:
        def __init__(self) -> None:
            pass

        def get_alias(self, _name: str):
            return None

        def get_default(self, key: str, fallback=None):
            if key == "duration":
                return "PT1H"
            if key == "justification":
                return "Default just"
            # Support resolver config
            if key == "fuzzy_matching":
                return True
            if key == "fuzzy_threshold":
                return 0.8
            if key == "cache_ttl_seconds":
                return 300
            return fallback if fallback is not None else None

        def list_aliases(self):
            return {}

    class FakeAuth:
        def __init__(self) -> None:
            pass

        def get_subscription_id(self) -> str:
            return "sub-id"

    class FakeClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def list_role_assignments(self):
            return ["dummy"]

        def request_role_activation(
            self,
            role_definition_id: str,
            duration: str,
            justification: str,
            ticket_number,
            ticket_system,
        ):
            captured["payload"] = {
                "role_definition_id": role_definition_id,
                "duration": duration,
                "justification": justification,
                "ticket_number": ticket_number,
                "ticket_system": ticket_system,
            }
            return {"id": "req-xyz"}

    def fake_normalize(_data, source=None) -> list[NormalizedRole]:
        return [
            NormalizedRole(
                name="Owner",
                id="role-id",
                status="Active",
                scope="/",
                source=RoleSource.ARM,
                is_alias=False,
            )
        ]

    monkeypatch.setattr(cli, "Config", FakeConfig)
    monkeypatch.setattr(cli, "AzureAuth", FakeAuth)
    monkeypatch.setattr(cli, "PIMClient", FakeClient)
    monkeypatch.setattr(cli, "normalize_roles", fake_normalize)
    monkeypatch.setattr(
        cli,
        "sys",
        types.SimpleNamespace(
            stdin=types.SimpleNamespace(isatty=lambda: True),
            stdout=types.SimpleNamespace(isatty=lambda: True),
        ),
    )

    result = runner.invoke(cli.app, ["activate", "--interactive"], input="Owner\n1\n\n\n")
    assert result.exit_code == 0
    assert captured["payload"]["role_definition_id"] == "role-id"
    assert captured["payload"]["duration"] == "PT1H"
    assert captured["payload"]["justification"] == "Default just"


def test_activate_help_shows_interactive_flag() -> None:
    """Test that activate help shows interactive flag."""
    result = runner.invoke(app, ["activate", "--help"])
    assert result.exit_code == 0
    assert "--interactive" in result.stdout or "-i" in result.stdout
    assert "interactive mode" in result.stdout.lower() or "guided prompts" in result.stdout.lower()


def test_tips_command() -> None:
    """Test tips command."""
    result = runner.invoke(app, ["tips"])
    assert result.exit_code == 0
    assert "Tips" in result.stdout or "tips" in result.stdout


def test_changelog_command() -> None:
    """Test changelog command."""
    result = runner.invoke(app, ["changelog"])
    assert result.exit_code == 0
    assert "Version" in result.stdout or "version" in result.stdout or "Changes" in result.stdout
