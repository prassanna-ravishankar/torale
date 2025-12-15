"""
Backwards compatibility shim for ClerkUser.

DEPRECATED: This module exists only for backwards compatibility.
New code should import User from torale.api.auth_provider instead.

All Clerk-specific logic has been moved to ProductionAuthProvider.
"""

from torale.api.auth_provider import ProductionAuthProvider, User, get_auth_provider

# Backwards compatibility alias
ClerkUser = User


def get_clerk_client():
    """
    Get the Clerk client from ProductionAuthProvider.

    Returns None if using NoAuthProvider or if Clerk is not configured.
    """
    provider = get_auth_provider()
    if isinstance(provider, ProductionAuthProvider):
        return provider.clerk_client
    return None


# Lazy property for backwards compatibility
# This allows `from torale.api.clerk_auth import clerk_client` to work
clerk_client = None


def __getattr__(name):
    """Provide lazy access to clerk_client for backwards compatibility."""
    if name == "clerk_client":
        global clerk_client
        if clerk_client is None:
            clerk_client = get_clerk_client()
        return clerk_client
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
