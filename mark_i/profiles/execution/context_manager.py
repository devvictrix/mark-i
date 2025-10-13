"""
Profile Context Manager

Manages execution context and integrates with MARK-I's Enhanced System Context
for intelligent profile execution with environmental awareness.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from ..models.profile import AutomationProfile


@dataclass
class ExecutionContext:
    """Execution context data"""
    profile: AutomationProfile
    user_variables: Dict[str, Any]
    system_context: Dict[str, Any]
    execution_history: List[Dict[str, Any]]
    start_time: datetime
    current_rule: Optional[str] = None
    current_step: Optional[str] = None


class ProfileContextManager:
    """Manages profile execution context with MARK-I integration"""
    
    def __init__(self):
        self.logger = logging.getLogger("mark_i.profiles.execution.context_manager")
        
        # Current execution context
        self.current_context: Optional[ExecutionContext] = None
        
        # Context history
        self.context_history: List[ExecutionContext] = []
        
        # Enhanced context integration
        self.enhanced_context_available = False
        self._initialize_enhanced_context()
        
        self.logger.info("ProfileContextManager initialized")
    
    def _initialize_enhanced_context(self):
        """Initialize connection to MARK-I's Enhanced System Context"""
        try:
            # Try to connect to Enhanced System Context
            # In real implementation, this would import and initialize the actual component
            # from mark_i.core.enhanced_context import EnhancedSystemContext
            # self.enhanced_context = EnhancedSystemContext()
            
            self.enhanced_context_available = True
            self.logger.info("Enhanced System Context connected")
            
        except ImportError:
            self.logger.warning("Enhanced System Context not available")
            self.enhanced_context_available = False
        except Exception as e:
            self.logger.error(f"Failed to initialize Enhanced System Context: {e}")
            self.enhanced_context_available = False
    
    def initialize_context(self, profile: AutomationProfile, 
                          user_variables: Dict[str, Any] = None) -> ExecutionContext:
        """Initialize execution context for a profile"""
        self.logger.info(f"Initializing context for profile: {profile.name}")
        
        # Gather system context
        system_context = self._gather_system_context()
        
        # Create execution context
        self.current_context = ExecutionContext(
            profile=profile,
            user_variables=user_variables or {},
            system_context=system_context,
            execution_history=[],
            start_time=datetime.now()
        )
        
        # Log context initialization
        self.logger.debug(f"Context initialized with {len(system_context)} system properties")
        
        return self.current_context
    
    def update_context(self, updates: Dict[str, Any]):
        """Update current execution context"""
        if not self.current_context:
            self.logger.warning("No active context to update")
            return
        
        # Update user variables
        if 'user_variables' in updates:
            self.current_context.user_variables.update(updates['user_variables'])
        
        # Update current rule/step
        if 'current_rule' in updates:
            self.current_context.current_rule = updates['current_rule']
        
        if 'current_step' in updates:
            self.current_context.current_step = updates['current_step']
        
        # Add to execution history
        if 'history_entry' in updates:
            self.current_context.execution_history.append(updates['history_entry'])
        
        self.logger.debug("Context updated")
    
    def get_context_variable(self, variable_name: str) -> Any:
        """Get a context variable"""
        if not self.current_context:
            return None
        
        # Check user variables first
        if variable_name in self.current_context.user_variables:
            return self.current_context.user_variables[variable_name]
        
        # Check system context
        if variable_name in self.current_context.system_context:
            return self.current_context.system_context[variable_name]
        
        # Check built-in variables
        built_in_vars = self._get_built_in_variables()
        if variable_name in built_in_vars:
            return built_in_vars[variable_name]
        
        return None
    
    def set_context_variable(self, variable_name: str, value: Any):
        """Set a context variable"""
        if not self.current_context:
            self.logger.warning("No active context to set variable")
            return
        
        self.current_context.user_variables[variable_name] = value
        self.logger.debug(f"Set context variable: {variable_name} = {value}")
    
    def get_intelligent_suggestions(self, current_step: str) -> List[Dict[str, Any]]:
        """Get intelligent suggestions based on current context"""
        if not self.enhanced_context_available or not self.current_context:
            return []
        
        try:
            # Use Enhanced System Context for intelligent suggestions
            suggestions = self._generate_context_aware_suggestions(current_step)
            
            self.logger.debug(f"Generated {len(suggestions)} intelligent suggestions")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to generate intelligent suggestions: {e}")
            return []
    
    def adapt_to_environment(self) -> Dict[str, Any]:
        """Adapt execution based on current environment"""
        if not self.current_context:
            return {}
        
        adaptations = {}
        
        try:
            # Check system resources
            system_context = self.current_context.system_context
            
            # Adapt timing based on system load
            cpu_usage = system_context.get('cpu_percent', 0)
            if cpu_usage > 80:
                adaptations['timing_multiplier'] = 1.5  # Slow down
                adaptations['reason'] = 'High CPU usage detected'
            elif cpu_usage < 20:
                adaptations['timing_multiplier'] = 0.8  # Speed up
                adaptations['reason'] = 'Low CPU usage, can speed up'
            
            # Adapt based on active applications
            active_apps = system_context.get('active_applications', [])
            target_app = self.current_context.profile.target_application
            
            if target_app and target_app not in active_apps:
                adaptations['launch_target_app'] = True
                adaptations['reason'] = f'Target application {target_app} not running'
            
            # Adapt based on time of day
            current_hour = datetime.now().hour
            if current_hour < 9 or current_hour > 17:  # Outside business hours
                adaptations['extended_timeouts'] = True
                adaptations['reason'] = 'Outside business hours, using extended timeouts'
            
            self.logger.debug(f"Generated {len(adaptations)} environment adaptations")
            return adaptations
            
        except Exception as e:
            self.logger.error(f"Failed to adapt to environment: {e}")
            return {}
    
    def get_execution_insights(self) -> Dict[str, Any]:
        """Get insights about current execution"""
        if not self.current_context:
            return {}
        
        insights = {}
        
        try:
            # Execution duration
            duration = (datetime.now() - self.current_context.start_time).total_seconds()
            insights['execution_duration'] = duration
            
            # Progress analysis
            total_rules = len(self.current_context.profile.rules)
            executed_steps = len(self.current_context.execution_history)
            insights['progress'] = {
                'total_rules': total_rules,
                'executed_steps': executed_steps,
                'estimated_completion': self._estimate_completion_time()
            }
            
            # Performance metrics
            insights['performance'] = self._analyze_performance()
            
            # Context relevance
            insights['context_relevance'] = self._analyze_context_relevance()
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate execution insights: {e}")
            return {}
    
    def cleanup_context(self):
        """Clean up execution context"""
        if self.current_context:
            # Archive current context
            self.context_history.append(self.current_context)
            
            # Keep only recent history (last 10 executions)
            if len(self.context_history) > 10:
                self.context_history = self.context_history[-10:]
            
            self.logger.info(f"Context archived for profile: {self.current_context.profile.name}")
            self.current_context = None
    
    def get_current_context(self) -> Optional[ExecutionContext]:
        """Get current execution context"""
        return self.current_context
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context"""
        if not self.current_context:
            return {}
        
        return {
            'profile_name': self.current_context.profile.name,
            'start_time': self.current_context.start_time.isoformat(),
            'current_rule': self.current_context.current_rule,
            'current_step': self.current_context.current_step,
            'user_variables_count': len(self.current_context.user_variables),
            'execution_history_count': len(self.current_context.execution_history),
            'system_context_keys': list(self.current_context.system_context.keys())
        }
    
    # Private helper methods
    
    def _gather_system_context(self) -> Dict[str, Any]:
        """Gather current system context"""
        context = {}
        
        try:
            # Basic system information
            context['timestamp'] = datetime.now().isoformat()
            context['platform'] = self._get_platform_info()
            
            # System resources
            context.update(self._get_system_resources())
            
            # Active applications
            context['active_applications'] = self._get_active_applications()
            
            # Network status
            context['network_connected'] = self._check_network_connectivity()
            
            # Screen information
            context['screen_info'] = self._get_screen_info()
            
            # Enhanced context (if available)
            if self.enhanced_context_available:
                enhanced_context = self._get_enhanced_context()
                context.update(enhanced_context)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to gather system context: {e}")
            return {'error': str(e)}
    
    def _get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        try:
            import platform
            
            return {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_system_resources(self) -> Dict[str, Any]:
        """Get system resource information"""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_active_applications(self) -> List[str]:
        """Get list of active applications"""
        try:
            import psutil
            
            apps = []
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name']:
                        apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Remove duplicates and return unique apps
            return list(set(apps))
            
        except ImportError:
            return []
        except Exception as e:
            self.logger.error(f"Failed to get active applications: {e}")
            return []
    
    def _check_network_connectivity(self) -> bool:
        """Check network connectivity"""
        try:
            import socket
            
            # Try to connect to a reliable server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
            
        except Exception:
            return False
    
    def _get_screen_info(self) -> Dict[str, Any]:
        """Get screen information"""
        try:
            import tkinter as tk
            
            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            
            return {
                'width': screen_width,
                'height': screen_height,
                'resolution': f"{screen_width}x{screen_height}"
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_enhanced_context(self) -> Dict[str, Any]:
        """Get enhanced context from MARK-I system"""
        # This would integrate with MARK-I's Enhanced System Context
        # For now, return placeholder data
        
        return {
            'user_behavior_patterns': {
                'most_active_hours': [9, 10, 11, 14, 15, 16],
                'preferred_applications': ['browser', 'editor', 'terminal'],
                'automation_frequency': 'daily'
            },
            'environmental_factors': {
                'lighting_conditions': 'normal',
                'system_stability': 'stable',
                'network_quality': 'good'
            },
            'contextual_hints': {
                'suggested_timing_adjustments': 1.0,
                'recommended_retry_count': 3,
                'optimal_execution_window': True
            }
        }
    
    def _get_built_in_variables(self) -> Dict[str, Any]:
        """Get built-in context variables"""
        now = datetime.now()
        
        return {
            'current_time': now.strftime('%H:%M:%S'),
            'current_date': now.strftime('%Y-%m-%d'),
            'current_datetime': now.isoformat(),
            'day_of_week': now.strftime('%A'),
            'month': now.strftime('%B'),
            'year': str(now.year),
            'timestamp': int(now.timestamp())
        }
    
    def _generate_context_aware_suggestions(self, current_step: str) -> List[Dict[str, Any]]:
        """Generate intelligent suggestions based on context"""
        suggestions = []
        
        if not self.current_context:
            return suggestions
        
        # Analyze current system state
        system_context = self.current_context.system_context
        
        # Suggest timing adjustments based on system load
        cpu_usage = system_context.get('cpu_percent', 0)
        if cpu_usage > 80:
            suggestions.append({
                'type': 'timing_adjustment',
                'suggestion': 'Consider adding delays between actions due to high CPU usage',
                'confidence': 0.8,
                'impact': 'performance'
            })
        
        # Suggest application focus based on active apps
        active_apps = system_context.get('active_applications', [])
        target_app = self.current_context.profile.target_application
        
        if target_app and target_app not in [app.lower() for app in active_apps]:
            suggestions.append({
                'type': 'application_launch',
                'suggestion': f'Target application "{target_app}" is not running. Consider launching it first.',
                'confidence': 0.9,
                'impact': 'reliability'
            })
        
        # Suggest error handling based on execution history
        failed_steps = [entry for entry in self.current_context.execution_history 
                       if entry.get('status') == 'failed']
        
        if len(failed_steps) > 2:
            suggestions.append({
                'type': 'error_handling',
                'suggestion': 'Multiple step failures detected. Consider adding error recovery actions.',
                'confidence': 0.7,
                'impact': 'reliability'
            })
        
        return suggestions
    
    def _estimate_completion_time(self) -> Optional[float]:
        """Estimate remaining execution time"""
        if not self.current_context:
            return None
        
        try:
            # Simple estimation based on average step time
            history = self.current_context.execution_history
            if len(history) < 2:
                return None
            
            # Calculate average step duration
            total_duration = 0
            step_count = 0
            
            for entry in history:
                if 'duration' in entry:
                    total_duration += entry['duration']
                    step_count += 1
            
            if step_count == 0:
                return None
            
            avg_step_duration = total_duration / step_count
            
            # Estimate remaining steps
            total_rules = len(self.current_context.profile.rules)
            executed_rules = len([entry for entry in history if entry.get('type') == 'rule'])
            remaining_rules = max(0, total_rules - executed_rules)
            
            # Rough estimation (assuming average of 3 steps per rule)
            estimated_remaining_steps = remaining_rules * 3
            estimated_time = estimated_remaining_steps * avg_step_duration
            
            return estimated_time
            
        except Exception as e:
            self.logger.error(f"Failed to estimate completion time: {e}")
            return None
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze execution performance"""
        if not self.current_context:
            return {}
        
        try:
            history = self.current_context.execution_history
            
            if not history:
                return {'status': 'no_data'}
            
            # Calculate performance metrics
            total_steps = len(history)
            successful_steps = len([entry for entry in history if entry.get('status') == 'success'])
            failed_steps = total_steps - successful_steps
            
            # Calculate average step duration
            durations = [entry.get('duration', 0) for entry in history if 'duration' in entry]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            return {
                'total_steps': total_steps,
                'successful_steps': successful_steps,
                'failed_steps': failed_steps,
                'success_rate': successful_steps / total_steps if total_steps > 0 else 0,
                'average_step_duration': avg_duration,
                'performance_trend': self._calculate_performance_trend(history)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze performance: {e}")
            return {'error': str(e)}
    
    def _analyze_context_relevance(self) -> Dict[str, Any]:
        """Analyze how well the context matches the execution"""
        if not self.current_context:
            return {}
        
        relevance_score = 0.5  # Base score
        factors = []
        
        try:
            # Check if target application is running
            target_app = self.current_context.profile.target_application
            active_apps = self.current_context.system_context.get('active_applications', [])
            
            if target_app and target_app in [app.lower() for app in active_apps]:
                relevance_score += 0.2
                factors.append('target_application_active')
            
            # Check system resources
            cpu_usage = self.current_context.system_context.get('cpu_percent', 0)
            if cpu_usage < 50:  # Good system performance
                relevance_score += 0.1
                factors.append('good_system_performance')
            
            # Check network connectivity if needed
            if self.current_context.system_context.get('network_connected', False):
                relevance_score += 0.1
                factors.append('network_available')
            
            # Check time appropriateness
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 17:  # Business hours
                relevance_score += 0.1
                factors.append('business_hours')
            
            return {
                'relevance_score': min(1.0, relevance_score),
                'contributing_factors': factors,
                'recommendations': self._get_relevance_recommendations(relevance_score)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze context relevance: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_trend(self, history: List[Dict[str, Any]]) -> str:
        """Calculate performance trend from execution history"""
        if len(history) < 4:
            return 'insufficient_data'
        
        try:
            # Split history into two halves
            mid_point = len(history) // 2
            first_half = history[:mid_point]
            second_half = history[mid_point:]
            
            # Calculate success rates for each half
            first_success_rate = len([e for e in first_half if e.get('status') == 'success']) / len(first_half)
            second_success_rate = len([e for e in second_half if e.get('status') == 'success']) / len(second_half)
            
            # Determine trend
            if second_success_rate > first_success_rate + 0.1:
                return 'improving'
            elif second_success_rate < first_success_rate - 0.1:
                return 'declining'
            else:
                return 'stable'
                
        except Exception:
            return 'unknown'
    
    def _get_relevance_recommendations(self, relevance_score: float) -> List[str]:
        """Get recommendations based on context relevance"""
        recommendations = []
        
        if relevance_score < 0.3:
            recommendations.append('Consider waiting for better execution conditions')
            recommendations.append('Check if target applications are available')
        elif relevance_score < 0.6:
            recommendations.append('Execution conditions are marginal - monitor closely')
            recommendations.append('Consider adding additional error handling')
        else:
            recommendations.append('Execution conditions are favorable')
        
        return recommendations