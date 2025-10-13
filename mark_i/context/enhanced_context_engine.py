"""Enhanced Context Awareness Engine for MARK-I comprehensive environment monitoring.

This module provides advanced context awareness, system state tracking, application
relationship mapping, and environmental change detection to enable intelligent
adaptation and decision making based on comprehensive environmental understanding.
"""

import logging
import threading
import time
import psutil
import os
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import hashlib

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".context.enhanced_context_engine")


class ContextChangeType(Enum):
    """Types of context changes."""
    APPLICATION_FOCUS = "application_focus"
    SYSTEM_RESOURCE = "system_resource"
    NETWORK_STATE = "network_state"
    USER_ACTIVITY = "user_activity"
    ENVIRONMENT_CONFIG = "environment_config"
    PROCESS_LIFECYCLE = "process_lifecycle"


class EnvironmentState(Enum):
    """Overall environment states."""
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


class AdaptationTrigger(Enum):
    """Triggers for environmental adaptation."""
    RESOURCE_PRESSURE = "resource_pressure"
    APPLICATION_CHANGE = "application_change"
    USER_PATTERN_SHIFT = "user_pattern_shift"
    SYSTEM_EVENT = "system_event"
    PERFORMANCE_DEGRADATION = "performance_degradation"


@dataclass
class SystemState:
    """Comprehensive system state snapshot."""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_activity: Dict[str, float]
    active_processes: List[Dict[str, Any]]
    focused_application: Optional[str]
    user_activity_level: float
    system_load: float
    environment_state: EnvironmentState


@dataclass
class ApplicationContext:
    """Context information for an application."""
    app_id: str
    name: str
    process_id: int
    window_title: str
    is_focused: bool
    resource_usage: Dict[str, float]
    relationships: List[str]  # Related applications
    user_interaction_level: float
    last_activity: datetime
    context_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvironmentChange:
    """Represents a detected environmental change."""
    change_id: str
    change_type: ContextChangeType
    description: str
    severity: str  # low, medium, high, critical
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    impact_assessment: Dict[str, Any]
    adaptation_suggestions: List[str]
    timestamp: datetime
    confidence: float


@dataclass
class ContextPattern:
    """Represents a learned context pattern."""
    pattern_id: str
    pattern_signature: str
    frequency: int
    typical_duration: timedelta
    associated_applications: List[str]
    resource_profile: Dict[str, float]
    user_behavior_indicators: Dict[str, Any]
    adaptation_strategies: List[str]
    success_rate: float
    last_seen: datetime


