"""
Base component implementation for MARK-I hierarchical AI architecture.

This module provides base classes that implement common functionality
for all MARK-I components, including configuration management, logging,
and lifecycle management.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Callable, Optional
from abc import ABC

from mark_i.core.interfaces import IComponent, IConfigurable, IObservable
from mark_i.core.architecture_config import ComponentConfig
# Use simple logger name to avoid import chain issues
APP_ROOT_LOGGER_NAME = "mark_i"


class BaseComponent(IComponent, IConfigurable, IObservable, ABC):
    """
    Base implementation for all MARK-I components.
    
    Provides common functionality including:
    - Configuration management
    - Logging setup
    - Lifecycle management (initialize/shutdown)
    - Status tracking
    - Observer pattern implementation
    """
    
    def __init__(self, component_name: str, config: Optional[ComponentConfig] = None):
        """
        Initialize the base component.
        
        Args:
            component_name: Name of the component (used for logging and config)
            config: Component configuration. If None, loads from global config.
        """
        self.component_name = component_name
        self.logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.{component_name}")
        
        # Load configuration (use provided config or default)
        self.config = config or ComponentConfig()
        
        # Set logging level from config
        self.logger.setLevel(self.config.log_level.value)
        
        # Component state
        self._initialized = False
        self._running = False
        self._shutdown_requested = False
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Observer pattern
        self._observers: List[Callable[[Dict[str, Any]], None]] = []
        
        # Status tracking
        self._status = {
            'name': self.component_name,
            'initialized': False,
            'running': False,
            'healthy': True,
            'last_error': None,
            'start_time': None,
            'uptime_seconds': 0,
        }
        
        self.logger.debug(f"Base component {component_name} created")
    
    def _get_component_config(self, component_name: str) -> Optional[ComponentConfig]:
        """Safely get component configuration without triggering environment requirements."""
        try:
            # Only try to load config if explicitly requested
            # This avoids triggering environment validation during basic instantiation
            return None  # Use default config for now
        except Exception:
            # If config loading fails, return None to use default
            return None
    
    def initialize(self) -> bool:
        """Initialize the component."""
        with self._lock:
            if self._initialized:
                self.logger.warning(f"Component {self.component_name} already initialized")
                return True
            
            try:
                self.logger.info(f"Initializing component {self.component_name}")
                
                # Validate configuration
                if not self.validate_configuration(self.config.__dict__):
                    self.logger.error(f"Invalid configuration for component {self.component_name}")
                    return False
                
                # Call subclass initialization
                if not self._initialize_component():
                    self.logger.error(f"Component-specific initialization failed for {self.component_name}")
                    return False
                
                self._initialized = True
                self._status['initialized'] = True
                self._status['start_time'] = time.time()
                
                self.logger.info(f"Component {self.component_name} initialized successfully")
                self._notify_observers({'type': 'component_initialized', 'component': self.component_name})
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to initialize component {self.component_name}: {e}", exc_info=True)
                self._status['healthy'] = False
                self._status['last_error'] = str(e)
                return False
    
    def shutdown(self) -> bool:
        """Shutdown the component gracefully."""
        with self._lock:
            if not self._initialized:
                self.logger.warning(f"Component {self.component_name} not initialized, nothing to shutdown")
                return True
            
            if self._shutdown_requested:
                self.logger.warning(f"Shutdown already requested for component {self.component_name}")
                return True
            
            try:
                self.logger.info(f"Shutting down component {self.component_name}")
                self._shutdown_requested = True
                
                # Call subclass shutdown
                if not self._shutdown_component():
                    self.logger.error(f"Component-specific shutdown failed for {self.component_name}")
                    return False
                
                self._running = False
                self._initialized = False
                self._status['initialized'] = False
                self._status['running'] = False
                
                self.logger.info(f"Component {self.component_name} shutdown successfully")
                self._notify_observers({'type': 'component_shutdown', 'component': self.component_name})
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to shutdown component {self.component_name}: {e}", exc_info=True)
                self._status['healthy'] = False
                self._status['last_error'] = str(e)
                return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current component status and health information."""
        with self._lock:
            status = self._status.copy()
            
            # Update uptime
            if status['start_time'] is not None:
                status['uptime_seconds'] = time.time() - status['start_time']
            
            # Add component-specific status
            try:
                component_status = self._get_component_status()
                status.update(component_status)
            except Exception as e:
                self.logger.error(f"Failed to get component status for {self.component_name}: {e}")
                status['healthy'] = False
                status['last_error'] = str(e)
            
            return status
    
    def get_name(self) -> str:
        """Get the component name."""
        return self.component_name
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the component with provided settings."""
        try:
            # Validate configuration
            if not self.validate_configuration(config):
                self.logger.error(f"Invalid configuration provided for {self.component_name}")
                return False
            
            # Update configuration
            for key, value in config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    # Store in custom_settings
                    self.config.custom_settings[key] = value
            
            # Update logging level if changed
            if 'log_level' in config:
                self.logger.setLevel(self.config.log_level.value)
            
            # Call component-specific configuration
            if not self._configure_component(config):
                self.logger.error(f"Component-specific configuration failed for {self.component_name}")
                return False
            
            self.logger.info(f"Component {self.component_name} configured successfully")
            self._notify_observers({'type': 'component_configured', 'component': self.component_name})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure component {self.component_name}: {e}", exc_info=True)
            return False
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        config_dict = {
            'enabled': self.config.enabled,
            'log_level': self.config.log_level.value,
            'max_retries': self.config.max_retries,
            'timeout_seconds': self.config.timeout_seconds,
        }
        config_dict.update(self.config.custom_settings)
        
        # Add component-specific configuration
        try:
            component_config = self._get_component_configuration()
            config_dict.update(component_config)
        except Exception as e:
            self.logger.error(f"Failed to get component configuration for {self.component_name}: {e}")
        
        return config_dict
    
    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """Validate a configuration before applying it."""
        try:
            # Basic validation
            if 'timeout_seconds' in config:
                if not isinstance(config['timeout_seconds'], (int, float)) or config['timeout_seconds'] <= 0:
                    return False
            
            if 'max_retries' in config:
                if not isinstance(config['max_retries'], int) or config['max_retries'] < 0:
                    return False
            
            # Call component-specific validation
            return self._validate_component_configuration(config)
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed for {self.component_name}: {e}")
            return False
    
    def add_observer(self, observer: Callable[[Dict[str, Any]], None]) -> None:
        """Add an observer callback."""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
                self.logger.debug(f"Observer added to {self.component_name}")
    
    def remove_observer(self, observer: Callable[[Dict[str, Any]], None]) -> None:
        """Remove an observer callback."""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
                self.logger.debug(f"Observer removed from {self.component_name}")
    
    def notify_observers(self, event: Dict[str, Any]) -> None:
        """Notify all observers of an event."""
        self._notify_observers(event)
    
    def _notify_observers(self, event: Dict[str, Any]) -> None:
        """Internal method to notify observers."""
        with self._lock:
            event['source'] = self.component_name
            event['timestamp'] = time.time()
            
            for observer in self._observers.copy():  # Copy to avoid modification during iteration
                try:
                    observer(event)
                except Exception as e:
                    self.logger.error(f"Observer notification failed for {self.component_name}: {e}")
    
    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._initialized
    
    def is_running(self) -> bool:
        """Check if component is running."""
        return self._running
    
    def is_healthy(self) -> bool:
        """Check if component is healthy."""
        return self._status['healthy']
    
    def set_running(self, running: bool) -> None:
        """Set the running state."""
        with self._lock:
            self._running = running
            self._status['running'] = running
    
    def execute_with_retry(self, operation: Callable[[], Any], operation_name: str = "operation") -> Any:
        """Execute an operation with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries:
                    self.logger.warning(f"Attempt {attempt + 1} failed for {operation_name} in {self.component_name}: {e}")
                    time.sleep(min(2 ** attempt, 10))  # Exponential backoff, max 10 seconds
                else:
                    self.logger.error(f"All {self.config.max_retries + 1} attempts failed for {operation_name} in {self.component_name}")
        
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"Operation {operation_name} failed without exception")
    
    # Abstract methods for subclasses to implement
    
    def _initialize_component(self) -> bool:
        """Component-specific initialization. Override in subclasses."""
        return True
    
    def _shutdown_component(self) -> bool:
        """Component-specific shutdown. Override in subclasses."""
        return True
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get component-specific status. Override in subclasses."""
        return {}
    
    def _configure_component(self, config: Dict[str, Any]) -> bool:
        """Component-specific configuration. Override in subclasses."""
        return True
    
    def _get_component_configuration(self) -> Dict[str, Any]:
        """Get component-specific configuration. Override in subclasses."""
        return {}
    
    def _validate_component_configuration(self, config: Dict[str, Any]) -> bool:
        """Validate component-specific configuration. Override in subclasses."""
        return True


class ObservableComponent(BaseComponent):
    """
    Base class for components that need to emit events regularly.
    
    Provides additional functionality for components that need to
    notify observers about state changes or events.
    """
    
    def __init__(self, component_name: str, config: Optional[ComponentConfig] = None):
        super().__init__(component_name, config)
        self._event_queue: List[Dict[str, Any]] = []
        self._event_thread: Optional[threading.Thread] = None
        self._event_stop_flag = threading.Event()
    
    def start_event_processing(self) -> None:
        """Start the event processing thread."""
        if self._event_thread and self._event_thread.is_alive():
            return
        
        self._event_stop_flag.clear()
        self._event_thread = threading.Thread(
            target=self._process_events,
            name=f"{self.component_name}_EventProcessor",
            daemon=True
        )
        self._event_thread.start()
        self.logger.debug(f"Event processing started for {self.component_name}")
    
    def stop_event_processing(self) -> None:
        """Stop the event processing thread."""
        if self._event_thread and self._event_thread.is_alive():
            self._event_stop_flag.set()
            self._event_thread.join(timeout=5.0)
            self.logger.debug(f"Event processing stopped for {self.component_name}")
    
    def queue_event(self, event: Dict[str, Any]) -> None:
        """Queue an event for processing."""
        with self._lock:
            self._event_queue.append(event)
    
    def _process_events(self) -> None:
        """Process queued events."""
        while not self._event_stop_flag.is_set():
            events_to_process = []
            
            with self._lock:
                if self._event_queue:
                    events_to_process = self._event_queue.copy()
                    self._event_queue.clear()
            
            for event in events_to_process:
                try:
                    self._notify_observers(event)
                except Exception as e:
                    self.logger.error(f"Failed to process event in {self.component_name}: {e}")
            
            time.sleep(0.1)  # Small delay to prevent busy waiting
    
    def _shutdown_component(self) -> bool:
        """Override to stop event processing."""
        self.stop_event_processing()
        return super()._shutdown_component()


class ProcessingComponent(BaseComponent):
    """
    Base class for processing components that handle input/output operations.
    
    Provides common functionality for components that process data,
    including input validation, output formatting, and performance tracking.
    """
    
    def __init__(self, component_name: str, config: Optional[ComponentConfig] = None):
        super().__init__(component_name, config)
        self._processing_stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'average_processing_time': 0.0,
            'last_processing_time': 0.0,
        }
    
    def process_with_stats(self, input_data: Any, processor: Callable[[Any], Any]) -> Any:
        """Process data with automatic statistics tracking."""
        start_time = time.time()
        
        try:
            result = processor(input_data)
            
            # Update success stats
            self._processing_stats['successful_processed'] += 1
            processing_time = time.time() - start_time
            self._update_processing_time(processing_time)
            
            return result
            
        except Exception as e:
            # Update failure stats
            self._processing_stats['failed_processed'] += 1
            self.logger.error(f"Processing failed in {self.component_name}: {e}")
            raise
        
        finally:
            self._processing_stats['total_processed'] += 1
    
    def _update_processing_time(self, processing_time: float) -> None:
        """Update processing time statistics."""
        self._processing_stats['last_processing_time'] = processing_time
        
        # Update rolling average
        total_successful = self._processing_stats['successful_processed']
        if total_successful > 1:
            current_avg = self._processing_stats['average_processing_time']
            new_avg = ((current_avg * (total_successful - 1)) + processing_time) / total_successful
            self._processing_stats['average_processing_time'] = new_avg
        else:
            self._processing_stats['average_processing_time'] = processing_time
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self._processing_stats.copy()
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Include processing stats in status."""
        status = super()._get_component_status()
        status['processing_stats'] = self.get_processing_stats()
        return status
    
    def reset_stats(self) -> None:
        """Reset processing statistics."""
        self._processing_stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'average_processing_time': 0.0,
            'last_processing_time': 0.0,
        }