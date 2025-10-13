"""
Base Collector Interface

Abstract base class for all context collectors in the MARK-I system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime


class BaseCollector(ABC):
    """Abstract base class for context collectors"""

    def __init__(self, name: str):
        """
        Initialize the collector

        Args:
            name: Human-readable name for this collector
        """
        self.name = name
        self.logger = logging.getLogger(f"mark_i.context.{name}")
        self._last_collection_time: Optional[datetime] = None
        self._last_collection_data: Optional[Dict[str, Any]] = None

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """
        Collect context data

        Returns:
            Dictionary containing the collected context data

        Raises:
            CollectionError: If data collection fails
        """
        pass

    @abstractmethod
    def get_refresh_interval(self) -> int:
        """
        Get the recommended refresh interval for this collector

        Returns:
            Refresh interval in seconds
        """
        pass

    @abstractmethod
    def is_expensive(self) -> bool:
        """
        Check if this collector performs expensive operations

        Returns:
            True if collection is resource-intensive, False otherwise
        """
        pass

    def get_cache_key(self) -> str:
        """
        Get the cache key for this collector's data

        Returns:
            Unique cache key string
        """
        return f"context_{self.name.lower().replace(' ', '_')}"

    def should_refresh(self) -> bool:
        """
        Check if this collector's data should be refreshed

        Returns:
            True if data should be refreshed, False otherwise
        """
        if self._last_collection_time is None:
            return True

        time_since_last = (datetime.now() - self._last_collection_time).total_seconds()
        return time_since_last >= self.get_refresh_interval()

    def collect_with_caching(self) -> Dict[str, Any]:
        """
        Collect data with automatic caching and refresh logic

        Returns:
            Dictionary containing the collected context data
        """
        try:
            if not self.should_refresh() and self._last_collection_data is not None:
                self.logger.debug(f"Using cached data for {self.name}")
                return self._last_collection_data

            self.logger.debug(f"Collecting fresh data for {self.name}")
            data = self.collect()

            # Add metadata
            data["_metadata"] = {"collector": self.name, "collected_at": datetime.now().isoformat(), "refresh_interval": self.get_refresh_interval(), "is_expensive": self.is_expensive()}

            self._last_collection_time = datetime.now()
            self._last_collection_data = data

            return data

        except Exception as e:
            self.logger.error(f"Failed to collect data for {self.name}: {str(e)}")

            # Return cached data if available, otherwise minimal fallback
            if self._last_collection_data is not None:
                self.logger.warning(f"Using stale cached data for {self.name}")
                return self._last_collection_data
            else:
                return self._get_fallback_data()

    def _get_fallback_data(self) -> Dict[str, Any]:
        """
        Get minimal fallback data when collection fails

        Returns:
            Dictionary with minimal fallback data
        """
        return {"error": f"Failed to collect {self.name} data", "fallback": True, "_metadata": {"collector": self.name, "collected_at": datetime.now().isoformat(), "status": "error"}}

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate collected data structure

        Args:
            data: Data to validate

        Returns:
            True if data is valid, False otherwise
        """
        # Basic validation - subclasses can override for specific validation
        return isinstance(data, dict) and len(data) > 0


class CollectionError(Exception):
    """Exception raised when context collection fails"""

    pass
