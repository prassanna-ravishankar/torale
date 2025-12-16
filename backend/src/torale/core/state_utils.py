import hashlib
import json


def compute_state_hash(state: dict) -> str:
    """
    Compute deterministic hash of state for fast comparison.

    Excludes _metadata field and sorts keys for consistency.
    Returns first 16 characters of SHA256 hash.

    Args:
        state: State dictionary to hash

    Returns:
        16-character hex string hash

    Example:
        >>> state = {"release_date": "2024-09-12", "confirmed": True}
        >>> compute_state_hash(state)
        'a3f2c1b4d5e6f7a8'
    """
    # Remove metadata to avoid hash mismatches from timestamps
    clean_state = {k: v for k, v in state.items() if k != "_metadata"}

    # Sort keys for deterministic serialization
    canonical = json.dumps(clean_state, sort_keys=True)

    # Compute SHA256 hash
    hash_bytes = hashlib.sha256(canonical.encode()).hexdigest()

    # Return first 16 chars for brevity
    return hash_bytes[:16]
