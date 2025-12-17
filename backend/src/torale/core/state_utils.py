import hashlib
import json


def compute_state_hash(state: dict | list) -> str:
    """
    Compute deterministic hash of state for fast comparison.

    Excludes _metadata field from dicts and sorts keys for consistency.
    Returns first 16 characters of SHA256 hash.

    Args:
        state: State dictionary or list to hash

    Returns:
        16-character hex string hash

    Example:
        >>> state = {"release_date": "2024-09-12", "confirmed": True}
        >>> compute_state_hash(state)
        'a3f2c1b4d5e6f7a8'
    """
    # Remove metadata to avoid hash mismatches from timestamps
    if isinstance(state, dict):
        clean_state = {k: v for k, v in state.items() if k != "_metadata"}
    elif isinstance(state, list):
        # For lists, remove _metadata from each dict item if present
        clean_state = [
            {k: v for k, v in item.items() if k != "_metadata"} if isinstance(item, dict) else item
            for item in state
        ]
    else:
        clean_state = state

    # Sort keys for deterministic serialization
    canonical = json.dumps(clean_state, sort_keys=True)

    # Compute SHA256 hash
    hash_bytes = hashlib.sha256(canonical.encode()).hexdigest()

    # Return first 16 chars for brevity
    return hash_bytes[:16]
