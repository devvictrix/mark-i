"""
Enhanced System Context Integration for MARK-I

This module provides comprehensive system context awareness and environment monitoring
integration that connects the enhanced context engine with the main MARK-I system,
enabling intelligent adaptation and decision making based on environmental understanding.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import Context
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME
from mark_i.context.enhanced_context_engine import EnhancedContextEngine, EnvironmentChange, ContextChangeType

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".context.system_context_integration")


class IntegrationMode(Enum):
    """Integration modes for system context."""
    PASSIVE = "passive"  # Monitor only, no adaptations
    ACTIVE = "active"    # Monitor and suggest adaptations
    AUTONOMOUS = "autonomous"  # Monitor and apply adaptations automatically


class ContextScope(Enum):
    """Scope of context monitoring."""
    SYSTEM_ONLY = "system_only"
    APPLICATION_FOCUSED = "application_focused"
    COMPREHENSIVE = "comprehensive"


@dataclass
class ContextIntegrationConfig:
    """Configuration for context integration."""
    integration_mode: IntegrationMode = IntegrationMode.ACTIVE
    context_scope: ContextScope = ContextScope.COMPREHENSIVE
    monitoring_interval: float = 5.0
    adaptation_threshold: float = 0.3
    enable_predictive_adaptation: bool = True
    enable_learning: bool = True
    max_adaptation_frequency: int = 10  # per minute
    context_history_size: int = 1000


@dataclass
class SystemAdaptation:
    """Represents a system adaptation based on context."""
    adaptation_id: str
    trigger_change: EnvironmentChange
    adaptation_type: str
    description: str
    parameters: Dict[str, Any]
    confidence: float
    estimated_impact: Dict[str, float]
    timestamp: datetime
    applied: bool = False
    success: Optional[bool] = None


class SystemContextIntegration(ProcessingComponent):
    """
    Enhanced system context integration that provides comprehensive environment
    monitoring and intelligent adaptation capabilities for the MARK-I system.
    """
    
    def __init__(self, config: ComponentConfig):
        super().__init__("system_context_integration", config)
        
        # Configuration
        self.integration_config = ContextIntegrationConfig()
        if hasattr(config, 'integration_mode'):
            self.integration_config.integration_mode = IntegrationMode(config.integration_mode)
        if hasattr(config, 'context_scope'):
            self.integration_config.context_scope = ContextScope(config.context_scope)
        if hasattr(config, 'monitoring_interval'):
            self.integration_config.monitoring_interval = config.monitoring_interval
        if hasattr(config, 'adaptation_threshold'):
            self.integration_config.adaptation_threshold = config.adaptation_threshold
        
        # Initialize enhanced context engine
        self.context_engine = EnhancedContextEngine(config)
        
        # Integration state
        self.integration_active = False
        self.last_context_update = None
        self.current_system_context: Optional[Dict[str, Any]] = None
        
        # Adaptation management
        self.pending_adaptations: List[SystemAdaptation] = []
        self.applied_adaptations: List[SystemAdaptation] = []
        self.adaptation_callbacks: Dict[str, Callable] = {}
        self.adaptation_rate_limiter = {}
        
        # Context change tracking
        self.context_change_history: List[EnvironmentChange] = []
        self.context_patterns: Dict[str, Any] = {}
        
        # Threading
        self.integration_lock = threading.Lock()
        self.integration_thread: Optional[threading.Thread] = None
        self.stop_integration = threading.Event()
        
        # Statistics
        self.context_updates = 0
        self.adaptations_suggested = 0
        self.adaptations_applied = 0
        self.integration_cycles = 0
        
        logger.info("SystemContextIntegration initialized for enhanced environment monitoring")
    
    def start_integration(self) -> bool:
        """Start the system context integration."""
        try:
            if self.integration_active:
                logger.warning("System context integration already active")
                return True
            
            # Start the enhanced context engine
            if not self.context_engine.start_monitoring():
                logger.error("Failed to start enhanced context engine")
                return False
            
            # Start integration thread
            self.integration_active = True
            self.stop_integration.clear()
            
            self.integration_thread = threading.Thread(
                target=self._integration_loop,
                name="SystemContextIntegration",
                daemon=True
            )
            self.integration_thread.start()
            
            logger.info(f"System context integration started in {self.integration_config.integration_mode.value} mode")
            return True
            
        except Exception as e:
            logger.error(f"Error starting system context integration: {e}")
            return False
    
    def stop_integration(self) -> bool:
        """Stop the system context integration."""
        try:
            if not self.integration_active:
                return True
            
            # Stop integration thread
            self.integration_active = False
            self.stop_integration.set()
            
            if self.integration_thread and self.integration_thread.is_alive():
                self.integration_thread.join(timeout=10.0)
            
            # Stop context engine
            self.context_engine.stop_monitoring()
            
            logger.info("System context integration stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping system context integration: {e}")
            return False
    
    def get_current_system_context(self) -> Optional[Dict[str, Any]]:
        """Get the current comprehensive system context."""
        try:
            with self.integration_lock:
                if self.current_system_context:
                    return self.current_system_context.copy()
                
                # Get context from engine if not cached
                context = self.context_engine.get_comprehensive_context()
                if context:
                    self.current_system_context = context
                    self.last_context_update = datetime.now()
                    return context.copy()
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting current system context: {e}")
            return None
    
    def register_adaptation_callback(self, adaptation_type: str, callback: Callable[[SystemAdaptation], bool]):
        """
        Register a callback for handling specific adaptation types.
        
        Args:
            adaptation_type: Type of adaptation to handle
            callback: Function that applies the adaptation and returns success status
        """
        self.adaptation_callbacks[adaptation_type] = callback
        logger.info(f"Registered adaptation callback for type: {adaptation_type}")
    
    def suggest_adaptation(self, change: EnvironmentChange) -> Optional[SystemAdaptation]:
        """
        Suggest a system adaptation based on an environment change.
        
        Args:
            change: The environment change that triggered the adaptation
            
        Returns:
            Suggested adaptation or None if no adaptation needed
        """
        try:
            # Check if adaptation is needed
            if not self._should_suggest_adaptation(change):
                return None
            
            # Generate adaptation strategy
            adaptation = self._generate_system_adaptation(change)
            if adaptation:
                self.pending_adaptations.append(adaptation)
                self.adaptations_suggested += 1
                
                logger.info(f"Suggested adaptation: {adaptation.description}")
                return adaptation
            
            return None
            
        except Exception as e:
            logger.error(f"Error suggesting adaptation: {e}")
            return None
    
    def apply_adaptation(self, adaptation: SystemAdaptation) -> bool:
        """
        Apply a system adaptation.
        
        Args:
            adaptation: The adaptation to apply
            
        Returns:
            True if adaptation was successfully applied
        """
        try:
            # Check rate limiting
            if not self._check_adaptation_rate_limit(adaptation.adaptation_type):
                logger.warning(f"Adaptation rate limit exceeded for type: {adaptation.adaptation_type}")
                return False
            
            # Apply adaptation using registered callback
            if adaptation.adaptation_type in self.adaptation_callbacks:
                callback = self.adaptation_callbacks[adaptation.adaptation_type]
                success = callback(adaptation)
                
                adaptation.applied = True
                adaptation.success = success
                
                if success:
                    self.applied_adaptations.append(adaptation)
                    self.adaptations_applied += 1
                    self._update_adaptation_rate_limit(adaptation.adaptation_type)
                    
                    logger.info(f"Successfully applied adaptation: {adaptation.description}")
                else:
                    logger.warning(f"Failed to apply adaptation: {adaptation.description}")
                
                return success
            else:
                logger.warning(f"No callback registered for adaptation type: {adaptation.adaptation_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying adaptation: {e}")
            return False
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current context and integration status."""
        try:
            context = self.get_current_system_context()
            
            summary = {
                "integration_status": {
                    "active": self.integration_active,
                    "mode": self.integration_config.integration_mode.value,
                    "scope": self.integration_config.context_scope.value,
                    "last_update": self.last_context_update.isoformat() if self.last_context_update else None
                },
                "statistics": {
                    "context_updates": self.context_updates,
                    "adaptations_suggested": self.adaptations_suggested,
                    "adaptations_applied": self.adaptations_applied,
                    "integration_cycles": self.integration_cycles
                },
                "current_context": {
                    "environment_state": context.get("environment_state") if context else None,
                    "active_applications": len(context.get("active_applications", {})) if context else 0,
                    "recent_changes": len(context.get("recent_changes", [])) if context else 0,
                    "resource_pressure": context.get("resource_pressure") if context else None
                },
                "adaptations": {
                    "pending": len(self.pending_adaptations),
                    "applied_recently": len([a for a in self.applied_adaptations 
                                           if (datetime.now() - a.timestamp).seconds < 300])
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting context summary: {e}")
            return {"error": str(e)}
    
    def _integration_loop(self):
        """Main integration loop for context monitoring and adaptation."""
        logger.info("System context integration loop started")
        
        while not self.stop_integration.is_set():
            try:
                # Update system context
                self._update_system_context()
                
                # Process environment changes
                changes = self._get_recent_environment_changes()
                if changes:
                    self._process_environment_changes(changes)
                
                # Apply pending adaptations if in autonomous mode
                if self.integration_config.integration_mode == IntegrationMode.AUTONOMOUS:
                    self._apply_pending_adaptations()
                
                # Learn from applied adaptations
                if self.integration_config.enable_learning:
                    self._learn_from_adaptations()
                
                # Update context patterns
                self._update_context_patterns()
                
                self.integration_cycles += 1
                
            except Exception as e:
                logger.error(f"Error in integration loop: {e}")
            
            # Wait for next cycle
            self.stop_integration.wait(self.integration_config.monitoring_interval)
        
        logger.info("System context integration loop stopped")
    
    def _update_system_context(self):
        """Update the current system context."""
        try:
            context = self.context_engine.get_comprehensive_context()
            if context:
                with self.integration_lock:
                    self.current_system_context = context
                    self.last_context_update = datetime.now()
                    self.context_updates += 1
                
        except Exception as e:
            logger.error(f"Error updating system context: {e}")
    
    def _get_recent_environment_changes(self) -> List[EnvironmentChange]:
        """Get recent environment changes from the context engine."""
        try:
            # Get changes from the last monitoring interval
            cutoff_time = datetime.now() - timedelta(seconds=self.integration_config.monitoring_interval * 2)
            
            all_changes = list(self.context_engine.detected_changes)
            recent_changes = [change for change in all_changes if change.timestamp > cutoff_time]
            
            # Update change history
            for change in recent_changes:
                if change not in self.context_change_history:
                    self.context_change_history.append(change)
            
            # Keep history size manageable
            if len(self.context_change_history) > self.integration_config.context_history_size:
                self.context_change_history = self.context_change_history[-self.integration_config.context_history_size:]
            
            return recent_changes
            
        except Exception as e:
            logger.error(f"Error getting recent environment changes: {e}")
            return []
    
    def _process_environment_changes(self, changes: List[EnvironmentChange]):
        """Process environment changes and suggest adaptations."""
        try:
            for change in changes:
                # Suggest adaptation if needed
                adaptation = self.suggest_adaptation(change)
                
                # In active mode, log the suggestion
                if adaptation and self.integration_config.integration_mode == IntegrationMode.ACTIVE:
                    logger.info(f"Adaptation suggested for {change.change_type.value}: {adaptation.description}")
                
        except Exception as e:
            logger.error(f"Error processing environment changes: {e}")
    
    def _apply_pending_adaptations(self):
        """Apply pending adaptations in autonomous mode."""
        try:
            adaptations_to_apply = [a for a in self.pending_adaptations if not a.applied]
            
            for adaptation in adaptations_to_apply:
                if adaptation.confidence >= self.integration_config.adaptation_threshold:
                    self.apply_adaptation(adaptation)
                
        except Exception as e:
            logger.error(f"Error applying pending adaptations: {e}")
    
    def _learn_from_adaptations(self):
        """Learn from the success/failure of applied adaptations."""
        try:
            # Analyze recent adaptations for learning
            recent_adaptations = [a for a in self.applied_adaptations 
                                if (datetime.now() - a.timestamp).seconds < 3600]  # Last hour
            
            if len(recent_adaptations) >= 5:  # Need sufficient data
                success_rate = sum(1 for a in recent_adaptations if a.success) / len(recent_adaptations)
                
                # Adjust adaptation threshold based on success rate
                if success_rate > 0.8:
                    # High success rate, can be more aggressive
                    self.integration_config.adaptation_threshold = max(0.1, 
                        self.integration_config.adaptation_threshold - 0.05)
                elif success_rate < 0.5:
                    # Low success rate, be more conservative
                    self.integration_config.adaptation_threshold = min(0.9, 
                        self.integration_config.adaptation_threshold + 0.1)
                
                logger.debug(f"Adaptation learning: success_rate={success_rate:.2f}, "
                           f"threshold={self.integration_config.adaptation_threshold:.2f}")
                
        except Exception as e:
            logger.error(f"Error learning from adaptations: {e}")
    
    def _update_context_patterns(self):
        """Update learned context patterns."""
        try:
            # Learn patterns from context engine
            patterns = self.context_engine.learn_context_patterns()
            
            # Update local pattern cache
            for pattern in patterns:
                self.context_patterns[pattern.pattern_id] = {
                    "signature": pattern.pattern_signature,
                    "frequency": pattern.frequency,
                    "success_rate": pattern.success_rate,
                    "last_seen": pattern.last_seen.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error updating context patterns: {e}")
    
    def _should_suggest_adaptation(self, change: EnvironmentChange) -> bool:
        """Determine if an adaptation should be suggested for a change."""
        try:
            # Check change severity
            if change.severity in ["low"]:
                return False
            
            # Check if adaptation is already suggested for similar change
            similar_adaptations = [a for a in self.pending_adaptations 
                                 if a.trigger_change.change_type == change.change_type
                                 and (datetime.now() - a.timestamp).seconds < 300]
            
            if similar_adaptations:
                return False
            
            # Check impact assessment
            impact = change.impact_assessment
            if impact.get("adaptation_required", False):
                return True
            
            # Check if impact exceeds threshold
            total_impact = (impact.get("performance_impact", 0) + 
                          impact.get("user_experience_impact", 0) + 
                          impact.get("system_stability_impact", 0)) / 3
            
            return total_impact >= self.integration_config.adaptation_threshold
            
        except Exception as e:
            logger.error(f"Error checking if adaptation should be suggested: {e}")
            return False
    
    def _generate_system_adaptation(self, change: EnvironmentChange) -> Optional[SystemAdaptation]:
        """Generate a system adaptation for an environment change."""
        try:
            adaptation_id = f"adapt_{change.change_type.value}_{int(time.time() * 1000)}"
            
            # Determine adaptation type and parameters based on change type
            if change.change_type == ContextChangeType.SYSTEM_RESOURCE:
                return self._generate_resource_adaptation(adaptation_id, change)
            elif change.change_type == ContextChangeType.APPLICATION_FOCUS:
                return self._generate_focus_adaptation(adaptation_id, change)
            elif change.change_type == ContextChangeType.USER_ACTIVITY:
                return self._generate_activity_adaptation(adaptation_id, change)
            else:
                return self._generate_generic_adaptation(adaptation_id, change)
                
        except Exception as e:
            logger.error(f"Error generating system adaptation: {e}")
            return None
    
    def _generate_resource_adaptation(self, adaptation_id: str, change: EnvironmentChange) -> SystemAdaptation:
        """Generate adaptation for system resource changes."""
        if change.severity in ["high", "critical"]:
            return SystemAdaptation(
                adaptation_id=adaptation_id,
                trigger_change=change,
                adaptation_type="resource_optimization",
                description="Optimize system resource usage due to high resource pressure",
                parameters={
                    "reduce_monitoring_frequency": True,
                    "defer_non_critical_operations": True,
                    "optimize_memory_usage": True
                },
                confidence=0.8,
                estimated_impact={
                    "performance_improvement": 0.3,
                    "resource_savings": 0.4,
                    "user_experience_impact": -0.1
                },
                timestamp=datetime.now()
            )
        else:
            return SystemAdaptation(
                adaptation_id=adaptation_id,
                trigger_change=change,
                adaptation_type="resource_monitoring",
                description="Increase resource monitoring due to resource changes",
                parameters={
                    "increase_monitoring_frequency": True,
                    "enable_detailed_tracking": True
                },
                confidence=0.6,
                estimated_impact={
                    "monitoring_accuracy": 0.2,
                    "resource_overhead": 0.1
                },
                timestamp=datetime.now()
            )
    
    def _generate_focus_adaptation(self, adaptation_id: str, change: EnvironmentChange) -> SystemAdaptation:
        """Generate adaptation for application focus changes."""
        return SystemAdaptation(
            adaptation_id=adaptation_id,
            trigger_change=change,
            adaptation_type="focus_adjustment",
            description="Adjust monitoring focus to new application context",
            parameters={
                "update_focus_targets": True,
                "adapt_monitoring_strategy": True,
                "learn_application_patterns": True
            },
            confidence=0.7,
            estimated_impact={
                "monitoring_relevance": 0.4,
                "processing_efficiency": 0.2
            },
            timestamp=datetime.now()
        )
    
    def _generate_activity_adaptation(self, adaptation_id: str, change: EnvironmentChange) -> SystemAdaptation:
        """Generate adaptation for user activity changes."""
        activity_level = change.after_state.get("activity_after", 0.5)
        
        if activity_level > 0.7:  # High activity
            return SystemAdaptation(
                adaptation_id=adaptation_id,
                trigger_change=change,
                adaptation_type="high_activity_mode",
                description="Switch to high activity monitoring mode",
                parameters={
                    "increase_responsiveness": True,
                    "reduce_autonomous_actions": True,
                    "enhance_user_interaction_monitoring": True
                },
                confidence=0.6,
                estimated_impact={
                    "user_experience": 0.3,
                    "system_responsiveness": 0.4,
                    "resource_usage": 0.2
                },
                timestamp=datetime.now()
            )
        else:  # Low activity
            return SystemAdaptation(
                adaptation_id=adaptation_id,
                trigger_change=change,
                adaptation_type="low_activity_mode",
                description="Switch to low activity optimization mode",
                parameters={
                    "increase_autonomous_operation": True,
                    "perform_background_optimizations": True,
                    "reduce_monitoring_frequency": True
                },
                confidence=0.6,
                estimated_impact={
                    "resource_efficiency": 0.3,
                    "background_optimization": 0.4
                },
                timestamp=datetime.now()
            )
    
    def _generate_generic_adaptation(self, adaptation_id: str, change: EnvironmentChange) -> SystemAdaptation:
        """Generate generic adaptation for other change types."""
        return SystemAdaptation(
            adaptation_id=adaptation_id,
            trigger_change=change,
            adaptation_type="generic_optimization",
            description=f"Generic optimization for {change.change_type.value} change",
            parameters={
                "monitor_change_impact": True,
                "adjust_system_parameters": True
            },
            confidence=0.4,
            estimated_impact={
                "system_stability": 0.1
            },
            timestamp=datetime.now()
        )
    
    def _check_adaptation_rate_limit(self, adaptation_type: str) -> bool:
        """Check if adaptation type is within rate limits."""
        current_time = datetime.now()
        minute_ago = current_time - timedelta(minutes=1)
        
        if adaptation_type not in self.adaptation_rate_limiter:
            self.adaptation_rate_limiter[adaptation_type] = []
        
        # Clean old entries
        self.adaptation_rate_limiter[adaptation_type] = [
            timestamp for timestamp in self.adaptation_rate_limiter[adaptation_type]
            if timestamp > minute_ago
        ]
        
        # Check limit
        return len(self.adaptation_rate_limiter[adaptation_type]) < self.integration_config.max_adaptation_frequency
    
    def _update_adaptation_rate_limit(self, adaptation_type: str):
        """Update rate limit tracking for adaptation type."""
        if adaptation_type not in self.adaptation_rate_limiter:
            self.adaptation_rate_limiter[adaptation_type] = []
        
        self.adaptation_rate_limiter[adaptation_type].append(datetime.now())