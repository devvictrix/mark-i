"""
Strategic Planner for MARK-I Agency Core.

This module provides strategic planning capabilities including goal decomposition,
strategic knowledge management, and long-term planning for the Agency Core.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from mark_i.core.base_component import BaseComponent
from mark_i.core.interfaces import Goal, Priority, Context
from mark_i.core.architecture_config import ComponentConfig

logger = logging.getLogger("mark_i.agency.strategic_planner")


class StrategicGoalType(Enum):
    """Types of strategic goals."""
    PRODUCTIVITY_OPTIMIZATION = "productivity_optimization"
    WORKFLOW_AUTOMATION = "workflow_automation"
    USER_ASSISTANCE = "user_assistance"
    SYSTEM_OPTIMIZATION = "system_optimization"
    LEARNING_IMPROVEMENT = "learning_improvement"


class PlanningHorizon(Enum):
    """Planning time horizons."""
    IMMEDIATE = "immediate"  # Next few minutes
    SHORT_TERM = "short_term"  # Next hour
    MEDIUM_TERM = "medium_term"  # Next few hours
    LONG_TERM = "long_term"  # Next day or more


@dataclass
class StrategicGoal:
    """Represents a strategic goal with decomposition."""
    id: str
    type: StrategicGoalType
    description: str
    priority: Priority
    horizon: PlanningHorizon
    success_criteria: List[str]
    sub_goals: List[str]  # IDs of sub-goals
    dependencies: List[str]  # IDs of dependent goals
    context_requirements: Dict[str, Any]
    estimated_effort: float  # 0.0 to 1.0
    estimated_benefit: float  # 0.0 to 1.0
    created_at: datetime
    target_completion: Optional[datetime] = None
    status: str = "active"  # active, completed, paused, cancelled
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StrategicPlan:
    """Represents a strategic plan with multiple goals."""
    id: str
    name: str
    description: str
    goals: List[str]  # Goal IDs
    priority: Priority
    created_at: datetime
    target_completion: Optional[datetime] = None
    status: str = "active"
    success_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.success_metrics is None:
            self.success_metrics = {}


@dataclass
class KnowledgePattern:
    """Represents a learned knowledge pattern."""
    id: str
    pattern_type: str
    description: str
    context_triggers: List[str]
    success_indicators: List[str]
    failure_indicators: List[str]
    confidence: float
    usage_count: int
    last_used: datetime
    effectiveness_score: float


class StrategicPlanner(BaseComponent):
    """
    Strategic planning component for the Agency Core.
    
    Handles goal decomposition, strategic knowledge management,
    and long-term planning capabilities.
    """
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize the Strategic Planner."""
        super().__init__("strategic_planner", config)
        
        # Strategic goals and plans
        self.strategic_goals: Dict[str, StrategicGoal] = {}
        self.strategic_plans: Dict[str, StrategicPlan] = {}
        self.goal_counter = 0
        self.plan_counter = 0
        
        # Knowledge management
        self.knowledge_patterns: Dict[str, KnowledgePattern] = {}
        self.pattern_counter = 0
        
        # User preference tracking
        self.user_preferences: Dict[str, Any] = {
            'automation_level': 0.5,
            'interruption_tolerance': 0.5,
            'learning_pace': 0.5,
            'preferred_communication_style': 'balanced',
            'goal_priorities': {},
            'context_preferences': {}
        }
        
        # Strategic knowledge base
        self.strategic_knowledge: Dict[str, Any] = {
            'workflow_patterns': [],
            'success_strategies': {},
            'failure_patterns': [],
            'context_associations': {},
            'optimization_opportunities': []
        }
        
    def _initialize_component(self) -> bool:
        """Initialize the Strategic Planner component."""
        try:
            # Load any persisted strategic knowledge
            self._load_strategic_knowledge()
            
            # Initialize default strategic goals
            self._initialize_default_goals()
            
            self.logger.info("Strategic Planner initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Strategic Planner: {e}")
            return False
    
    def create_strategic_goal(self, 
                            goal_type: StrategicGoalType,
                            description: str,
                            priority: Priority = Priority.MEDIUM,
                            horizon: PlanningHorizon = PlanningHorizon.SHORT_TERM,
                            success_criteria: Optional[List[str]] = None,
                            context_requirements: Optional[Dict[str, Any]] = None) -> StrategicGoal:
        """Create a new strategic goal."""
        try:
            goal = StrategicGoal(
                id=f"goal_{self.goal_counter}",
                type=goal_type,
                description=description,
                priority=priority,
                horizon=horizon,
                success_criteria=success_criteria or [],
                sub_goals=[],
                dependencies=[],
                context_requirements=context_requirements or {},
                estimated_effort=0.5,  # Default moderate effort
                estimated_benefit=0.5,  # Default moderate benefit
                created_at=datetime.now()
            )
            
            self.goal_counter += 1
            self.strategic_goals[goal.id] = goal
            
            self.logger.info(f"Created strategic goal: {goal.description}")
            
            # Notify observers
            self._notify_observers({
                'type': 'strategic_goal_created',
                'goal': goal.to_dict(),
                'timestamp': datetime.now().isoformat()
            })
            
            return goal
            
        except Exception as e:
            self.logger.error(f"Failed to create strategic goal: {e}")
            raise
    
    def decompose_goal(self, goal_id: str, context: Optional[Context] = None) -> List[StrategicGoal]:
        """Decompose a strategic goal into sub-goals."""
        try:
            if goal_id not in self.strategic_goals:
                raise ValueError(f"Goal {goal_id} not found")
            
            parent_goal = self.strategic_goals[goal_id]
            sub_goals = []
            
            # Goal decomposition based on type and context
            if parent_goal.type == StrategicGoalType.PRODUCTIVITY_OPTIMIZATION:
                sub_goals.extend(self._decompose_productivity_goal(parent_goal, context))
            elif parent_goal.type == StrategicGoalType.WORKFLOW_AUTOMATION:
                sub_goals.extend(self._decompose_workflow_goal(parent_goal, context))
            elif parent_goal.type == StrategicGoalType.USER_ASSISTANCE:
                sub_goals.extend(self._decompose_assistance_goal(parent_goal, context))
            elif parent_goal.type == StrategicGoalType.SYSTEM_OPTIMIZATION:
                sub_goals.extend(self._decompose_system_goal(parent_goal, context))
            elif parent_goal.type == StrategicGoalType.LEARNING_IMPROVEMENT:
                sub_goals.extend(self._decompose_learning_goal(parent_goal, context))
            
            # Store sub-goals and update parent
            for sub_goal in sub_goals:
                self.strategic_goals[sub_goal.id] = sub_goal
                parent_goal.sub_goals.append(sub_goal.id)
            
            self.logger.info(f"Decomposed goal {goal_id} into {len(sub_goals)} sub-goals")
            
            return sub_goals
            
        except Exception as e:
            self.logger.error(f"Failed to decompose goal {goal_id}: {e}")
            return []
    
    def create_strategic_plan(self, 
                            name: str,
                            description: str,
                            goal_ids: List[str],
                            priority: Priority = Priority.MEDIUM) -> StrategicPlan:
        """Create a strategic plan from multiple goals."""
        try:
            # Validate all goals exist
            for goal_id in goal_ids:
                if goal_id not in self.strategic_goals:
                    raise ValueError(f"Goal {goal_id} not found")
            
            plan = StrategicPlan(
                id=f"plan_{self.plan_counter}",
                name=name,
                description=description,
                goals=goal_ids,
                priority=priority,
                created_at=datetime.now()
            )
            
            self.plan_counter += 1
            self.strategic_plans[plan.id] = plan
            
            # Calculate plan metrics
            self._calculate_plan_metrics(plan)
            
            self.logger.info(f"Created strategic plan: {plan.name}")
            
            # Notify observers
            self._notify_observers({
                'type': 'strategic_plan_created',
                'plan': asdict(plan),
                'timestamp': datetime.now().isoformat()
            })
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Failed to create strategic plan: {e}")
            raise
    
    def update_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences based on interactions."""
        try:
            # Merge new preferences with existing ones
            for key, value in preferences.items():
                if key in self.user_preferences:
                    if isinstance(self.user_preferences[key], dict) and isinstance(value, dict):
                        self.user_preferences[key].update(value)
                    else:
                        self.user_preferences[key] = value
                else:
                    self.user_preferences[key] = value
            
            # Validate preference values
            self._validate_preferences()
            
            self.logger.info(f"Updated user preferences: {list(preferences.keys())}")
            
            # Notify observers
            self._notify_observers({
                'type': 'user_preferences_updated',
                'updated_keys': list(preferences.keys()),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Failed to update user preferences: {e}")
    
    def learn_from_success(self, context: Context, action_taken: str, outcome: Dict[str, Any]) -> None:
        """Learn from successful actions to improve future planning."""
        try:
            # Extract pattern from successful action
            pattern = KnowledgePattern(
                id=f"pattern_{self.pattern_counter}",
                pattern_type="success",
                description=f"Successful {action_taken}",
                context_triggers=self._extract_context_triggers(context),
                success_indicators=[outcome.get('indicator', 'positive_outcome')],
                failure_indicators=[],
                confidence=0.7,  # Initial confidence
                usage_count=1,
                last_used=datetime.now(),
                effectiveness_score=outcome.get('effectiveness', 0.8)
            )
            
            self.pattern_counter += 1
            self.knowledge_patterns[pattern.id] = pattern
            
            # Update strategic knowledge
            self.strategic_knowledge['success_strategies'][action_taken] = {
                'pattern_id': pattern.id,
                'success_rate': outcome.get('success_rate', 0.8),
                'context': asdict(context),
                'learned_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Learned success pattern: {pattern.description}")
            
        except Exception as e:
            self.logger.error(f"Failed to learn from success: {e}")
    
    def learn_from_failure(self, context: Context, action_taken: str, failure_reason: str) -> None:
        """Learn from failures to avoid similar mistakes."""
        try:
            # Record failure pattern
            failure_pattern = {
                'action': action_taken,
                'context': asdict(context),
                'failure_reason': failure_reason,
                'timestamp': datetime.now().isoformat()
            }
            
            self.strategic_knowledge['failure_patterns'].append(failure_pattern)
            
            # Update existing patterns if they exist
            for pattern in self.knowledge_patterns.values():
                if action_taken in pattern.description:
                    pattern.failure_indicators.append(failure_reason)
                    pattern.confidence = max(pattern.confidence - 0.1, 0.1)
            
            self.logger.info(f"Learned failure pattern: {action_taken} -> {failure_reason}")
            
        except Exception as e:
            self.logger.error(f"Failed to learn from failure: {e}")
    
    def prioritize_suggestions(self, suggestions: List[Dict[str, Any]], context: Context) -> List[Dict[str, Any]]:
        """Prioritize suggestions based on strategic knowledge and user preferences."""
        try:
            prioritized = []
            
            for suggestion in suggestions:
                # Calculate priority score
                priority_score = self._calculate_suggestion_priority(suggestion, context)
                suggestion['priority_score'] = priority_score
                prioritized.append(suggestion)
            
            # Sort by priority score (highest first)
            prioritized.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
            
            self.logger.debug(f"Prioritized {len(suggestions)} suggestions")
            
            return prioritized
            
        except Exception as e:
            self.logger.error(f"Failed to prioritize suggestions: {e}")
            return suggestions
    
    def filter_suggestions(self, suggestions: List[Dict[str, Any]], context: Context) -> List[Dict[str, Any]]:
        """Filter suggestions based on user preferences and context."""
        try:
            filtered = []
            
            for suggestion in suggestions:
                if self._should_include_suggestion(suggestion, context):
                    filtered.append(suggestion)
                else:
                    self.logger.debug(f"Filtered out suggestion: {suggestion.get('title', 'Unknown')}")
            
            self.logger.info(f"Filtered {len(suggestions)} suggestions to {len(filtered)}")
            
            return filtered
            
        except Exception as e:
            self.logger.error(f"Failed to filter suggestions: {e}")
            return suggestions
    
    def get_strategic_insights(self) -> Dict[str, Any]:
        """Get strategic insights based on accumulated knowledge."""
        try:
            insights = {
                'user_behavior_patterns': self._analyze_user_patterns(),
                'optimization_opportunities': self._identify_optimization_opportunities(),
                'learning_recommendations': self._generate_learning_recommendations(),
                'strategic_priorities': self._assess_strategic_priorities(),
                'knowledge_gaps': self._identify_knowledge_gaps()
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to generate strategic insights: {e}")
            return {}
    
    # Private helper methods
    
    def _initialize_default_goals(self) -> None:
        """Initialize default strategic goals."""
        try:
            # Create default productivity optimization goal
            self.create_strategic_goal(
                goal_type=StrategicGoalType.PRODUCTIVITY_OPTIMIZATION,
                description="Continuously optimize user productivity through intelligent automation",
                priority=Priority.HIGH,
                horizon=PlanningHorizon.LONG_TERM,
                success_criteria=[
                    "Reduce repetitive task time by 20%",
                    "Increase workflow efficiency",
                    "Maintain user satisfaction above 80%"
                ]
            )
            
            # Create default user assistance goal
            self.create_strategic_goal(
                goal_type=StrategicGoalType.USER_ASSISTANCE,
                description="Provide proactive assistance based on user context and needs",
                priority=Priority.MEDIUM,
                horizon=PlanningHorizon.MEDIUM_TERM,
                success_criteria=[
                    "Anticipate user needs accurately",
                    "Provide timely assistance",
                    "Minimize interruptions"
                ]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize default goals: {e}")
    
    def _decompose_productivity_goal(self, goal: StrategicGoal, context: Optional[Context]) -> List[StrategicGoal]:
        """Decompose productivity optimization goals."""
        sub_goals = []
        
        # Identify repetitive tasks
        sub_goals.append(StrategicGoal(
            id=f"goal_{self.goal_counter}",
            type=StrategicGoalType.WORKFLOW_AUTOMATION,
            description="Identify and automate repetitive tasks",
            priority=Priority.HIGH,
            horizon=PlanningHorizon.SHORT_TERM,
            success_criteria=["Detect repetitive patterns", "Suggest automation"],
            sub_goals=[],
            dependencies=[],
            context_requirements={'min_repetition_count': 3},
            estimated_effort=0.6,
            estimated_benefit=0.8,
            created_at=datetime.now()
        ))
        self.goal_counter += 1
        
        # Optimize workflow efficiency
        sub_goals.append(StrategicGoal(
            id=f"goal_{self.goal_counter}",
            type=StrategicGoalType.SYSTEM_OPTIMIZATION,
            description="Optimize workflow efficiency through intelligent suggestions",
            priority=Priority.MEDIUM,
            horizon=PlanningHorizon.MEDIUM_TERM,
            success_criteria=["Reduce task completion time", "Improve user satisfaction"],
            sub_goals=[],
            dependencies=[],
            context_requirements={'workflow_analysis': True},
            estimated_effort=0.7,
            estimated_benefit=0.7,
            created_at=datetime.now()
        ))
        self.goal_counter += 1
        
        return sub_goals
    
    def _decompose_workflow_goal(self, goal: StrategicGoal, context: Optional[Context]) -> List[StrategicGoal]:
        """Decompose workflow automation goals."""
        sub_goals = []
        
        # Pattern recognition
        sub_goals.append(StrategicGoal(
            id=f"goal_{self.goal_counter}",
            type=StrategicGoalType.LEARNING_IMPROVEMENT,
            description="Learn user workflow patterns",
            priority=Priority.HIGH,
            horizon=PlanningHorizon.SHORT_TERM,
            success_criteria=["Identify workflow patterns", "Build pattern database"],
            sub_goals=[],
            dependencies=[],
            context_requirements={'observation_period': 'continuous'},
            estimated_effort=0.5,
            estimated_benefit=0.9,
            created_at=datetime.now()
        ))
        self.goal_counter += 1
        
        return sub_goals
    
    def _decompose_assistance_goal(self, goal: StrategicGoal, context: Optional[Context]) -> List[StrategicGoal]:
        """Decompose user assistance goals."""
        sub_goals = []
        
        # Context awareness
        sub_goals.append(StrategicGoal(
            id=f"goal_{self.goal_counter}",
            type=StrategicGoalType.SYSTEM_OPTIMIZATION,
            description="Improve context awareness for better assistance",
            priority=Priority.MEDIUM,
            horizon=PlanningHorizon.SHORT_TERM,
            success_criteria=["Accurate context detection", "Relevant assistance"],
            sub_goals=[],
            dependencies=[],
            context_requirements={'context_analysis': True},
            estimated_effort=0.6,
            estimated_benefit=0.8,
            created_at=datetime.now()
        ))
        self.goal_counter += 1
        
        return sub_goals
    
    def _decompose_system_goal(self, goal: StrategicGoal, context: Optional[Context]) -> List[StrategicGoal]:
        """Decompose system optimization goals."""
        sub_goals = []
        
        # Performance optimization
        sub_goals.append(StrategicGoal(
            id=f"goal_{self.goal_counter}",
            type=StrategicGoalType.SYSTEM_OPTIMIZATION,
            description="Optimize system performance and resource usage",
            priority=Priority.LOW,
            horizon=PlanningHorizon.LONG_TERM,
            success_criteria=["Reduce resource usage", "Improve response time"],
            sub_goals=[],
            dependencies=[],
            context_requirements={'performance_monitoring': True},
            estimated_effort=0.8,
            estimated_benefit=0.6,
            created_at=datetime.now()
        ))
        self.goal_counter += 1
        
        return sub_goals
    
    def _decompose_learning_goal(self, goal: StrategicGoal, context: Optional[Context]) -> List[StrategicGoal]:
        """Decompose learning improvement goals."""
        sub_goals = []
        
        # Knowledge acquisition
        sub_goals.append(StrategicGoal(
            id=f"goal_{self.goal_counter}",
            type=StrategicGoalType.LEARNING_IMPROVEMENT,
            description="Improve knowledge acquisition and retention",
            priority=Priority.MEDIUM,
            horizon=PlanningHorizon.MEDIUM_TERM,
            success_criteria=["Better pattern recognition", "Improved predictions"],
            sub_goals=[],
            dependencies=[],
            context_requirements={'learning_data': True},
            estimated_effort=0.7,
            estimated_benefit=0.9,
            created_at=datetime.now()
        ))
        self.goal_counter += 1
        
        return sub_goals
    
    def _calculate_plan_metrics(self, plan: StrategicPlan) -> None:
        """Calculate metrics for a strategic plan."""
        try:
            total_effort = 0.0
            total_benefit = 0.0
            goal_count = len(plan.goals)
            
            for goal_id in plan.goals:
                if goal_id in self.strategic_goals:
                    goal = self.strategic_goals[goal_id]
                    total_effort += goal.estimated_effort
                    total_benefit += goal.estimated_benefit
            
            plan.success_metrics = {
                'average_effort': total_effort / goal_count if goal_count > 0 else 0.0,
                'average_benefit': total_benefit / goal_count if goal_count > 0 else 0.0,
                'goal_count': goal_count,
                'complexity_score': total_effort / goal_count if goal_count > 0 else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate plan metrics: {e}")
    
    def _extract_context_triggers(self, context: Context) -> List[str]:
        """Extract context triggers for pattern learning."""
        triggers = []
        
        if context.active_applications:
            triggers.extend([f"app:{app}" for app in context.active_applications])
        
        if context.user_activity:
            triggers.append(f"activity:{context.user_activity}")
        
        if context.system_state:
            for key, value in context.system_state.items():
                triggers.append(f"system:{key}:{value}")
        
        return triggers
    
    def _calculate_suggestion_priority(self, suggestion: Dict[str, Any], context: Context) -> float:
        """Calculate priority score for a suggestion."""
        try:
            base_score = suggestion.get('confidence', 0.5)
            
            # Adjust based on user preferences
            suggestion_type = suggestion.get('type', 'unknown')
            type_preference = self.user_preferences.get('goal_priorities', {}).get(suggestion_type, 0.5)
            
            # Adjust based on context
            context_score = self._assess_context_relevance(suggestion, context)
            
            # Adjust based on historical success
            historical_score = self._get_historical_success_score(suggestion_type)
            
            # Calculate weighted priority
            priority_score = (
                base_score * 0.4 +
                type_preference * 0.3 +
                context_score * 0.2 +
                historical_score * 0.1
            )
            
            return min(max(priority_score, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate suggestion priority: {e}")
            return 0.5
    
    def _should_include_suggestion(self, suggestion: Dict[str, Any], context: Context) -> bool:
        """Determine if a suggestion should be included based on filters."""
        try:
            # Check minimum confidence threshold
            min_confidence = self.user_preferences.get('min_suggestion_confidence', 0.3)
            if suggestion.get('confidence', 0) < min_confidence:
                return False
            
            # Check interruption tolerance
            interruption_risk = suggestion.get('interruption_risk', 0.5)
            max_interruption = self.user_preferences.get('interruption_tolerance', 0.5)
            if interruption_risk > max_interruption:
                return False
            
            # Check context appropriateness
            if not self._is_context_appropriate(suggestion, context):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate suggestion inclusion: {e}")
            return True  # Default to include if evaluation fails
    
    def _assess_context_relevance(self, suggestion: Dict[str, Any], context: Context) -> float:
        """Assess how relevant a suggestion is to the current context."""
        try:
            relevance_score = 0.5  # Default moderate relevance
            
            # Check application context
            suggestion_apps = suggestion.get('relevant_applications', [])
            if suggestion_apps and context.active_applications:
                app_overlap = len(set(suggestion_apps) & set(context.active_applications))
                if app_overlap > 0:
                    relevance_score += 0.3
            
            # Check activity context
            suggestion_activity = suggestion.get('relevant_activity')
            if suggestion_activity and context.user_activity:
                if suggestion_activity.lower() in context.user_activity.lower():
                    relevance_score += 0.2
            
            return min(relevance_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Failed to assess context relevance: {e}")
            return 0.5
    
    def _is_context_appropriate(self, suggestion: Dict[str, Any], context: Context) -> bool:
        """Check if the context is appropriate for the suggestion."""
        try:
            # Check focus level requirements
            required_focus = suggestion.get('required_focus_level', 0.0)
            current_focus = context.system_state.get('focus_level', 0.5)
            
            if required_focus > current_focus:
                return False
            
            # Check timing requirements
            suggestion_timing = suggestion.get('timing_requirements', {})
            if suggestion_timing:
                # Add timing logic here if needed
                pass
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check context appropriateness: {e}")
            return True
    
    def _get_historical_success_score(self, suggestion_type: str) -> float:
        """Get historical success score for a suggestion type."""
        try:
            success_strategies = self.strategic_knowledge.get('success_strategies', {})
            if suggestion_type in success_strategies:
                return success_strategies[suggestion_type].get('success_rate', 0.5)
            return 0.5
            
        except Exception as e:
            self.logger.error(f"Failed to get historical success score: {e}")
            return 0.5
    
    def _analyze_user_patterns(self) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        try:
            patterns = {
                'preferred_automation_types': [],
                'peak_activity_times': [],
                'common_workflows': [],
                'interaction_preferences': {}
            }
            
            # Analyze success strategies for preferred types
            success_strategies = self.strategic_knowledge.get('success_strategies', {})
            for strategy, data in success_strategies.items():
                if data.get('success_rate', 0) > 0.7:
                    patterns['preferred_automation_types'].append(strategy)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to analyze user patterns: {e}")
            return {}
    
    def _identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify optimization opportunities."""
        try:
            opportunities = []
            
            # Look for patterns in failure data
            failure_patterns = self.strategic_knowledge.get('failure_patterns', [])
            if len(failure_patterns) > 5:
                opportunities.append({
                    'type': 'failure_reduction',
                    'description': 'Reduce common failure patterns',
                    'priority': 'high'
                })
            
            # Look for underutilized successful patterns
            success_strategies = self.strategic_knowledge.get('success_strategies', {})
            for strategy, data in success_strategies.items():
                if data.get('success_rate', 0) > 0.8 and data.get('usage_frequency', 0) < 0.3:
                    opportunities.append({
                        'type': 'underutilized_success',
                        'description': f'Increase usage of successful strategy: {strategy}',
                        'priority': 'medium'
                    })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Failed to identify optimization opportunities: {e}")
            return []
    
    def _generate_learning_recommendations(self) -> List[Dict[str, Any]]:
        """Generate learning recommendations."""
        try:
            recommendations = []
            
            # Recommend learning based on knowledge gaps
            if len(self.knowledge_patterns) < 10:
                recommendations.append({
                    'type': 'pattern_learning',
                    'description': 'Increase pattern recognition through more user interactions',
                    'priority': 'high'
                })
            
            # Recommend preference refinement
            automation_level = self.user_preferences.get('automation_level', 0.5)
            if automation_level < 0.3:
                recommendations.append({
                    'type': 'preference_adjustment',
                    'description': 'Consider increasing automation level for better productivity',
                    'priority': 'low'
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate learning recommendations: {e}")
            return []
    
    def _assess_strategic_priorities(self) -> Dict[str, float]:
        """Assess current strategic priorities."""
        try:
            priorities = {}
            
            # Calculate priority scores for each goal type
            for goal in self.strategic_goals.values():
                goal_type = goal.type.value
                if goal_type not in priorities:
                    priorities[goal_type] = 0.0
                
                # Weight by priority and estimated benefit
                priority_weight = {
                    Priority.LOW: 0.25,
                    Priority.MEDIUM: 0.5,
                    Priority.HIGH: 0.75,
                    Priority.CRITICAL: 1.0
                }.get(goal.priority, 0.5)
                
                priorities[goal_type] += priority_weight * goal.estimated_benefit
            
            # Normalize priorities
            max_priority = max(priorities.values()) if priorities else 1.0
            if max_priority > 0:
                for key in priorities:
                    priorities[key] /= max_priority
            
            return priorities
            
        except Exception as e:
            self.logger.error(f"Failed to assess strategic priorities: {e}")
            return {}
    
    def _identify_knowledge_gaps(self) -> List[str]:
        """Identify gaps in strategic knowledge."""
        try:
            gaps = []
            
            # Check for missing pattern types
            pattern_types = set(p.pattern_type for p in self.knowledge_patterns.values())
            expected_types = {'success', 'failure', 'context', 'workflow'}
            missing_types = expected_types - pattern_types
            
            for missing_type in missing_types:
                gaps.append(f"Missing {missing_type} patterns")
            
            # Check for insufficient data
            if len(self.knowledge_patterns) < 5:
                gaps.append("Insufficient pattern data for reliable predictions")
            
            if len(self.strategic_knowledge.get('workflow_patterns', [])) < 3:
                gaps.append("Limited workflow pattern knowledge")
            
            return gaps
            
        except Exception as e:
            self.logger.error(f"Failed to identify knowledge gaps: {e}")
            return []
    
    def _validate_preferences(self) -> None:
        """Validate and normalize user preferences."""
        try:
            # Ensure numeric preferences are in valid range
            numeric_prefs = ['automation_level', 'interruption_tolerance', 'learning_pace']
            for pref in numeric_prefs:
                if pref in self.user_preferences:
                    value = self.user_preferences[pref]
                    if isinstance(value, (int, float)):
                        self.user_preferences[pref] = max(0.0, min(1.0, float(value)))
            
        except Exception as e:
            self.logger.error(f"Failed to validate preferences: {e}")
    
    def _load_strategic_knowledge(self) -> None:
        """Load persisted strategic knowledge (placeholder for future implementation)."""
        try:
            # This would load from persistent storage in a full implementation
            self.logger.debug("Strategic knowledge loading placeholder")
            
        except Exception as e:
            self.logger.error(f"Failed to load strategic knowledge: {e}")
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get Strategic Planner specific status."""
        return {
            'strategic_goals_count': len(self.strategic_goals),
            'strategic_plans_count': len(self.strategic_plans),
            'knowledge_patterns_count': len(self.knowledge_patterns),
            'user_automation_level': self.user_preferences.get('automation_level', 0.5),
            'active_goals': len([g for g in self.strategic_goals.values() if g.status == 'active']),
            'completed_goals': len([g for g in self.strategic_goals.values() if g.status == 'completed']),
        }