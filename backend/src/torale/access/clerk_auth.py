"""
Backwards compatibility shim for ClerkUser.

DEPRECATED: This module exists only for backwards compatibility.
New code should import User from torale.access instead.

All Clerk-specific logic has been moved to ProductionAuthProvider.
"""

from .auth_provider import ProductionAuthProvider, User, get_auth_provider

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
# This allows `from torale.access import clerk_client` to work


def __getattr__(name):
    """
    Provide lazy access to clerk_client for backwards compatibility.

    This is called when clerk_client is accessed as a module attribute.
    Returns None if the auth provider isn't initialized yet (during imports),
    otherwise returns the Clerk client from ProductionAuthProvider.
    """
    if name == "clerk_client":
        try:
            return get_clerk_client()
        except RuntimeError:
            # Auth provider not initialized yet (during module imports)
            # Return None for backwards compatibility with code that checks
            # `if clerk_client:` before using it
            return None
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
