"""
Context Manager

Main orchestrator for the MARK-I context collection system.
Manages all collectors, caching, and provides unified API for context access.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import threading

from .collectors.base_collector import BaseCollector


class ContextManager:
    """Main orchestrator for context collection system"""
    
    def __init__(self, storage_path: str = "storage/context"):
        """
        Initialize the context manager
        
        Args:
            storage_path: Path to context storage directory
        """
        self.storage_path = Path(storage_path)
        self.logger = logging.getLogger("mark_i.context.manager")
        
        # Ensure storage directories exist
        self._ensure_storage_structure()
        
        # Collector registry
        self._collectors: Dict[str, BaseCollector] = {}
        self._collection_lock = threading.Lock()
        self._background_thread: Optional[threading.Thread] = None
        self._stop_background = threading.Event()
        
        self.logger.info("ContextManager initialized")
    
    def _ensure_storage_structure(self):
        """Ensure all required storage directories exist"""
        directories = [
            self.storage_path / "current",
            self.storage_path / "history",
            self.storage_path / "cache"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Ensured directory exists: {directory}")
    
    def register_collector(self, collector: BaseCollector):
        """
        Register a context collector
        
        Args:
            collector: Collector instance to register
        """
        collector_key = collector.get_cache_key()
        self._collectors[collector_key] = collector
        self.logger.info(f"Registered collector: {collector.name} ({collector_key})")
    
    def unregister_collector(self, collector_name: str):
        """
        Unregister a context collector
        
        Args:
            collector_name: Name of collector to unregister
        """
        collector_key = f"context_{collector_name.lower().replace(' ', '_')}"
        if collector_key in self._collectors:
            del self._collectors[collector_key]
            self.logger.info(f"Unregistered collector: {collector_name}")
    
    def get_collectors(self) -> List[str]:
        """
        Get list of registered collector names
        
        Returns:
            List of collector names
        """
        return [collector.name for collector in self._collectors.values()]
    
    def collect_all(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Collect context data from all registered collectors
        
        Args:
            force_refresh: If True, force refresh of all collectors
            
        Returns:
            Dictionary containing all collected context data
        """
        with self._collection_lock:
            context_data = {
                'collection_timestamp': datetime.now().isoformat(),
                'collectors_count': len(self._collectors),
                'context': {}
            }
            
            for collector_key, collector in self._collectors.items():
                try:
                    if force_refresh:
                        # Reset cache to force fresh collection
                        collector._last_collection_time = None
                    
                    data = collector.collect_with_caching()
                    context_data['context'][collector_key] = data
                    
                    self.logger.debug(f"Collected data from {collector.name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to collect from {collector.name}: {str(e)}")
                    context_data['context'][collector_key] = {
                        'error': str(e),
                        'collector': collector.name,
                        'failed_at': datetime.now().isoformat()
                    }
            
            # Save to current context
            self._save_current_context(context_data)
            
            return context_data
    
    def collect_specific(self, collector_names: List[str]) -> Dict[str, Any]:
        """
        Collect context data from specific collectors
        
        Args:
            collector_names: List of collector names to collect from
            
        Returns:
            Dictionary containing collected context data
        """
        context_data = {
            'collection_timestamp': datetime.now().isoformat(),
            'requested_collectors': collector_names,
            'context': {}
        }
        
        for collector_name in collector_names:
            collector_key = f"context_{collector_name.lower().replace(' ', '_')}"
            
            if collector_key in self._collectors:
                try:
                    collector = self._collectors[collector_key]
                    data = collector.collect_with_caching()
                    context_data['context'][collector_key] = data
                    
                except Exception as e:
                    self.logger.error(f"Failed to collect from {collector_name}: {str(e)}")
                    context_data['context'][collector_key] = {
                        'error': str(e),
                        'collector': collector_name,
                        'failed_at': datetime.now().isoformat()
                    }
            else:
                self.logger.warning(f"Collector not found: {collector_name}")
                context_data['context'][collector_key] = {
                    'error': f"Collector '{collector_name}' not registered",
                    'failed_at': datetime.now().isoformat()
                }
        
        return context_data
    
    def get_current_context(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent context data
        
        Returns:
            Dictionary containing current context data, or None if not available
        """
        current_file = self.storage_path / "current" / "context.json"
        
        try:
            if current_file.exists():
                with open(current_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load current context: {str(e)}")
        
        return None
    
    def _save_current_context(self, context_data: Dict[str, Any]):
        """
        Save context data to current context file
        
        Args:
            context_data: Context data to save
        """
        current_file = self.storage_path / "current" / "context.json"
        
        try:
            with open(current_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved current context to {current_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save current context: {str(e)}")
    
    def save_historical_context(self, context_data: Dict[str, Any]):
        """
        Save context data to historical storage
        
        Args:
            context_data: Context data to save
        """
        today = datetime.now().strftime("%Y-%m-%d")
        history_dir = self.storage_path / "history" / today
        history_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%H-%M-%S")
        history_file = history_dir / f"context_{timestamp}.json"
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved historical context to {history_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save historical context: {str(e)}")
    
    def start_background_collection(self, interval: int = 30):
        """
        Start background context collection
        
        Args:
            interval: Collection interval in seconds
        """
        if self._background_thread and self._background_thread.is_alive():
            self.logger.warning("Background collection already running")
            return
        
        self._stop_background.clear()
        self._background_thread = threading.Thread(
            target=self._background_collection_loop,
            args=(interval,),
            daemon=True
        )
        self._background_thread.start()
        
        self.logger.info(f"Started background collection with {interval}s interval")
    
    def stop_background_collection(self):
        """Stop background context collection"""
        if self._background_thread and self._background_thread.is_alive():
            self._stop_background.set()
            self._background_thread.join(timeout=5)
            self.logger.info("Stopped background collection")
    
    def _background_collection_loop(self, interval: int):
        """
        Background collection loop
        
        Args:
            interval: Collection interval in seconds
        """
        while not self._stop_background.is_set():
            try:
                context_data = self.collect_all()
                
                # Save historical snapshot every hour
                current_time = datetime.now()
                if current_time.minute == 0:  # Top of the hour
                    self.save_historical_context(context_data)
                
            except Exception as e:
                self.logger.error(f"Background collection failed: {str(e)}")
            
            # Wait for next collection or stop signal
            self._stop_background.wait(interval)
    
    def get_system_summary(self) -> Dict[str, Any]:
        """
        Get a high-level summary of system context
        
        Returns:
            Dictionary containing system summary
        """
        context = self.get_current_context()
        if not context:
            return {'error': 'No context data available'}
        
        summary = {
            'timestamp': context.get('collection_timestamp'),
            'collectors_active': context.get('collectors_count', 0),
            'summary': {}
        }
        
        # Extract key information from each collector
        for collector_key, data in context.get('context', {}).items():
            if 'error' in data:
                summary['summary'][collector_key] = {'status': 'error', 'error': data['error']}
            else:
                # Extract key metrics (this will be enhanced as collectors are implemented)
                summary['summary'][collector_key] = {
                    'status': 'ok',
                    'last_updated': data.get('_metadata', {}).get('collected_at')
                }
        
        return summary
    
    def cleanup_old_data(self, days_to_keep: int = 7):
        """
        Clean up old historical context data
        
        Args:
            days_to_keep: Number of days of historical data to keep
        """
        history_dir = self.storage_path / "history"
        if not history_dir.exists():
            return
        
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for date_dir in history_dir.iterdir():
            if date_dir.is_dir():
                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d").timestamp()
                    if dir_date < cutoff_date:
                        import shutil
                        shutil.rmtree(date_dir)
                        self.logger.info(f"Cleaned up old context data: {date_dir}")
                except ValueError:
                    # Skip directories that don't match date format
                    continue
                except Exception as e:
                    self.logger.error(f"Failed to cleanup {date_dir}: {str(e)}")
    
    def __del__(self):
        """Cleanup when context manager is destroyed"""
        self.stop_background_collection()