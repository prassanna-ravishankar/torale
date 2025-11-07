"""
Torale - AI-powered monitoring platform with grounded search.

Monitor the web for specific conditions and get notified when they're met.
"""

__version__ = "0.1.0"

# Export SDK for easy imports
from torale.sdk import Torale, monitor

__all__ = ["Torale", "monitor", "__version__"]
