"""Tests for input resolver functionality."""

import time
from unittest.mock import patch

import pytest

from az_pim_cli.resolver import (
    InputResolver,
    Match,
    MatchStrategy,
    resolve_role,
    resolve_scope,
)


@pytest.fixture
def sample_candidates():
    """Sample candidates for testing."""
    return [
        {"id": "1", "name": "Owner"},
        {"id": "2", "name": "Contributor"},
        {"id": "3", "name": "Reader"},
        {"id": "4", "name": "Security Administrator"},
        {"id": "5", "name": "Security Reader"},
    ]


@pytest.fixture
def resolver_non_tty():
    """Resolver instance in non-TTY mode."""
    return InputResolver(
        fuzzy_enabled=True,
        fuzzy_threshold=0.8,
        cache_ttl_seconds=300,
        is_tty=False,
    )


@pytest.fixture
def resolver_tty():
    """Resolver instance in TTY mode."""
    return InputResolver(
        fuzzy_enabled=True,
        fuzzy_threshold=0.8,
        cache_ttl_seconds=300,
        is_tty=True,
    )


class TestExactMatching:
    """Test exact matching strategy."""

    def test_exact_match_success(self, resolver_non_tty, sample_candidates):
        """Test exact match returns correct candidate."""
        result = resolver_non_tty.resolve(
            user_input="Owner",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result == sample_candidates[0]

    def test_exact_match_with_spaces(self, resolver_non_tty, sample_candidates):
        """Test exact match with spaces in name."""
        result = resolver_non_tty.resolve(
            user_input="Security Administrator",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result == sample_candidates[3]

    def test_no_exact_match(self, resolver_non_tty, sample_candidates):
        """Test when no exact match exists."""
        # Should fall back to case-insensitive
        result = resolver_non_tty.resolve(
            user_input="owner",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result == sample_candidates[0]


class TestCaseInsensitiveMatching:
    """Test case-insensitive matching strategy."""

    def test_case_insensitive_match(self, resolver_non_tty, sample_candidates):
        """Test case-insensitive matching."""
        result = resolver_non_tty.resolve(
            user_input="OWNER",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result == sample_candidates[0]

    def test_mixed_case_match(self, resolver_non_tty, sample_candidates):
        """Test mixed case matching."""
        result = resolver_non_tty.resolve(
            user_input="CoNtRiBuToR",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result == sample_candidates[1]


class TestPrefixMatching:
    """Test prefix matching strategy."""

    def test_prefix_match_unique(self, resolver_non_tty, sample_candidates):
        """Test prefix match with unique result."""
        result = resolver_non_tty.resolve(
            user_input="Own",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result == sample_candidates[0]

    def test_prefix_match_case_insensitive(self, resolver_non_tty, sample_candidates):
        """Test prefix match is case-insensitive."""
        result = resolver_non_tty.resolve(
            user_input="read",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result == sample_candidates[2]

    def test_prefix_match_multiple_non_tty(self, resolver_non_tty, sample_candidates):
        """Test prefix match with multiple results in non-TTY mode."""
        # "Security" matches both "Security Administrator" and "Security Reader"
        result = resolver_non_tty.resolve(
            user_input="Security",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
            allow_interactive=False,
        )
        # Should return None and show error in non-TTY
        assert result is None


class TestFuzzyMatching:
    """Test fuzzy matching strategy."""

    def test_fuzzy_match_typo(self, resolver_non_tty, sample_candidates):
        """Test fuzzy match with typo."""
        result = resolver_non_tty.resolve(
            user_input="Ownar",  # Typo in "Owner"
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        # Should match "Owner" with high score
        assert result == sample_candidates[0]

    def test_fuzzy_match_below_threshold(self, resolver_non_tty, sample_candidates):
        """Test fuzzy match below threshold returns None."""
        result = resolver_non_tty.resolve(
            user_input="XYZ",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result is None

    def test_fuzzy_disabled(self, sample_candidates):
        """Test that fuzzy matching can be disabled."""
        resolver = InputResolver(fuzzy_enabled=False, is_tty=False)
        result = resolver.resolve(
            user_input="Ownar",  # Typo that would fuzzy-match
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result is None


class TestInteractiveMode:
    """Test interactive selection in TTY mode."""

    @patch("az_pim_cli.resolver.Prompt.ask")
    def test_interactive_multiple_matches(self, mock_prompt, resolver_tty, sample_candidates):
        """Test interactive selection with multiple matches."""
        # Simulate user selecting option 1
        mock_prompt.return_value = "1"

        result = resolver_tty.resolve(
            user_input="Security",  # Matches multiple
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        # Should return first matching candidate after user selection
        assert result in [sample_candidates[3], sample_candidates[4]]
        mock_prompt.assert_called_once()

    @patch("az_pim_cli.resolver.Prompt.ask")
    def test_interactive_user_selects_second(self, mock_prompt, resolver_tty, sample_candidates):
        """Test interactive selection when user picks second option."""
        mock_prompt.return_value = "2"

        result = resolver_tty.resolve(
            user_input="Security",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        # Should return based on user's choice
        assert result in [sample_candidates[3], sample_candidates[4]]

    @patch("az_pim_cli.resolver.Prompt.ask")
    def test_interactive_cancelled(self, mock_prompt, resolver_tty, sample_candidates):
        """Test interactive selection cancelled by user."""
        mock_prompt.side_effect = KeyboardInterrupt()

        result = resolver_tty.resolve(
            user_input="Security",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result is None


class TestCaching:
    """Test caching functionality."""

    def test_cache_stores_and_retrieves(self, resolver_non_tty):
        """Test cache stores and retrieves data."""
        test_data = {"key": "value"}
        resolver_non_tty.set_cache("test_key", test_data)

        retrieved = resolver_non_tty.get_cached("test_key")
        assert retrieved == test_data

    def test_cache_expiry(self, resolver_non_tty):
        """Test cache expiry after TTL."""
        # Create resolver with 1-second TTL
        resolver = InputResolver(cache_ttl_seconds=1, is_tty=False)

        test_data = {"key": "value"}
        resolver.set_cache("test_key", test_data)

        # Immediately should be available
        assert resolver.get_cached("test_key") == test_data

        # Wait for expiry
        time.sleep(1.1)

        # Should be expired
        assert resolver.get_cached("test_key") is None

    def test_cache_clear(self, resolver_non_tty):
        """Test cache clear."""
        resolver_non_tty.set_cache("key1", "value1")
        resolver_non_tty.set_cache("key2", "value2")

        resolver_non_tty.clear_cache()

        assert resolver_non_tty.get_cached("key1") is None
        assert resolver_non_tty.get_cached("key2") is None

    def test_cache_key_isolation(self, resolver_non_tty):
        """Test that different cache keys are isolated."""
        resolver_non_tty.set_cache("key1", "value1")
        resolver_non_tty.set_cache("key2", "value2")

        assert resolver_non_tty.get_cached("key1") == "value1"
        assert resolver_non_tty.get_cached("key2") == "value2"


class TestResolveRole:
    """Test resolve_role helper function."""

    def test_resolve_role_by_name(self, resolver_non_tty):
        """Test resolving role by name."""
        # Use dict-like objects instead of MagicMock to avoid name attribute confusion
        roles = [
            type("Role", (), {"id": "role-1", "name": "Owner"})(),
            type("Role", (), {"id": "role-2", "name": "Contributor"})(),
        ]

        def fetch_fn():
            return roles

        result = resolve_role(
            resolver=resolver_non_tty,
            role_input="Owner",
            scope="/subscriptions/123",
            fetch_roles_fn=fetch_fn,
            role_name_extractor=lambda r: r.name,
        )

        assert result == roles[0]
        assert result.id == "role-1"

    def test_resolve_role_by_number(self, resolver_non_tty):
        """Test resolving role by number."""
        roles = [
            type("Role", (), {"id": "role-1", "name": "Owner"})(),
            type("Role", (), {"id": "role-2", "name": "Contributor"})(),
        ]

        def fetch_fn():
            return roles

        result = resolve_role(
            resolver=resolver_non_tty,
            role_input="2",
            scope="/subscriptions/123",
            fetch_roles_fn=fetch_fn,
            role_name_extractor=lambda r: r.name,
        )

        assert result == roles[1]
        assert result.id == "role-2"

    def test_resolve_role_by_hash_number(self, resolver_non_tty):
        """Test resolving role by #N format."""
        roles = [
            type("Role", (), {"id": "role-1", "name": "Owner"})(),
            type("Role", (), {"id": "role-2", "name": "Contributor"})(),
        ]

        def fetch_fn():
            return roles

        result = resolve_role(
            resolver=resolver_non_tty,
            role_input="#1",
            scope="/subscriptions/123",
            fetch_roles_fn=fetch_fn,
            role_name_extractor=lambda r: r.name,
        )

        assert result == roles[0]

    def test_resolve_role_invalid_number(self, resolver_non_tty):
        """Test resolving role with invalid number."""
        roles = [type("Role", (), {"id": "role-1", "name": "Owner"})()]

        def fetch_fn():
            return roles

        result = resolve_role(
            resolver=resolver_non_tty,
            role_input="999",
            scope="/subscriptions/123",
            fetch_roles_fn=fetch_fn,
            role_name_extractor=lambda r: r.name,
        )

        assert result is None

    def test_resolve_role_uses_cache(self, resolver_non_tty):
        """Test that resolve_role uses caching."""
        roles = [type("Role", (), {"id": "role-1", "name": "Owner"})()]
        fetch_calls = []

        def fetch_fn():
            fetch_calls.append(1)
            return roles

        # First call
        resolve_role(
            resolver=resolver_non_tty,
            role_input="Owner",
            scope="/subscriptions/123",
            fetch_roles_fn=fetch_fn,
            role_name_extractor=lambda r: r.name,
        )

        # Second call with same scope
        resolve_role(
            resolver=resolver_non_tty,
            role_input="Owner",
            scope="/subscriptions/123",
            fetch_roles_fn=fetch_fn,
            role_name_extractor=lambda r: r.name,
        )

        # Fetch function should only be called once due to caching
        assert len(fetch_calls) == 1


class TestResolveScopeHelper:
    """Test resolve_scope helper function."""

    def test_resolve_full_path_passthrough(self, resolver_non_tty):
        """Test that full paths are passed through."""
        result = resolve_scope(
            resolver=resolver_non_tty,
            scope_input="/subscriptions/12345678-1234-1234-1234-123456789abc",
        )
        assert result == "/subscriptions/12345678-1234-1234-1234-123456789abc"

    def test_resolve_directory_scope(self, resolver_non_tty):
        """Test resolving directory scope."""
        result = resolve_scope(
            resolver=resolver_non_tty,
            scope_input="directory",
        )
        assert result == "/"

        result = resolve_scope(
            resolver=resolver_non_tty,
            scope_input="/",
        )
        assert result == "/"

    def test_resolve_resource_group_with_sub(self, resolver_non_tty):
        """Test resolving resource group name with subscription context."""
        result = resolve_scope(
            resolver=resolver_non_tty,
            scope_input="my-rg",
            subscription_id="12345678-1234-1234-1234-123456789abc",
        )
        expected = "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/my-rg"
        assert result == expected


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_input(self, resolver_non_tty, sample_candidates):
        """Test with empty input."""
        result = resolver_non_tty.resolve(
            user_input="",
            candidates=sample_candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result is None

    def test_empty_candidates(self, resolver_non_tty):
        """Test with empty candidates list."""
        result = resolver_non_tty.resolve(
            user_input="Owner",
            candidates=[],
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result is None

    def test_special_characters_in_input(self, resolver_non_tty):
        """Test with special characters in input."""
        candidates = [
            {"id": "1", "name": "Role-With-Dashes"},
            {"id": "2", "name": "Role_With_Underscores"},
        ]
        result = resolver_non_tty.resolve(
            user_input="Role-With-Dashes",
            candidates=candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result == candidates[0]

    def test_unicode_in_names(self, resolver_non_tty):
        """Test with Unicode characters in names."""
        candidates = [
            {"id": "1", "name": "Rôle spécial"},
            {"id": "2", "name": "Standard Role"},
        ]
        result = resolver_non_tty.resolve(
            user_input="Rôle spécial",
            candidates=candidates,
            name_extractor=lambda x: x["name"],
            context="role",
        )
        assert result == candidates[0]


class TestMatchStrategy:
    """Test Match dataclass and strategy tracking."""

    def test_match_object_creation(self):
        """Test Match object creation."""
        item = {"id": "1", "name": "Test"}
        match = Match(
            item=item,
            name="Test",
            strategy=MatchStrategy.EXACT,
            score=1.0,
        )
        assert match.item == item
        assert match.name == "Test"
        assert match.strategy == MatchStrategy.EXACT
        assert match.score == 1.0

    def test_match_strategies_enum(self):
        """Test MatchStrategy enum values."""
        assert MatchStrategy.EXACT.value == "exact"
        assert MatchStrategy.CASE_INSENSITIVE.value == "case_insensitive"
        assert MatchStrategy.PREFIX.value == "prefix"
        assert MatchStrategy.FUZZY.value == "fuzzy"