class EnhancedContextEngine(ProcessingComponent):
    """
    Advanced context awareness engine for comprehensive environment monitoring.
    
    Provides intelligent system state tracking, application relationship mapping,
    environmental change detection, and adaptive optimization based on
    comprehensive environmental understanding.
    """
    
    def __init__(self, config: ComponentConfig):
        super().__init__("enhanced_context_engine", config)
        
        # Configuration
        self.monitoring_interval = getattr(config, "monitoring_interval", 5.0)
        self.change_detection_threshold = getattr(config, "change_detection_threshold", 0.1)
        self.pattern_learning_enabled = getattr(config, "pattern_learning_enabled", True)
        self.max_history_size = getattr(config, "max_history_size", 10000)
        self.adaptation_sensitivity = getattr(config, "adaptation_sensitivity", 0.2)
        
        # System state tracking
        self.current_system_state: Optional[SystemState] = None
        self.system_state_history: deque = deque(maxlen=self.max_history_size)
        self.baseline_metrics: Dict[str, float] = {}
        
        # Application context management
        self.active_applications: Dict[str, ApplicationContext] = {}
        self.application_relationships: Dict[str, Set[str]] = defaultdict(set)
        self.application_history: deque = deque(maxlen=5000)
        
        # Change detection and adaptation
        self.detected_changes: deque = deque(maxlen=1000)
        self.adaptation_triggers: List[AdaptationTrigger] = []
        self.environment_transitions: List[Dict[str, Any]] = []
        
        # Pattern learning and recognition
        self.learned_patterns: Dict[str, ContextPattern] = {}
        self.pattern_matching_cache: Dict[str, List[str]] = {}
        self.user_behavior_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Threading and synchronization
        self.monitoring_lock = threading.Lock()
        self.context_lock = threading.Lock()
        self.pattern_lock = threading.Lock()
        
        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.stop_monitoring = threading.Event()
        
        # Statistics
        self.monitoring_cycles = 0
        self.changes_detected = 0
        self.patterns_learned = 0
        self.adaptations_triggered = 0
        
        # Initialize baseline metrics
        self._initialize_baseline_metrics()
        
        logger.info("EnhancedContextEngine initialized for comprehensive environment monitoring")
    
    def start_monitoring(self) -> bool:
        """Start continuous environment monitoring."""
        try:
            if self.monitoring_active:
                logger.warning("Monitoring already active")
                return True
            
            self.monitoring_active = True
            self.stop_monitoring.clear()
            
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="EnhancedContextMonitoring",
                daemon=True
            )
            self.monitoring_thread.start()
            
            logger.info("Enhanced context monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop continuous environment monitoring."""
        try:
            if not self.monitoring_active:
                return True
            
            self.monitoring_active = False
            self.stop_monitoring.set()
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=10.0)
            
            logger.info("Enhanced context monitoring stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            return False
    
    def get_comprehensive_context(self) -> Dict[str, Any]:
        """Get comprehensive current context information."""
        try:
            with self.context_lock:
                context = {
                    "timestamp": datetime.now().isoformat(),
                    "system_state": self._get_current_system_state_dict(),
                    "active_applications": self._get_active_applications_dict(),
                    "environment_state": self._assess_environment_state().value,
                    "recent_changes": self._get_recent_changes(),
                    "detected_patterns": self._get_active_patterns(),
                    "adaptation_recommendations": self._generate_adaptation_recommendations(),
                    "resource_pressure": self._assess_resource_pressure(),
                    "user_activity_assessment": self._assess_user_activity(),
                    "system_health": self._assess_system_health()
                }
                
                return context
                
        except Exception as e:
            logger.error(f"Error getting comprehensive context: {e}")
            return {"error": str(e)}
    
    def detect_environment_changes(self, previous_state: Optional[SystemState] = None) -> List[EnvironmentChange]:
        """Detect significant environmental changes."""
        try:
            if not previous_state and len(self.system_state_history) < 2:
                return []
            
            if not previous_state:
                previous_state = list(self.system_state_history)[-2]
            
            current_state = self.current_system_state
            if not current_state:
                return []
            
            changes = []
            
            # Detect CPU usage changes
            cpu_change = abs(current_state.cpu_usage - previous_state.cpu_usage)
            if cpu_change > self.change_detection_threshold * 100:
                changes.append(self._create_change_record(
                    ContextChangeType.SYSTEM_RESOURCE,
                    f"CPU usage changed by {cpu_change:.1f}%",
                    {"cpu_before": previous_state.cpu_usage, "cpu_after": current_state.cpu_usage},
                    "high" if cpu_change > 50 else "medium"
                ))
            
            # Detect memory usage changes
            memory_change = abs(current_state.memory_usage - previous_state.memory_usage)
            if memory_change > self.change_detection_threshold * 100:
                changes.append(self._create_change_record(
                    ContextChangeType.SYSTEM_RESOURCE,
                    f"Memory usage changed by {memory_change:.1f}%",
                    {"memory_before": previous_state.memory_usage, "memory_after": current_state.memory_usage},
                    "high" if memory_change > 30 else "medium"
                ))
            
            # Detect application focus changes
            if current_state.focused_application != previous_state.focused_application:
                changes.append(self._create_change_record(
                    ContextChangeType.APPLICATION_FOCUS,
                    f"Application focus changed from {previous_state.focused_application} to {current_state.focused_application}",
                    {"app_before": previous_state.focused_application, "app_after": current_state.focused_application},
                    "medium"
                ))
            
            # Detect user activity changes
            activity_change = abs(current_state.user_activity_level - previous_state.user_activity_level)
            if activity_change > 0.3:
                changes.append(self._create_change_record(
                    ContextChangeType.USER_ACTIVITY,
                    f"User activity level changed by {activity_change:.2f}",
                    {"activity_before": previous_state.user_activity_level, "activity_after": current_state.user_activity_level},
                    "low"
                ))
            
            # Store detected changes
            for change in changes:
                self.detected_changes.append(change)
                self.changes_detected += 1
            
            return changes
            
        except Exception as e:
            logger.error(f"Error detecting environment changes: {e}")
            return []
    
    def map_application_relationships(self) -> Dict[str, List[str]]:
        """Map relationships between applications."""
        try:
            relationships = {}
            
            for app_id, app_context in self.active_applications.items():
                related_apps = []
                
                # Find applications with similar resource patterns
                for other_id, other_context in self.active_applications.items():
                    if other_id == app_id:
                        continue
                    
                    # Check resource usage similarity
                    similarity = self._calculate_resource_similarity(
                        app_context.resource_usage, 
                        other_context.resource_usage
                    )
                    
                    if similarity > 0.7:
                        related_apps.append(other_id)
                
                # Find applications that are frequently active together
                co_occurrence_apps = self._find_co_occurring_applications(app_id)
                related_apps.extend(co_occurrence_apps)
                
                # Remove duplicates and store
                relationships[app_id] = list(set(related_apps))
                self.application_relationships[app_id].update(related_apps)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error mapping application relationships: {e}")
            return {}
    
    def learn_context_patterns(self) -> List[ContextPattern]:
        """Learn patterns from historical context data."""
        try:
            if not self.pattern_learning_enabled:
                return []
            
            with self.pattern_lock:
                new_patterns = []
                
                # Analyze system state patterns
                state_patterns = self._analyze_system_state_patterns()
                new_patterns.extend(state_patterns)
                
                # Analyze application usage patterns
                app_patterns = self._analyze_application_patterns()
                new_patterns.extend(app_patterns)
                
                # Analyze user behavior patterns
                behavior_patterns = self._analyze_user_behavior_patterns()
                new_patterns.extend(behavior_patterns)
                
                # Store learned patterns
                for pattern in new_patterns:
                    self.learned_patterns[pattern.pattern_id] = pattern
                    self.patterns_learned += 1
                
                logger.info(f"Learned {len(new_patterns)} new context patterns")
                return new_patterns
                
        except Exception as e:
            logger.error(f"Error learning context patterns: {e}")
            return []
    
    def adapt_to_environment(self, changes: List[EnvironmentChange]) -> List[Dict[str, Any]]:
        """Adapt system behavior based on environmental changes."""
        try:
            adaptations = []
            
            for change in changes:
                # Determine if adaptation is needed
                if self._should_adapt_to_change(change):
                    adaptation = self._generate_adaptation_strategy(change)
                    if adaptation:
                        adaptations.append(adaptation)
                        self.adaptations_triggered += 1
            
            # Apply adaptations
            applied_adaptations = []
            for adaptation in adaptations:
                if self._apply_adaptation(adaptation):
                    applied_adaptations.append(adaptation)
            
            logger.info(f"Applied {len(applied_adaptations)} environmental adaptations")
            return applied_adaptations
            
        except Exception as e:
            logger.error(f"Error adapting to environment: {e}")
            return [] 
   
    def _monitoring_loop(self):
        """Main monitoring loop for continuous context awareness."""
        logger.info("Enhanced context monitoring loop started")
        
        while not self.stop_monitoring.is_set():
            try:
                # Capture current system state
                current_state = self._capture_system_state()
                
                # Detect changes from previous state
                changes = self.detect_environment_changes()
                
                # Learn patterns from current context
                if self.monitoring_cycles % 10 == 0:  # Learn patterns every 10 cycles
                    self.learn_context_patterns()
                
                # Adapt to significant changes
                if changes:
                    self.adapt_to_environment(changes)
                
                # Update application contexts
                self._update_application_contexts()
                
                # Map application relationships
                if self.monitoring_cycles % 20 == 0:  # Update relationships every 20 cycles
                    self.map_application_relationships()
                
                self.monitoring_cycles += 1
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            # Wait for next monitoring cycle
            self.stop_monitoring.wait(self.monitoring_interval)
        
        logger.info("Enhanced context monitoring loop stopped")
    
    def _capture_system_state(self) -> SystemState:
        """Capture comprehensive current system state."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network activity
            network_io = psutil.net_io_counters()
            network_activity = {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            }
            
            # Get active processes
            active_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['cpu_percent'] > 1.0 or proc_info['memory_percent'] > 1.0:
                        active_processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent'],
                            'memory_percent': proc_info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Determine focused application (simplified)
            focused_app = self._get_focused_application()
            
            # Assess user activity level
            user_activity = self._assess_current_user_activity()
            
            # Calculate system load
            system_load = (cpu_percent + memory.percent) / 2
            
            # Determine environment state
            environment_state = self._determine_environment_state(cpu_percent, memory.percent, user_activity)
            
            # Create system state
            system_state = SystemState(
                timestamp=datetime.now(),
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_activity=network_activity,
                active_processes=active_processes,
                focused_application=focused_app,
                user_activity_level=user_activity,
                system_load=system_load,
                environment_state=environment_state
            )
            
            # Update current state and history
            with self.monitoring_lock:
                self.current_system_state = system_state
                self.system_state_history.append(system_state)
            
            return system_state
            
        except Exception as e:
            logger.error(f"Error capturing system state: {e}")
            return SystemState(
                timestamp=datetime.now(),
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_activity={},
                active_processes=[],
                focused_application=None,
                user_activity_level=0.0,
                system_load=0.0,
                environment_state=EnvironmentState.IDLE
            )
    
    def _get_focused_application(self) -> Optional[str]:
        """Get the currently focused application."""
        try:
            # This is a simplified implementation
            # In a real system, this would use platform-specific APIs
            for app_id, app_context in self.active_applications.items():
                if app_context.is_focused:
                    return app_id
            
            # Fallback: find application with highest user interaction
            if self.active_applications:
                most_active = max(
                    self.active_applications.values(),
                    key=lambda app: app.user_interaction_level
                )
                return most_active.app_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting focused application: {e}")
            return None
    
    def _assess_current_user_activity(self) -> float:
        """Assess current user activity level."""
        try:
            # This is a simplified implementation
            # In a real system, this would analyze mouse/keyboard activity, window focus changes, etc.
            
            # Base assessment on system activity
            if not self.current_system_state:
                return 0.5
            
            # High CPU/memory usage might indicate user activity
            activity_score = 0.0
            
            if self.current_system_state.cpu_usage > 20:
                activity_score += 0.3
            
            if self.current_system_state.memory_usage > 60:
                activity_score += 0.2
            
            # Active applications indicate user activity
            if len(self.active_applications) > 3:
                activity_score += 0.3
            
            # Recent application changes indicate activity
            recent_changes = [c for c in self.detected_changes 
                            if c.change_type == ContextChangeType.APPLICATION_FOCUS 
                            and (datetime.now() - c.timestamp).seconds < 300]
            
            if recent_changes:
                activity_score += 0.2
            
            return min(1.0, activity_score)
            
        except Exception as e:
            logger.error(f"Error assessing user activity: {e}")
            return 0.5
    
    def _determine_environment_state(self, cpu_usage: float, memory_usage: float, user_activity: float) -> EnvironmentState:
        """Determine overall environment state."""
        # Critical state
        if cpu_usage > 90 or memory_usage > 95:
            return EnvironmentState.CRITICAL
        
        # Busy state
        if cpu_usage > 70 or memory_usage > 80 or user_activity > 0.8:
            return EnvironmentState.BUSY
        
        # Active state
        if cpu_usage > 30 or memory_usage > 50 or user_activity > 0.4:
            return EnvironmentState.ACTIVE
        
        # Idle state
        return EnvironmentState.IDLE
    
    def _update_application_contexts(self):
        """Update context information for all active applications."""
        try:
            current_processes = {proc.info['name']: proc.info for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])}
            
            # Update existing applications
            for app_id, app_context in self.active_applications.items():
                if app_context.name in current_processes:
                    proc_info = current_processes[app_context.name]
                    app_context.resource_usage = {
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_percent': proc_info['memory_percent']
                    }
                    app_context.last_activity = datetime.now()
                else:
                    # Application no longer active
                    app_context.last_activity = datetime.now() - timedelta(minutes=5)
            
            # Add new applications
            for proc_name, proc_info in current_processes.items():
                if proc_info['cpu_percent'] > 1.0:  # Only track active processes
                    app_id = f"{proc_name}_{proc_info['pid']}"
                    if app_id not in self.active_applications:
                        self.active_applications[app_id] = ApplicationContext(
                            app_id=app_id,
                            name=proc_name,
                            process_id=proc_info['pid'],
                            window_title=proc_name,  # Simplified
                            is_focused=False,  # Will be updated by focus detection
                            resource_usage={
                                'cpu_percent': proc_info['cpu_percent'],
                                'memory_percent': proc_info['memory_percent']
                            },
                            relationships=[],
                            user_interaction_level=0.5,
                            last_activity=datetime.now()
                        )
            
            # Remove inactive applications
            inactive_threshold = datetime.now() - timedelta(minutes=10)
            inactive_apps = [app_id for app_id, app_context in self.active_applications.items()
                           if app_context.last_activity < inactive_threshold]
            
            for app_id in inactive_apps:
                del self.active_applications[app_id]
            
        except Exception as e:
            logger.error(f"Error updating application contexts: {e}")
    
    def _create_change_record(self, change_type: ContextChangeType, description: str, 
                            state_data: Dict[str, Any], severity: str) -> EnvironmentChange:
        """Create a change record."""
        change_id = f"change_{change_type.value}_{int(time.time() * 1000)}"
        
        # Assess impact
        impact_assessment = self._assess_change_impact(change_type, state_data, severity)
        
        # Generate adaptation suggestions
        adaptation_suggestions = self._generate_change_adaptations(change_type, state_data, severity)
        
        return EnvironmentChange(
            change_id=change_id,
            change_type=change_type,
            description=description,
            severity=severity,
            before_state=state_data,
            after_state=state_data,
            impact_assessment=impact_assessment,
            adaptation_suggestions=adaptation_suggestions,
            timestamp=datetime.now(),
            confidence=0.8
        )
    
    def _assess_change_impact(self, change_type: ContextChangeType, state_data: Dict[str, Any], severity: str) -> Dict[str, Any]:
        """Assess the impact of an environmental change."""
        impact = {
            "performance_impact": 0.0,
            "user_experience_impact": 0.0,
            "system_stability_impact": 0.0,
            "adaptation_required": False
        }
        
        if change_type == ContextChangeType.SYSTEM_RESOURCE:
            if severity in ["high", "critical"]:
                impact["performance_impact"] = 0.7
                impact["system_stability_impact"] = 0.5
                impact["adaptation_required"] = True
        
        elif change_type == ContextChangeType.APPLICATION_FOCUS:
            impact["user_experience_impact"] = 0.4
            impact["adaptation_required"] = True
        
        elif change_type == ContextChangeType.USER_ACTIVITY:
            impact["user_experience_impact"] = 0.3
            if severity == "high":
                impact["adaptation_required"] = True
        
        return impact
    
    def _generate_change_adaptations(self, change_type: ContextChangeType, 
                                   state_data: Dict[str, Any], severity: str) -> List[str]:
        """Generate adaptation suggestions for a change."""
        adaptations = []
        
        if change_type == ContextChangeType.SYSTEM_RESOURCE:
            if severity in ["high", "critical"]:
                adaptations.extend([
                    "Reduce processing intensity",
                    "Defer non-critical operations",
                    "Optimize resource usage",
                    "Consider process prioritization"
                ])
        
        elif change_type == ContextChangeType.APPLICATION_FOCUS:
            adaptations.extend([
                "Adjust monitoring focus to new application",
                "Update context-specific strategies",
                "Adapt user interaction patterns"
            ])
        
        elif change_type == ContextChangeType.USER_ACTIVITY:
            if "increased" in str(state_data):
                adaptations.extend([
                    "Increase responsiveness",
                    "Reduce autonomous actions",
                    "Enhance user interaction monitoring"
                ])
            else:
                adaptations.extend([
                    "Increase autonomous operation",
                    "Perform background optimizations",
                    "Reduce monitoring frequency"
                ])
        
        return adaptations
    
    def _initialize_baseline_metrics(self):
        """Initialize baseline system metrics."""
        try:
            # Capture initial system state for baseline
            initial_state = self._capture_system_state()
            
            self.baseline_metrics = {
                "cpu_baseline": initial_state.cpu_usage,
                "memory_baseline": initial_state.memory_usage,
                "disk_baseline": initial_state.disk_usage,
                "user_activity_baseline": initial_state.user_activity_level,
                "system_load_baseline": initial_state.system_load
            }
            
            logger.info("Baseline metrics initialized")
            
        except Exception as e:
            logger.error(f"Error initializing baseline metrics: {e}")
            self.baseline_metrics = {
                "cpu_baseline": 10.0,
                "memory_baseline": 30.0,
                "disk_baseline": 50.0,
                "user_activity_baseline": 0.3,
                "system_load_baseline": 20.0
            }
    
    def _get_current_system_state_dict(self) -> Dict[str, Any]:
        """Get current system state as dictionary."""
        if not self.current_system_state:
            return {}
        
        return {
            "cpu_usage": self.current_system_state.cpu_usage,
            "memory_usage": self.current_system_state.memory_usage,
            "disk_usage": self.current_system_state.disk_usage,
            "network_activity": self.current_system_state.network_activity,
            "focused_application": self.current_system_state.focused_application,
            "user_activity_level": self.current_system_state.user_activity_level,
            "system_load": self.current_system_state.system_load,
            "environment_state": self.current_system_state.environment_state.value,
            "active_process_count": len(self.current_system_state.active_processes)
        }
    
    def _get_active_applications_dict(self) -> Dict[str, Dict[str, Any]]:
        """Get active applications as dictionary."""
        return {
            app_id: {
                "name": app.name,
                "process_id": app.process_id,
                "window_title": app.window_title,
                "is_focused": app.is_focused,
                "resource_usage": app.resource_usage,
                "relationships": app.relationships,
                "user_interaction_level": app.user_interaction_level,
                "last_activity": app.last_activity.isoformat()
            }
            for app_id, app in self.active_applications.items()
        }
    
    def _assess_environment_state(self) -> EnvironmentState:
        """Assess current environment state."""
        if self.current_system_state:
            return self.current_system_state.environment_state
        return EnvironmentState.IDLE
    
    def _get_recent_changes(self) -> List[Dict[str, Any]]:
        """Get recent environmental changes."""
        recent_threshold = datetime.now() - timedelta(minutes=30)
        recent_changes = [
            {
                "change_id": change.change_id,
                "type": change.change_type.value,
                "description": change.description,
                "severity": change.severity,
                "timestamp": change.timestamp.isoformat(),
                "confidence": change.confidence
            }
            for change in self.detected_changes
            if change.timestamp > recent_threshold
        ]
        
        return recent_changes[-10:]  # Last 10 changes
    
    def _get_active_patterns(self) -> List[Dict[str, Any]]:
        """Get currently active context patterns."""
        active_patterns = []
        
        for pattern_id, pattern in self.learned_patterns.items():
            # Check if pattern is currently active
            if self._is_pattern_active(pattern):
                active_patterns.append({
                    "pattern_id": pattern_id,
                    "signature": pattern.pattern_signature,
                    "frequency": pattern.frequency,
                    "success_rate": pattern.success_rate,
                    "associated_applications": pattern.associated_applications,
                    "last_seen": pattern.last_seen.isoformat()
                })
        
        return active_patterns[:5]  # Top 5 active patterns
    
    def _is_pattern_active(self, pattern: ContextPattern) -> bool:
        """Check if a context pattern is currently active."""
        # Simple check based on associated applications
        if pattern.associated_applications:
            active_app_names = [app.name for app in self.active_applications.values()]
            return any(app_name in active_app_names for app_name in pattern.associated_applications)
        
        return False
    
    def _generate_adaptation_recommendations(self) -> List[str]:
        """Generate recommendations for environmental adaptation."""
        recommendations = []
        
        if not self.current_system_state:
            return recommendations
        
        # Resource-based recommendations
        if self.current_system_state.cpu_usage > 80:
            recommendations.append("Consider reducing CPU-intensive operations")
        
        if self.current_system_state.memory_usage > 85:
            recommendations.append("Optimize memory usage or defer memory-intensive tasks")
        
        if self.current_system_state.system_load > 80:
            recommendations.append("System under high load - prioritize critical operations only")
        
        # User activity-based recommendations
        if self.current_system_state.user_activity_level > 0.8:
            recommendations.append("High user activity detected - minimize autonomous actions")
        elif self.current_system_state.user_activity_level < 0.2:
            recommendations.append("Low user activity - opportunity for background optimizations")
        
        # Environment state-based recommendations
        if self.current_system_state.environment_state == EnvironmentState.CRITICAL:
            recommendations.append("Critical system state - emergency protocols may be needed")
        elif self.current_system_state.environment_state == EnvironmentState.IDLE:
            recommendations.append("System idle - good time for maintenance and optimization")
        
        return recommendations
    
    def _assess_resource_pressure(self) -> Dict[str, Any]:
        """Assess current resource pressure."""
        if not self.current_system_state:
            return {"overall": "unknown"}
        
        pressure = {
            "cpu_pressure": "high" if self.current_system_state.cpu_usage > 80 else 
                           "medium" if self.current_system_state.cpu_usage > 50 else "low",
            "memory_pressure": "high" if self.current_system_state.memory_usage > 85 else
                              "medium" if self.current_system_state.memory_usage > 60 else "low",
            "disk_pressure": "high" if self.current_system_state.disk_usage > 90 else
                            "medium" if self.current_system_state.disk_usage > 75 else "low",
            "overall": "high" if any(self.current_system_state.__dict__[key] > 80 
                                   for key in ["cpu_usage", "memory_usage"]) else "normal"
        }
        
        return pressure
    
    def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health."""
        if not self.current_system_state:
            return {"status": "unknown"}
        
        health_score = 1.0
        issues = []
        
        # Check resource usage
        if self.current_system_state.cpu_usage > 90:
            health_score -= 0.3
            issues.append("High CPU usage")
        
        if self.current_system_state.memory_usage > 95:
            health_score -= 0.4
            issues.append("Critical memory usage")
        
        if self.current_system_state.disk_usage > 95:
            health_score -= 0.2
            issues.append("Low disk space")
        
        # Determine health status
        if health_score > 0.8:
            status = "excellent"
        elif health_score > 0.6:
            status = "good"
        elif health_score > 0.4:
            status = "fair"
        elif health_score > 0.2:
            status = "poor"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_score": health_score,
            "issues": issues,
            "recommendations": self._generate_health_recommendations(health_score, issues)
        }
    
    def _generate_health_recommendations(self, health_score: float, issues: List[str]) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []
        
        if "High CPU usage" in issues:
            recommendations.append("Close unnecessary applications or processes")
        
        if "Critical memory usage" in issues:
            recommendations.append("Free up memory by closing unused applications")
        
        if "Low disk space" in issues:
            recommendations.append("Clean up temporary files and free disk space")
        
        if health_score < 0.5:
            recommendations.append("Consider system restart or maintenance")
        
        return recommendations
    
    def get_context_statistics(self) -> Dict[str, Any]:
        """Get comprehensive context statistics."""
        return {
            "monitoring_cycles": self.monitoring_cycles,
            "changes_detected": self.changes_detected,
            "patterns_learned": self.patterns_learned,
            "adaptations_triggered": self.adaptations_triggered,
            "active_applications": len(self.active_applications),
            "learned_patterns": len(self.learned_patterns),
            "monitoring_active": self.monitoring_active,
            "system_state_history_size": len(self.system_state_history),
            "recent_changes": len([c for c in self.detected_changes 
                                 if (datetime.now() - c.timestamp).hours < 1]),
            "baseline_metrics": self.baseline_metrics.copy()
        }
    
    def process(self, context: Context) -> Dict[str, Any]:
        """Process context for enhanced context awareness."""
        try:
            # Get comprehensive context
            comprehensive_context = self.get_comprehensive_context()
            
            # Add statistics
            comprehensive_context["statistics"] = self.get_context_statistics()
            
            return {
                "success": True,
                "data": comprehensive_context,
                "metadata": {"component": "EnhancedContextEngine", "operation": "context_analysis"}
            }
            
        except Exception as e:
            logger.error(f"Error in process method: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {"component": "EnhancedContextEngine", "operation": "process"}
            }