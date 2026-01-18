"""
API Key Rotation Manager

This module provides a thread-safe API key rotation mechanism for LLM providers.
It supports multiple API keys with automatic failover and retry logic.
"""

import logging
import threading
from typing import List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    Thread-safe API key rotation manager.

    Features:
    - Automatic key rotation on failure
    - Round-robin key selection
    - Per-model key management
    - Thread-safe operations
    """

    # Class-level storage for all model key managers
    _managers: dict = {}
    _lock = threading.Lock()

    @classmethod
    def get_manager(cls, model_name: str, api_keys: List[str]) -> 'APIKeyManager':
        """
        Get or create a key manager for the given model.

        Args:
            model_name: Model identifier
            api_keys: List of API keys

        Returns:
            APIKeyManager instance
        """
        if not api_keys:
            return None

        with cls._lock:
            if model_name not in cls._managers:
                cls._managers[model_name] = APIKeyManager(api_keys, model_name)
            return cls._managers[model_name]

    def __init__(self, api_keys: List[str], model_name: str = "unknown"):
        """
        Initialize API key manager.

        Args:
            api_keys: List of API keys for rotation
            model_name: Model identifier for logging
        """
        if not api_keys:
            raise ValueError("api_keys cannot be empty")

        self.model_name = model_name
        self._keys = deque(api_keys)
        self._current_key = None
        self._lock = threading.Lock()

        # Start with first key
        self._current_key = self._keys[0]
        logger.info(f"APIKeyManager initialized for '{model_name}' with {len(api_keys)} keys")

    def get_current_key(self) -> str:
        """
        Get the current API key.

        Returns:
            Current API key
        """
        with self._lock:
            return self._current_key

    def rotate_key(self) -> str:
        """
        Rotate to the next API key.

        This moves the current key to the end of the queue and selects the next one.
        Useful when a key fails or reaches rate limits.

        Returns:
            New current API key
        """
        with self._lock:
            if len(self._keys) <= 1:
                logger.debug(f"Only 1 key available for '{self.model_name}', no rotation")
                return self._current_key

            # Rotate: move current to end, get next
            self._keys.rotate(-1)
            self._current_key = self._keys[0]

            logger.info(f"Rotated API key for '{self.model_name}'. Remaining keys: {len(self._keys)}")
            return self._current_key

    def mark_key_failed(self, failed_key: str = None) -> str:
        """
        Mark current key as failed and rotate to next.

        Args:
            failed_key: Optional failed key for verification

        Returns:
            New API key after rotation
        """
        with self._lock:
            if failed_key and failed_key != self._current_key:
                logger.warning(
                    f"Failed key mismatch for '{self.model_name}'. "
                    f"Expected: {failed_key[:10]}..., Current: {self._current_key[:10]}..."
                )

            logger.warning(f"Key failed for '{self.model_name}', rotating to next key")
            return self.rotate_key()

    def get_all_keys(self) -> List[str]:
        """
        Get all API keys.

        Returns:
            List of all API keys
        """
        with self._lock:
            return list(self._keys)

    def reset(self, api_keys: List[str] = None):
        """
        Reset the manager with new keys.

        Args:
            api_keys: Optional new list of keys. If None, keeps current keys.
        """
        with self._lock:
            if api_keys:
                self._keys = deque(api_keys)
                self._current_key = api_keys[0]
                logger.info(f"Reset APIKeyManager for '{self.model_name}' with {len(api_keys)} keys")
            else:
                # Just reset to first key
                self._keys = deque(list(self._keys))  # Rebuild deque
                self._current_key = self._keys[0]
                logger.info(f"Reset APIKeyManager for '{self.model_name}' to first key")

    def __repr__(self) -> str:
        """String representation (hides sensitive data)."""
        with self._lock:
            num_keys = len(self._keys)
            current_preview = self._current_key[:10] + "..." if self._current_key else "None"
            return f"APIKeyManager(model='{self.model_name}', keys={num_keys}, current={current_preview})"


def get_api_key_manager(model_name: str, api_keys: List[str]) -> Optional[APIKeyManager]:
    """
    Convenience function to get or create an API key manager.

    Args:
        model_name: Model identifier
        api_keys: List of API keys

    Returns:
        APIKeyManager instance or None if api_keys is empty
    """
    return APIKeyManager.get_manager(model_name, api_keys)
