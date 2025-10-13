"""
Cache Manager

Provides TTL-based caching for context data with different refresh intervals.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class CacheManager:
    """Manages caching of context data with TTL support"""

    def __init__(self, cache_dir: str = "storage/context/cache"):
        """
        Initialize the cache manager

        Args:
            cache_dir: Directory for cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("mark_i.context.cache")

        # In-memory cache for frequently accessed data
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

        self.logger.info("CacheManager initialized")

    def get(self, key: str, max_age_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get cached data

        Args:
            key: Cache key
            max_age_seconds: Maximum age in seconds, None for no age limit

        Returns:
            Cached data if available and not expired, None otherwise
        """
        # Check memory cache first
        if key in self._memory_cache:
            cache_entry = self._memory_cache[key]
            if self._is_cache_valid(cache_entry, max_age_seconds):
                self.logger.debug(f"Cache hit (memory): {key}")
                return cache_entry['data']
            else:
                # Remove expired entry
                del self._memory_cache[key]

        # Check disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_entry = json.load(f)

                if self._is_cache_valid(cache_entry, max_age_seconds):
                    self.logger.debug(f"Cache hit (disk): {key}")
                    # Store in memory cache for faster access
                    self._memory_cache[key] = cache_entry
                    return cache_entry['data']
                else:
                    # Remove expired file
                    cache_file.unlink()

            except Exception as e:
                self.logger.error(f"Failed to read cache file {cache_file}: {str(e)}")

        self.logger.debug(f"Cache miss: {key}")
        return None

    def set(self, key: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None):
        """
        Store data in cache

        Args:
            key: Cache key
            data: Data to cache
            ttl_seconds: Time to live in seconds, None for no expiration
        """
        cache_entry = {
            'data': data,
            'cached_at': datetime.now().isoformat(),
            'ttl_seconds': ttl_seconds
        }

        # Store in memory cache
        self._memory_cache[key] = cache_entry

        # Store on disk for persistence
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Cached data: {key} (TTL: {ttl_seconds}s)")

        except Exception as e:
            self.logger.error(f"Failed to write cache file {cache_file}: {str(e)}")

    def invalidate(self, key: str):
        """
        Invalidate cached data

        Args:
            key: Cache key to invalidate
        """
        # Remove from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]

        # Remove from disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
                self.logger.debug(f"Invalidated cache: {key}")
            except Exception as e:
                self.logger.error(f"Failed to remove cache file {cache_file}: {str(e)}")

    def clear_all(self):
        """Clear all cached data"""
        # Clear memory cache
        self._memory_cache.clear()

        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except Exception as e:
                self.logger.error(f"Failed to remove cache file {cache_file}: {str(e)}")

        self.logger.info("Cleared all cache data")

    def cleanup_expired(self):
        """Remove expired cache entries"""
        # Clean memory cache
        expired_keys = []
        for key, cache_entry in self._memory_cache.items():
            if not self._is_cache_valid(cache_entry, None):
                expired_keys.append(key)

        for key in expired_keys:
            del self._memory_cache[key]

        # Clean disk cache
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_entry = json.load(f)

                if not self._is_cache_valid(cache_entry, None):
                    cache_file.unlink()
                    self.logger.debug(f"Removed expired cache: {cache_file.stem}")

            except Exception as e:
                self.logger.error(f"Failed to process cache file {cache_file}: {str(e)}")

        self.logger.debug("Cleaned up expired cache entries")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary containing cache statistics
        """
        memory_count = len(self._memory_cache)
        disk_count = len(list(self.cache_dir.glob("*.json")))

        return {
            'memory_entries': memory_count,
            'disk_entries': disk_count,
            'cache_directory': str(self.cache_dir),
            'memory_keys': list(self._memory_cache.keys())
        }

    def _is_cache_valid(self, cache_entry: Dict[str, Any], max_age_seconds: Optional[int]) -> bool:
        """
        Check if cache entry is still valid

        Args:
            cache_entry: Cache entry to check
            max_age_seconds: Maximum age override

        Returns:
            True if cache is valid, False otherwise
        """
        try:
            cached_at = datetime.fromisoformat(cache_entry['cached_at'])
            ttl_seconds = cache_entry.get('ttl_seconds')

            # Use provided max_age_seconds or cached TTL
            effective_ttl = max_age_seconds if max_age_seconds is not None else ttl_seconds

            if effective_ttl is None:
                # No expiration
                return True

            age_seconds = (datetime.now() - cached_at).total_seconds()
            return age_seconds < effective_ttl

        except Exception as e:
            self.logger.error(f"Failed to validate cache entry: {str(e)}")
            return False