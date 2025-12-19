"""Response normalization for Azure PIM CLI.

DEPRECATION NOTICE:
    This module provides backward compatibility. New code should import from
    az_pim_cli.domain.models instead.

This module provides a mapping layer to normalize ARM and Graph API responses
into a common role model, keeping UI logic stable when switching backends.
"""

# Import from domain layer for backward compatibility
from az_pim_cli.domain.models import (  # noqa: F401
    SUBSCRIPTION_ID_DISPLAY_LENGTH,
    NormalizedRole,
    RoleSource,
    alias_to_normalized_role,
    normalize_arm_role,
    normalize_graph_role,
    normalize_roles,
)

__all__ = [
    "SUBSCRIPTION_ID_DISPLAY_LENGTH",
    "RoleSource",
    "NormalizedRole",
    "normalize_arm_role",
    "normalize_graph_role",
    "normalize_roles",
    "alias_to_normalized_role",
]
