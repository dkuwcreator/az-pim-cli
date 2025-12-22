"""PIM API providers for different backends."""

from az_pim_cli.providers.azure_arm import AzureARMProvider
from az_pim_cli.providers.entra_graph import EntraGraphProvider

__all__ = ["EntraGraphProvider", "AzureARMProvider"]
