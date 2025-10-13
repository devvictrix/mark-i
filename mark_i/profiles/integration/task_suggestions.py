"""
AI Task Suggestion Engine

AI-powered system for analyzing user behavior and suggesting relevant
automation profiles and tasks based on patterns and context.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass

from ..models.profile import AutomationProfile
from ..profile_manager import ProfileManager
from ..templates.template_manager import TemplateManager


@dataclass
class TaskSuggestion:
    """Individual task suggestion"""
    suggestion_id: str
    title: str
    description: str
    confidence: float
    suggestion_type: str  # 'profile', 'template', 'optimization', 'automation'
    profile_id: Optional[str] = None
    template_category: Optional[str] = None
    template_variant: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    reasoning: Optional[str] = None
    priority: int = 1  # 1=low, 2=medium, 3=high
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'suggestion_id': self.suggestion_id,
            'title': self.title,
            'description': self.description,
            'confidence': self.confidence,
            'suggestion_type': self.suggestion_type,
            'profile_id': self.profile_id,
            'template_category': self.template_category,
            'template_variant': self.template_variant,
            'action_data': self.action_data,
            'reasoning': self.reasoning,
            'priority': self.priority
        }


class UserBehaviorAnalyzer:
    """Analyzes user behavior patterns for task suggestions"""
    
    def __init__(self, data_dir: str = None):
        self.logger = logging.getLogger("mark_i.profiles.integration.behavior_analyzer")
        
        # Data storage
        self.data_dir = Path(data_dir) if data_dir else Path.home() / ".mark_i" / "behavior_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Behavior tracking
        self.activity_log_file = self.data_dir / "activity_log.json"
        self.patterns_file = self.data_dir / "behavior_patterns.json"
        
        # Load existing data
        self.activity_log = self._load_activity_log()
        self.behavior_patterns = self._load_behavior_patterns()
        
        self.logger.info("UserBehaviorAnalyzer initialized")
    
    def _load_activity_log(self) -> List[Dict[str, Any]]:
        """Load user activity log"""
        try:
            if self.activity_log_file.exists():
                with open(self.activity_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            self.logger.error(f"Failed to load activity log: {e}")
            return []
    
    def _load_behavior_patterns(self) -> Dict[str, Any]:
        """Load analyzed behavior patterns"""
        try:
            if self.patterns_file.exists():
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to load behavior patterns: {e}")
            return {}
    
    def _save_activity_log(self):
        """Save activity log"""
        try:
            with open(self.activity_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.activity_log, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save activity log: {e}")
    
    def _save_behavior_patterns(self):
        """Save behavior patterns"""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.behavior_patterns, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save behavior patterns: {e}")
    
    def log_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log user activity"""
        try:
            activity = {
                'timestamp': datetime.now().isoformat(),
                'type': activity_type,
                'details': details
            }
            
            self.activity_log.append(activity)
            
            # Keep only recent activities (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            self.activity_log = [
                activity for activity in self.activity_log
                if datetime.fromisoformat(activity['timestamp']) > cutoff_date
            ]
            
            self._save_activity_log()
            
        except Exception as e:
            self.logger.error(f"Failed to log activity: {e}")
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        try:
            patterns = {
                'most_active_hours': self._analyze_active_hours(),
                'frequent_applications': self._analyze_frequent_applications(),
                'common_tasks': self._analyze_common_tasks(),
                'automation_opportunities': self._identify_automation_opportunities(),
                'usage_trends': self._analyze_usage_trends()
            }
            
            self.behavior_patterns = patterns
            self._save_behavior_patterns()
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to analyze patterns: {e}")
            return {}
    
    def _analyze_active_hours(self) -> List[int]:
        """Analyze most active hours of the day"""
        hour_counts = {}
        
        for activity in self.activity_log:
            try:
                timestamp = datetime.fromisoformat(activity['timestamp'])
                hour = timestamp.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            except Exception:
                continue
        
        # Return top 5 most active hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:5]]
    
    def _analyze_frequent_applications(self) -> List[Dict[str, Any]]:
        """Analyze frequently used applications"""
        app_counts = {}
        
        for activity in self.activity_log:
            if activity['type'] == 'application_focus':
                app_name = activity['details'].get('application')
                if app_name:
                    app_counts[app_name] = app_counts.get(app_name, 0) + 1
        
        # Return top 10 applications
        sorted_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'name': app, 'count': count} for app, count in sorted_apps[:10]]
    
    def _analyze_common_tasks(self) -> List[Dict[str, Any]]:
        """Analyze common task patterns"""
        task_patterns = []
        
        # Look for repeated sequences of actions
        # This is a simplified implementation
        for i in range(len(self.activity_log) - 2):
            sequence = self.activity_log[i:i+3]
            pattern = [activity['type'] for activity in sequence]
            
            # Look for automation-worthy patterns
            if self._is_automation_worthy_pattern(pattern):
                task_patterns.append({
                    'pattern': pattern,
                    'frequency': self._count_pattern_frequency(pattern),
                    'last_seen': sequence[-1]['timestamp']
                })
        
        return task_patterns
    
    def _identify_automation_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for automation"""
        opportunities = []
        
        # Repetitive click patterns
        click_sequences = self._find_repetitive_click_sequences()
        for sequence in click_sequences:
            opportunities.append({
                'type': 'repetitive_clicks',
                'description': f"Repetitive clicking pattern detected ({len(sequence)} clicks)",
                'confidence': 0.7,
                'automation_potential': 'high'
            })
        
        # Frequent application switching
        app_switches = self._analyze_application_switching()
        if app_switches['frequency'] > 10:  # More than 10 switches per day
            opportunities.append({
                'type': 'application_switching',
                'description': f"Frequent application switching detected",
                'confidence': 0.6,
                'automation_potential': 'medium'
            })
        
        # Form filling patterns
        form_patterns = self._detect_form_filling_patterns()
        for pattern in form_patterns:
            opportunities.append({
                'type': 'form_filling',
                'description': f"Repetitive form filling in {pattern['application']}",
                'confidence': 0.8,
                'automation_potential': 'high'
            })
        
        return opportunities
    
    def _analyze_usage_trends(self) -> Dict[str, Any]:
        """Analyze usage trends over time"""
        now = datetime.now()
        
        # Weekly trend
        weekly_activity = {}
        for activity in self.activity_log:
            try:
                timestamp = datetime.fromisoformat(activity['timestamp'])
                if (now - timestamp).days <= 7:
                    day = timestamp.strftime('%A')
                    weekly_activity[day] = weekly_activity.get(day, 0) + 1
            except Exception:
                continue
        
        # Daily trend
        daily_activity = {}
        for activity in self.activity_log:
            try:
                timestamp = datetime.fromisoformat(activity['timestamp'])
                if (now - timestamp).days <= 30:
                    date = timestamp.strftime('%Y-%m-%d')
                    daily_activity[date] = daily_activity.get(date, 0) + 1
            except Exception:
                continue
        
        return {
            'weekly_activity': weekly_activity,
            'daily_activity': daily_activity,
            'total_activities': len(self.activity_log),
            'average_daily_activity': len(self.activity_log) / 30 if self.activity_log else 0
        }
    
    def _is_automation_worthy_pattern(self, pattern: List[str]) -> bool:
        """Check if a pattern is worth automating"""
        # Simple heuristics for automation-worthy patterns
        automation_indicators = [
            'mouse_click', 'key_press', 'application_focus', 'window_switch'
        ]
        
        return len([p for p in pattern if p in automation_indicators]) >= 2
    
    def _count_pattern_frequency(self, pattern: List[str]) -> int:
        """Count how often a pattern occurs"""
        count = 0
        for i in range(len(self.activity_log) - len(pattern) + 1):
            sequence = [self.activity_log[i+j]['type'] for j in range(len(pattern))]
            if sequence == pattern:
                count += 1
        return count
    
    def _find_repetitive_click_sequences(self) -> List[List[Dict[str, Any]]]:
        """Find repetitive click sequences"""
        click_sequences = []
        current_sequence = []
        
        for activity in self.activity_log:
            if activity['type'] == 'mouse_click':
                current_sequence.append(activity)
            else:
                if len(current_sequence) >= 3:  # At least 3 clicks
                    click_sequences.append(current_sequence)
                current_sequence = []
        
        return click_sequences
    
    def _analyze_application_switching(self) -> Dict[str, Any]:
        """Analyze application switching patterns"""
        switches = 0
        last_app = None
        
        for activity in self.activity_log:
            if activity['type'] == 'application_focus':
                current_app = activity['details'].get('application')
                if last_app and current_app != last_app:
                    switches += 1
                last_app = current_app
        
        return {
            'frequency': switches,
            'average_per_day': switches / 30 if switches > 0 else 0
        }
    
    def _detect_form_filling_patterns(self) -> List[Dict[str, Any]]:
        """Detect form filling patterns"""
        patterns = []
        
        # Look for sequences of text input in the same application
        current_app = None
        text_inputs = []
        
        for activity in self.activity_log:
            if activity['type'] == 'application_focus':
                current_app = activity['details'].get('application')
                if text_inputs and len(text_inputs) >= 3:
                    patterns.append({
                        'application': current_app,
                        'input_count': len(text_inputs)
                    })
                text_inputs = []
            elif activity['type'] == 'text_input' and current_app:
                text_inputs.append(activity)
        
        return patterns


class AITaskSuggestionEngine:
    """AI-powered task suggestion engine"""
    
    def __init__(self, data_dir: str = None):
        self.logger = logging.getLogger("mark_i.profiles.integration.task_suggestions")
        
        # Components
        self.profile_manager = ProfileManager()
        self.template_manager = TemplateManager()
        self.behavior_analyzer = UserBehaviorAnalyzer(data_dir)
        
        # Suggestion cache
        self.suggestion_cache: List[TaskSuggestion] = []
        self.last_analysis_time: Optional[datetime] = None
        
        self.logger.info("AITaskSuggestionEngine initialized")
    
    def generate_suggestions(self, force_refresh: bool = False) -> List[TaskSuggestion]:
        """Generate task suggestions based on user behavior"""
        try:
            # Check if we need to refresh suggestions
            if not force_refresh and self._should_use_cache():
                return self.suggestion_cache
            
            suggestions = []
            
            # Analyze current behavior patterns
            patterns = self.behavior_analyzer.analyze_patterns()
            
            # Generate different types of suggestions
            suggestions.extend(self._suggest_profile_executions(patterns))
            suggestions.extend(self._suggest_new_profiles(patterns))
            suggestions.extend(self._suggest_templates(patterns))
            suggestions.extend(self._suggest_optimizations(patterns))
            suggestions.extend(self._suggest_automations(patterns))
            
            # Sort by confidence and priority
            suggestions.sort(key=lambda s: (s.priority, s.confidence), reverse=True)
            
            # Cache suggestions
            self.suggestion_cache = suggestions[:20]  # Keep top 20
            self.last_analysis_time = datetime.now()
            
            self.logger.info(f"Generated {len(suggestions)} task suggestions")
            return self.suggestion_cache
            
        except Exception as e:
            self.logger.error(f"Failed to generate suggestions: {e}")
            return []
    
    def _should_use_cache(self) -> bool:
        """Check if we should use cached suggestions"""
        if not self.suggestion_cache or not self.last_analysis_time:
            return False
        
        # Refresh every hour
        return (datetime.now() - self.last_analysis_time).seconds < 3600
    
    def _suggest_profile_executions(self, patterns: Dict[str, Any]) -> List[TaskSuggestion]:
        """Suggest profile executions based on patterns"""
        suggestions = []
        
        try:
            # Get user's profiles
            profiles = self.profile_manager.list_profiles()
            
            # Analyze which profiles might be relevant
            frequent_apps = patterns.get('frequent_applications', [])
            app_names = [app['name'].lower() for app in frequent_apps]
            
            for profile in profiles:
                # Match profile target application with frequent apps
                if profile.target_application and profile.target_application.lower() in app_names:
                    confidence = 0.7
                    
                    # Boost confidence if it's a highly used app
                    for app in frequent_apps:
                        if app['name'].lower() == profile.target_application.lower():
                            if app['count'] > 10:  # Frequently used
                                confidence = 0.9
                            break
                    
                    suggestions.append(TaskSuggestion(
                        suggestion_id=f"exec_{profile.id}",
                        title=f"Execute {profile.name}",
                        description=f"Run automation for {profile.target_application}",
                        confidence=confidence,
                        suggestion_type="profile",
                        profile_id=profile.id,
                        reasoning=f"You frequently use {profile.target_application}",
                        priority=2
                    ))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to suggest profile executions: {e}")
            return []
    
    def _suggest_new_profiles(self, patterns: Dict[str, Any]) -> List[TaskSuggestion]:
        """Suggest creating new profiles based on patterns"""
        suggestions = []
        
        try:
            automation_opportunities = patterns.get('automation_opportunities', [])
            
            for opportunity in automation_opportunities:
                if opportunity['automation_potential'] == 'high':
                    suggestions.append(TaskSuggestion(
                        suggestion_id=f"new_profile_{opportunity['type']}",
                        title=f"Create {opportunity['type'].replace('_', ' ').title()} Profile",
                        description=f"Automate {opportunity['description'].lower()}",
                        confidence=opportunity['confidence'],
                        suggestion_type="automation",
                        reasoning=f"Detected repetitive pattern: {opportunity['description']}",
                        priority=3
                    ))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to suggest new profiles: {e}")
            return []
    
    def _suggest_templates(self, patterns: Dict[str, Any]) -> List[TaskSuggestion]:
        """Suggest templates based on user behavior"""
        suggestions = []
        
        try:
            frequent_apps = patterns.get('frequent_applications', [])
            
            # Template suggestions based on frequent applications
            template_mappings = {
                'outlook': ('email', 'outlook'),
                'gmail': ('email', 'gmail'),
                'chrome': ('web', 'chrome'),
                'firefox': ('web', 'firefox'),
                'explorer': ('system', 'windows'),
                'finder': ('system', 'macos')
            }
            
            for app in frequent_apps:
                app_name = app['name'].lower()
                if app_name in template_mappings and app['count'] > 5:
                    category, variant = template_mappings[app_name]
                    
                    suggestions.append(TaskSuggestion(
                        suggestion_id=f"template_{category}_{variant}",
                        title=f"Create {category.title()} Automation",
                        description=f"Use {variant.title()} template for {category} automation",
                        confidence=0.6,
                        suggestion_type="template",
                        template_category=category,
                        template_variant=variant,
                        reasoning=f"You frequently use {app['name']}",
                        priority=1
                    ))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to suggest templates: {e}")
            return []
    
    def _suggest_optimizations(self, patterns: Dict[str, Any]) -> List[TaskSuggestion]:
        """Suggest profile optimizations"""
        suggestions = []
        
        try:
            # Get existing profiles
            profiles = self.profile_manager.list_profiles()
            
            for profile in profiles:
                # Suggest optimizations based on profile complexity
                if len(profile.regions) > 15:
                    suggestions.append(TaskSuggestion(
                        suggestion_id=f"optimize_{profile.id}_regions",
                        title=f"Optimize {profile.name} Regions",
                        description="Reduce number of regions for better performance",
                        confidence=0.5,
                        suggestion_type="optimization",
                        profile_id=profile.id,
                        reasoning="Profile has many regions which may impact performance",
                        priority=1
                    ))
                
                if len(profile.rules) > 8:
                    suggestions.append(TaskSuggestion(
                        suggestion_id=f"optimize_{profile.id}_rules",
                        title=f"Optimize {profile.name} Rules",
                        description="Consider splitting complex rules for better maintainability",
                        confidence=0.4,
                        suggestion_type="optimization",
                        profile_id=profile.id,
                        reasoning="Profile has many rules which may be complex to maintain",
                        priority=1
                    ))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to suggest optimizations: {e}")
            return []
    
    def _suggest_automations(self, patterns: Dict[str, Any]) -> List[TaskSuggestion]:
        """Suggest automation opportunities"""
        suggestions = []
        
        try:
            common_tasks = patterns.get('common_tasks', [])
            
            for task in common_tasks:
                if task['frequency'] > 3:  # Occurs more than 3 times
                    suggestions.append(TaskSuggestion(
                        suggestion_id=f"automate_{hash(str(task['pattern']))}",
                        title="Automate Repetitive Task",
                        description=f"Create automation for {' → '.join(task['pattern'])}",
                        confidence=0.6,
                        suggestion_type="automation",
                        action_data={'pattern': task['pattern']},
                        reasoning=f"Task pattern occurs {task['frequency']} times",
                        priority=2
                    ))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Failed to suggest automations: {e}")
            return []
    
    def get_suggestions_by_type(self, suggestion_type: str) -> List[TaskSuggestion]:
        """Get suggestions filtered by type"""
        return [s for s in self.suggestion_cache if s.suggestion_type == suggestion_type]
    
    def get_high_confidence_suggestions(self, min_confidence: float = 0.7) -> List[TaskSuggestion]:
        """Get high confidence suggestions"""
        return [s for s in self.suggestion_cache if s.confidence >= min_confidence]
    
    def dismiss_suggestion(self, suggestion_id: str):
        """Dismiss a suggestion"""
        self.suggestion_cache = [s for s in self.suggestion_cache if s.suggestion_id != suggestion_id]
    
    def log_user_activity(self, activity_type: str, details: Dict[str, Any]):
        """Log user activity for behavior analysis"""
        self.behavior_analyzer.log_activity(activity_type, details)
    
    def get_suggestion_statistics(self) -> Dict[str, Any]:
        """Get statistics about suggestions"""
        if not self.suggestion_cache:
            return {}
        
        type_counts = {}
        confidence_sum = 0
        
        for suggestion in self.suggestion_cache:
            type_counts[suggestion.suggestion_type] = type_counts.get(suggestion.suggestion_type, 0) + 1
            confidence_sum += suggestion.confidence
        
        return {
            'total_suggestions': len(self.suggestion_cache),
            'average_confidence': confidence_sum / len(self.suggestion_cache),
            'suggestions_by_type': type_counts,
            'last_analysis': self.last_analysis_time.isoformat() if self.last_analysis_time else None
        }