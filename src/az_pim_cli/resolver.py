"""Input resolution and matching utilities for Azure PIM CLI.

Provides intelligent matching for user inputs (scopes, roles, resource groups, etc.)
with support for exact, case-insensitive, prefix, and fuzzy matching strategies.
"""

import difflib
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from rich.console import Console
from rich.prompt import Prompt

# Optional fuzzy matching with rapidfuzz
try:
    from rapidfuzz import fuzz, process

    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


class MatchStrategy(Enum):
    """Matching strategy for input resolution."""

    EXACT = "exact"
    CASE_INSENSITIVE = "case_insensitive"
    PREFIX = "prefix"
    FUZZY = "fuzzy"


@dataclass
class Match:
    """A matched item with metadata."""

    item: Any
    name: str
    strategy: MatchStrategy
    score: float = 1.0


@dataclass
class CacheEntry:
    """Cached data with TTL."""

    data: Any
    timestamp: float


class InputResolver:
    """Resolve user inputs with intelligent matching and caching."""

    def __init__(
        self,
        fuzzy_enabled: bool = True,
        fuzzy_threshold: float = 0.8,
        cache_ttl_seconds: int = 300,
        is_tty: Optional[bool] = None,
    ):
        """
        Initialize input resolver.

        Args:
            fuzzy_enabled: Enable fuzzy matching
            fuzzy_threshold: Minimum similarity score (0-1) for fuzzy matches
            cache_ttl_seconds: Cache TTL in seconds
            is_tty: Override TTY detection (None = auto-detect)
        """
        self.fuzzy_enabled = fuzzy_enabled
        self.fuzzy_threshold = fuzzy_threshold
        self.cache_ttl_seconds = cache_ttl_seconds
        self.is_tty = is_tty if is_tty is not None else sys.stdout.isatty()
        self._cache: Dict[str, CacheEntry] = {}
        self.console = Console()

    def resolve(
        self,
        user_input: str,
        candidates: List[Any],
        name_extractor: Callable[[Any], str],
        context: str = "item",
        allow_interactive: bool = True,
        cache_key: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Resolve user input against candidate items.

        Args:
            user_input: User-provided input to match
            candidates: List of candidate items to match against
            name_extractor: Function to extract name/ID from candidate
            context: Context for error messages (e.g., "scope", "role")
            allow_interactive: Allow interactive selection in TTY mode
            cache_key: Optional cache key for candidates

        Returns:
            Matched item or None if no match found

        Raises:
            ValueError: If multiple matches found in non-interactive mode
        """
        if not candidates:
            self._show_error(f"No {context}s available to match against")
            return None

        if not user_input:
            self._show_error(f"{context.capitalize()} input is required")
            return None

        # Try matching strategies in order
        matches = self._find_matches(user_input, candidates, name_extractor)

        if not matches:
            self._show_no_match_error(user_input, candidates, name_extractor, context)
            return None

        if len(matches) == 1:
            match = matches[0]
            if match.strategy != MatchStrategy.EXACT:
                self._show_match_info(match, context)
            return match.item

        # Multiple matches - handle based on TTY mode
        return self._handle_multiple_matches(
            matches, user_input, context, allow_interactive
        )

    def _find_matches(
        self,
        user_input: str,
        candidates: List[Any],
        name_extractor: Callable[[Any], str],
    ) -> List[Match]:
        """Find all matching candidates using various strategies."""
        # Extract names once
        candidate_names = [(c, name_extractor(c)) for c in candidates]

        # 1. Exact match
        exact_matches = [
            Match(c, name, MatchStrategy.EXACT, 1.0)
            for c, name in candidate_names
            if name == user_input
        ]
        if exact_matches:
            return exact_matches

        # 2. Case-insensitive match
        user_lower = user_input.lower()
        ci_matches = [
            Match(c, name, MatchStrategy.CASE_INSENSITIVE, 0.95)
            for c, name in candidate_names
            if name.lower() == user_lower
        ]
        if ci_matches:
            return ci_matches

        # 3. Prefix match (case-insensitive)
        prefix_matches = [
            Match(c, name, MatchStrategy.PREFIX, 0.9)
            for c, name in candidate_names
            if name.lower().startswith(user_lower)
        ]
        if prefix_matches:
            return prefix_matches

        # 4. Fuzzy match (if enabled)
        if self.fuzzy_enabled:
            return self._fuzzy_match(user_input, candidate_names)

        return []

    def _fuzzy_match(
        self,
        user_input: str,
        candidate_names: List[Tuple[Any, str]],
    ) -> List[Match]:
        """Perform fuzzy matching using available library."""
        names = [name for _, name in candidate_names]
        name_to_candidate = {name: c for c, name in candidate_names}

        if HAS_RAPIDFUZZ:
            # Use rapidfuzz for better performance
            results = process.extract(
                user_input,
                names,
                scorer=fuzz.ratio,
                limit=None,
            )
            matches = [
                Match(
                    name_to_candidate[name],
                    name,
                    MatchStrategy.FUZZY,
                    score / 100.0,
                )
                for name, score, _ in results
                if score / 100.0 >= self.fuzzy_threshold
            ]
        else:
            # Fall back to difflib
            close_matches = difflib.get_close_matches(
                user_input,
                names,
                n=10,
                cutoff=self.fuzzy_threshold,
            )
            matches = [
                Match(
                    name_to_candidate[name],
                    name,
                    MatchStrategy.FUZZY,
                    difflib.SequenceMatcher(None, user_input, name).ratio(),
                )
                for name in close_matches
            ]

        # Sort by score descending
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches

    def _handle_multiple_matches(
        self,
        matches: List[Match],
        user_input: str,
        context: str,
        allow_interactive: bool,
    ) -> Optional[Any]:
        """Handle multiple matches based on TTY mode."""
        if self.is_tty and allow_interactive:
            return self._interactive_select(matches, context)
        else:
            self._show_multiple_matches_error(matches, user_input, context)
            return None

    def _interactive_select(self, matches: List[Match], context: str) -> Optional[Any]:
        """Show interactive selection prompt."""
        self.console.print(f"\n[yellow]Multiple {context}s match your input:[/yellow]")

        for i, match in enumerate(matches, 1):
            score_str = (
                f" [dim](score: {match.score:.0%})[/dim]"
                if match.strategy == MatchStrategy.FUZZY
                else ""
            )
            self.console.print(f"  [cyan]{i}.[/cyan] {match.name}{score_str}")

        try:
            choice = Prompt.ask(
                "\nSelect number",
                choices=[str(i) for i in range(1, len(matches) + 1)],
                default="1",
            )
            return matches[int(choice) - 1].item
        except (KeyboardInterrupt, EOFError):
            self.console.print("\n[yellow]Selection cancelled[/yellow]")
            return None

    def _show_match_info(self, match: Match, context: str) -> None:
        """Show information about a non-exact match."""
        strategy_msg = {
            MatchStrategy.CASE_INSENSITIVE: "case-insensitive match",
            MatchStrategy.PREFIX: "prefix match",
            MatchStrategy.FUZZY: f"fuzzy match (score: {match.score:.0%})",
        }
        msg = strategy_msg.get(match.strategy, "match")
        self.console.print(
            f"[dim]Using {context} '{match.name}' ({msg})[/dim]", style="dim"
        )

    def _show_no_match_error(
        self,
        user_input: str,
        candidates: List[Any],
        name_extractor: Callable[[Any], str],
        context: str,
    ) -> None:
        """Show error with suggestions when no match found."""
        self.console.print(f"[red]✗[/red] {context.capitalize()} '{user_input}' not found")

        # Show suggestions (top 3)
        suggestions = self._get_suggestions(user_input, candidates, name_extractor)
        if suggestions:
            self.console.print("\n[yellow]Did you mean:[/yellow]")
            for i, name in enumerate(suggestions, 1):
                self.console.print(f"  [cyan]{i}.[/cyan] {name}")

        self.console.print(
            f"\n[dim]Tip: Run 'az-pim list' to see all available {context}s[/dim]"
        )

    def _show_multiple_matches_error(
        self,
        matches: List[Match],
        user_input: str,
        context: str,
    ) -> None:
        """Show error for multiple matches in non-interactive mode."""
        self.console.print(
            f"[red]✗[/red] Multiple {context}s match '{user_input}' "
            f"(non-interactive mode)"
        )
        self.console.print("\n[yellow]Matching candidates:[/yellow]")
        for match in matches[:5]:  # Show top 5
            self.console.print(f"  • {match.name}")

        if len(matches) > 5:
            self.console.print(f"  [dim]...and {len(matches) - 5} more[/dim]")

        self.console.print(
            "\n[dim]Tip: Use exact name/ID or run in interactive mode[/dim]"
        )

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self.console.print(f"[red]✗[/red] {message}")

    def _get_suggestions(
        self,
        user_input: str,
        candidates: List[Any],
        name_extractor: Callable[[Any], str],
        max_suggestions: int = 3,
    ) -> List[str]:
        """Get suggested candidates for user input."""
        names = [name_extractor(c) for c in candidates]

        if HAS_RAPIDFUZZ:
            results = process.extract(
                user_input,
                names,
                scorer=fuzz.ratio,
                limit=max_suggestions,
            )
            return [name for name, _, _ in results]
        else:
            return difflib.get_close_matches(
                user_input,
                names,
                n=max_suggestions,
                cutoff=0.4,  # Lower threshold for suggestions
            )

    def get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() - entry.timestamp > self.cache_ttl_seconds:
            del self._cache[key]
            return None

        return entry.data

    def set_cache(self, key: str, data: Any) -> None:
        """Store data in cache."""
        self._cache[key] = CacheEntry(data=data, timestamp=time.time())

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()


# Helper functions for common use cases


def resolve_scope(
    resolver: InputResolver,
    scope_input: str,
    subscription_id: Optional[str] = None,
    fetch_scopes_fn: Optional[Callable[[], List[Any]]] = None,
) -> Optional[str]:
    """
    Resolve a scope identifier to a full scope path.

    Args:
        resolver: InputResolver instance
        scope_input: User-provided scope (name, ID, partial path)
        subscription_id: Current subscription ID for context
        fetch_scopes_fn: Optional function to fetch available scopes

    Returns:
        Resolved scope path or None
    """
    # If it looks like a full path, use it directly
    if scope_input.startswith("/subscriptions/") or scope_input.startswith("/providers/"):
        return scope_input

    # Special case: "directory" or "/"
    if scope_input.lower() in ("directory", "/"):
        return "/"

    # If we have a subscription context and input looks like a subscription name/ID
    if subscription_id and not fetch_scopes_fn:
        # Simple subscription-level scope
        if "/" not in scope_input:
            # Could be resource group or subscription name
            if len(scope_input) == 36 and "-" in scope_input:
                # Looks like a GUID
                return f"/subscriptions/{scope_input}"
            else:
                # Assume resource group within subscription
                return f"/subscriptions/{subscription_id}/resourceGroups/{scope_input}"

    # Use fetch function if provided
    if fetch_scopes_fn:
        cache_key = f"scopes_{subscription_id or 'all'}"
        scopes = resolver.get_cached(cache_key)

        if scopes is None:
            scopes = fetch_scopes_fn()
            resolver.set_cache(cache_key, scopes)

        def extract_scope_name(scope: Any) -> str:
            # Handle different scope formats
            if isinstance(scope, str):
                return scope
            if isinstance(scope, dict):
                return scope.get("name", scope.get("id", str(scope)))
            return str(scope)

        resolved = resolver.resolve(
            scope_input,
            scopes,
            extract_scope_name,
            context="scope",
            cache_key=cache_key,
        )

        if resolved:
            return extract_scope_name(resolved)

    return None


def resolve_role(
    resolver: InputResolver,
    role_input: str,
    scope: str,
    fetch_roles_fn: Callable[[], List[Any]],
    role_name_extractor: Callable[[Any], str],
) -> Optional[Any]:
    """
    Resolve a role identifier to a role object.

    Args:
        resolver: InputResolver instance
        role_input: User-provided role (name, ID, number)
        scope: Scope for role lookup
        fetch_roles_fn: Function to fetch eligible roles for scope
        role_name_extractor: Function to extract role name from role object

    Returns:
        Resolved role object or None
    """
    cache_key = f"roles_{scope}"
    roles = resolver.get_cached(cache_key)

    if roles is None:
        roles = fetch_roles_fn()
        resolver.set_cache(cache_key, roles)

    # Check if input is a list number (e.g., "1" or "#1")
    role_number = None
    if role_input.startswith("#"):
        try:
            role_number = int(role_input[1:])
        except ValueError:
            pass
    elif role_input.isdigit():
        try:
            role_number = int(role_input)
        except ValueError:
            pass

    if role_number is not None:
        if 1 <= role_number <= len(roles):
            return roles[role_number - 1]
        else:
            resolver.console.print(
                f"[red]✗[/red] Invalid role number {role_number} "
                f"(must be 1-{len(roles)})"
            )
            return None

    # Resolve by name/ID
    return resolver.resolve(
        role_input,
        roles,
        role_name_extractor,
        context="role",
        cache_key=cache_key,
    )
