import logging
import threading
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from mark_i.perception.perception_engine import PerceptionEngine
from mark_i.agent.agent_core import AgentCore
from mark_i.engines.gemini_analyzer import GeminiAnalyzer, MODEL_PREFERENCE_REASONING
from mark_i.foresight.simulation_engine import SimulationEngine
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME
from mark_i.core.interfaces import IAgencyCore, Context, Priority
from mark_i.core.base_component import ObservableComponent
from mark_i.core.architecture_config import AgencyCoreConfig, get_component_config

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.agency.agency_core")


class OpportunityType(Enum):
    """Types of automation opportunities."""
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    REPETITIVE_TASK = "repetitive_task"
    ERROR_ASSISTANCE = "error_assistance"
    INFORMATION_PREPARATION = "information_preparation"
    SYSTEM_MAINTENANCE = "system_maintenance"


class SuggestionStatus(Enum):
    """Status of automation suggestions."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    MODIFIED = "modified"
    EXPIRED = "expired"


@dataclass
class Opportunity:
    """Represents an automation opportunity."""
    id: str
    type: OpportunityType
    description: str
    confidence: float
    context: Dict[str, Any]
    detected_at: datetime
    urgency: Priority = Priority.MEDIUM
    estimated_benefit: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OpportunityAssessment:
    """Assessment of an automation opportunity."""
    opportunity_id: str
    feasibility_score: float
    benefit_score: float
    risk_score: float
    user_preference_alignment: float
    recommended_action: str
    reasoning: str
    alternative_approaches: List[str]
    
    @property
    def overall_score(self) -> float:
        """Calculate overall opportunity score."""
        return (self.feasibility_score * 0.3 + 
                self.benefit_score * 0.4 + 
                (1 - self.risk_score) * 0.2 + 
                self.user_preference_alignment * 0.1)


@dataclass
class AutomationSuggestion:
    """Represents an automation suggestion to the user."""
    id: str
    opportunity_id: str
    title: str
    description: str
    proposed_actions: List[str]
    estimated_time_saved: float
    confidence: float
    status: SuggestionStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    user_response: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if suggestion has expired."""
        return self.expires_at is not None and datetime.now() > self.expires_at


@dataclass
class UserInteraction:
    """Represents user interaction with suggestions."""
    suggestion_id: str
    response_type: str  # accept, decline, modify, ignore
    response_data: Dict[str, Any]
    timestamp: datetime
    context: Dict[str, Any]


@dataclass
class StrategyKnowledge:
    """Strategic knowledge for decision making."""
    user_preferences: Dict[str, Any]
    workflow_patterns: List[Dict[str, Any]]
    success_metrics: Dict[str, float]
    failure_patterns: List[Dict[str, Any]]
    context_associations: Dict[str, Any]

OPPORTUNITY_DETECTION_PROMPT = """
You are the Agency Core for MARK-I, a proactive AI assistant with strategic reasoning capabilities.
Your role is to analyze the user's environment and identify automation opportunities.

**Core Directives:**
1. **Observe and Learn:** Understand user habits and workflow patterns
2. **Optimize Workflow:** Identify repetitive or inefficient actions
3. **Anticipate Needs:** Prepare applications or information proactively
4. **Maintain System:** Respect user focus and avoid interruptions during complex tasks

**Current Context:**
- Timestamp: {timestamp}
- Visual State: (See attached image)
- Recent Events: {events_summary}
- User Activity Pattern: {activity_pattern}
- Current Focus Level: {focus_level}

**Analysis Task:**
Identify potential automation opportunities based on the current context.
Consider workflow optimization, repetitive tasks, error assistance, and proactive preparation.

Respond with a JSON object:
{{
  "opportunities": [
    {{
      "type": "workflow_optimization|repetitive_task|error_assistance|information_preparation|system_maintenance",
      "description": "Brief description of the opportunity",
      "confidence": 0.0-1.0,
      "urgency": "low|medium|high|critical",
      "estimated_benefit": 0.0-1.0,
      "context": {{"relevant": "context data"}}
    }}
  ],
  "user_focus_assessment": {{
    "is_focused": true/false,
    "task_complexity": "low|medium|high",
    "interruption_risk": 0.0-1.0,
    "reasoning": "Why this assessment was made"
  }}
}}
"""

SUGGESTION_GENERATION_PROMPT = """
You are generating an automation suggestion based on an identified opportunity.

**Opportunity Details:**
{opportunity_details}

**User Context:**
- Current preferences: {user_preferences}
- Historical interactions: {interaction_history}
- Success patterns: {success_patterns}

**Task:**
Create a specific, actionable automation suggestion that addresses this opportunity.
Consider user preferences, past interactions, and potential risks.

Respond with a JSON object:
{{
  "suggestion": {{
    "title": "Clear, concise title",
    "description": "Detailed explanation of what will be automated",
    "proposed_actions": ["Step 1", "Step 2", "Step 3"],
    "estimated_time_saved": 30.0,
    "confidence": 0.85,
    "risk_factors": ["Potential risk 1", "Potential risk 2"],
    "alternatives": ["Alternative approach 1", "Alternative approach 2"]
  }},
  "presentation": {{
    "urgency": "low|medium|high",
    "best_timing": "immediate|when_idle|scheduled",
    "communication_style": "brief|detailed|interactive"
  }}
}}
"""


class AgencyCore(ObservableComponent, IAgencyCore):
    """
    Enhanced Agency Core implementing strategic and proactive reasoning capabilities.
    
    The Agency Core operates at the highest cognitive level, continuously monitoring
    the environment, identifying automation opportunities, and generating strategic
    suggestions for user assistance.
    """

    def __init__(self, 
                 perception_engine: PerceptionEngine, 
                 agent_core: AgentCore, 
                 gemini_analyzer: GeminiAnalyzer, 
                 simulation_engine: SimulationEngine,
                 config: Optional[AgencyCoreConfig] = None):
        
        super().__init__("agency_core", config)
        
        # Core dependencies
        self.perception_engine = perception_engine
        self.agent_core = agent_core
        self.gemini_analyzer = gemini_analyzer
        self.simulation_engine = simulation_engine
        
        # Configuration
        self.agency_config = config or get_component_config("agency_core") or AgencyCoreConfig()
        
        # State management
        self._agency_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Opportunity tracking
        self._opportunities: Dict[str, Opportunity] = {}
        self._suggestions: Dict[str, AutomationSuggestion] = {}
        self._opportunity_counter = 0
        self._suggestion_counter = 0
        
        # Strategic knowledge
        self._strategic_knowledge = StrategyKnowledge(
            user_preferences={},
            workflow_patterns=[],
            success_metrics={},
            failure_patterns=[],
            context_associations={}
        )
        
        # User interaction tracking
        self._interaction_history: List[UserInteraction] = []
        self._last_suggestion_time: Optional[datetime] = None
        
        # Activity pattern tracking
        self._activity_patterns: List[Dict[str, Any]] = []
        self._focus_level_history: List[float] = []
        
        logger.info("Enhanced AgencyCore initialized with proactive monitoring capabilities")


    def _initialize_component(self) -> bool:
        """Initialize Agency Core specific components."""
        try:
            # Initialize perception engine if not already running
            if hasattr(self.perception_engine, 'initialize'):
                if not self.perception_engine.initialize():
                    self.logger.error("Failed to initialize perception engine")
                    return False
            
            # Start event processing
            self.start_event_processing()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Agency Core: {e}")
            return False
    
    def _shutdown_component(self) -> bool:
        """Shutdown Agency Core specific components."""
        try:
            self.stop_monitoring()
            self.stop_event_processing()
            return True
        except Exception as e:
            self.logger.error(f"Failed to shutdown Agency Core: {e}")
            return False
    
    def start_monitoring(self) -> None:
        """Start proactive environment monitoring."""
        if self.is_running():
            self.logger.warning("Agency Core monitoring already running")
            return
        
        self.set_running(True)
        self._stop_event.clear()
        
        # Start perception engine
        if hasattr(self.perception_engine, 'start'):
            self.perception_engine.start()
        
        # Start monitoring thread
        self._agency_thread = threading.Thread(
            target=self._monitoring_loop, 
            daemon=True, 
            name="AgencyCoreMonitoring"
        )
        self._agency_thread.start()
        
        self.logger.info("Agency Core proactive monitoring started")
        self.queue_event({
            'type': 'monitoring_started',
            'timestamp': datetime.now().isoformat()
        })
    
    def stop_monitoring(self) -> None:
        """Stop proactive environment monitoring."""
        if not self.is_running():
            return
        
        self.logger.info("Stopping Agency Core monitoring...")
        
        # Stop perception engine
        if hasattr(self.perception_engine, 'stop'):
            self.perception_engine.stop()
        
        # Stop monitoring thread
        self._stop_event.set()
        if self._agency_thread and self._agency_thread.is_alive():
            self._agency_thread.join(timeout=5.0)
        
        self.set_running(False)
        self.logger.info("Agency Core monitoring stopped")
        
        self.queue_event({
            'type': 'monitoring_stopped',
            'timestamp': datetime.now().isoformat()
        })


    # IAgencyCore interface implementation
    
    def monitor_environment(self) -> List[Dict[str, Any]]:
        """Monitor environment for automation opportunities."""
        try:
            opportunities: List[Dict[str, Any]] = []
            
            # Get recent perception data
            recent_events = self._get_recent_events()
            if not recent_events:
                return opportunities
            
            # Analyze current context
            context = self._build_current_context(recent_events)
            
            # Detect opportunities using AI analysis
            detected_opportunities = self._detect_opportunities(context)
            
            # Store and return opportunities
            for opp_data in detected_opportunities:
                opportunity = self._create_opportunity(opp_data, context)
                self._opportunities[opportunity.id] = opportunity
                opportunities.append(opportunity.to_dict())
                
                self.logger.debug(f"Detected opportunity: {opportunity.description}")
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error monitoring environment: {e}")
            return []
    
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate an automation opportunity and return assessment."""
        try:
            opp_id = opportunity.get('id')
            if not opp_id or opp_id not in self._opportunities:
                return {'error': 'Opportunity not found'}
            
            opp = self._opportunities[opp_id]
            
            # Assess feasibility
            feasibility_score = self._assess_feasibility(opp)
            
            # Assess benefit
            benefit_score = self._assess_benefit(opp)
            
            # Assess risk
            risk_score = self._assess_risk(opp)
            
            # Check user preference alignment
            preference_alignment = self._assess_user_preference_alignment(opp)
            
            # Generate assessment
            assessment = OpportunityAssessment(
                opportunity_id=opp_id,
                feasibility_score=feasibility_score,
                benefit_score=benefit_score,
                risk_score=risk_score,
                user_preference_alignment=preference_alignment,
                recommended_action=self._determine_recommended_action(opp, feasibility_score, benefit_score, risk_score),
                reasoning=self._generate_assessment_reasoning(opp, feasibility_score, benefit_score, risk_score),
                alternative_approaches=self._generate_alternatives(opp)
            )
            
            return asdict(assessment)
            
        except Exception as e:
            self.logger.error(f"Error evaluating opportunity: {e}")
            return {'error': str(e)}
    
    def suggest_automation(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate automation suggestion based on assessment."""
        try:
            opp_id = assessment.get('opportunity_id')
            if not opp_id or opp_id not in self._opportunities:
                return {'error': 'Opportunity not found'}
            
            opportunity = self._opportunities[opp_id]
            
            # Check cooldown period
            if not self._can_make_suggestion():
                self.logger.debug("Suggestion cooldown active, skipping")
                return {'status': 'cooldown_active'}
            
            # Generate suggestion using AI
            suggestion_data = self._generate_suggestion(opportunity, assessment)
            
            if not suggestion_data:
                return {'error': 'Failed to generate suggestion'}
            
            # Create suggestion object
            suggestion = AutomationSuggestion(
                id=f"suggestion_{self._suggestion_counter}",
                opportunity_id=opp_id,
                title=suggestion_data['title'],
                description=suggestion_data['description'],
                proposed_actions=suggestion_data['proposed_actions'],
                estimated_time_saved=suggestion_data.get('estimated_time_saved', 0.0),
                confidence=suggestion_data.get('confidence', 0.5),
                status=SuggestionStatus.PENDING,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=30)  # 30 minute expiry
            )
            
            self._suggestion_counter += 1
            self._suggestions[suggestion.id] = suggestion
            self._last_suggestion_time = datetime.now()
            
            # Notify observers
            self.queue_event({
                'type': 'suggestion_generated',
                'suggestion': asdict(suggestion),
                'timestamp': datetime.now().isoformat()
            })
            
            self.logger.info(f"Generated suggestion: {suggestion.title}")
            return asdict(suggestion)
            
        except Exception as e:
            self.logger.error(f"Error generating suggestion: {e}")
            return {'error': str(e)}
    
    def learn_from_interaction(self, interaction: Dict[str, Any]) -> None:
        """Learn from user interaction to improve future suggestions."""
        try:
            user_interaction = UserInteraction(
                suggestion_id=interaction['suggestion_id'],
                response_type=interaction['response_type'],
                response_data=interaction.get('response_data', {}),
                timestamp=datetime.now(),
                context=interaction.get('context', {})
            )
            
            self._interaction_history.append(user_interaction)
            
            # Update user preferences based on interaction
            self._update_user_preferences(user_interaction)
            
            # Update suggestion status
            if user_interaction.suggestion_id in self._suggestions:
                suggestion = self._suggestions[user_interaction.suggestion_id]
                if user_interaction.response_type == 'accept':
                    suggestion.status = SuggestionStatus.ACCEPTED
                elif user_interaction.response_type == 'decline':
                    suggestion.status = SuggestionStatus.DECLINED
                elif user_interaction.response_type == 'modify':
                    suggestion.status = SuggestionStatus.MODIFIED
                
                suggestion.user_response = user_interaction.response_type
            
            # Learn patterns for future improvements
            self._learn_interaction_patterns(user_interaction)
            
            self.logger.info(f"Learned from user interaction: {user_interaction.response_type}")
            
            self.queue_event({
                'type': 'interaction_learned',
                'interaction': asdict(user_interaction),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error learning from interaction: {e}")
    
    def update_strategic_knowledge(self, knowledge: Dict[str, Any]) -> None:
        """Update strategic knowledge base."""
        try:
            if 'user_preferences' in knowledge:
                self._strategic_knowledge.user_preferences.update(knowledge['user_preferences'])
            
            if 'workflow_patterns' in knowledge:
                self._strategic_knowledge.workflow_patterns.extend(knowledge['workflow_patterns'])
            
            if 'success_metrics' in knowledge:
                self._strategic_knowledge.success_metrics.update(knowledge['success_metrics'])
            
            if 'failure_patterns' in knowledge:
                self._strategic_knowledge.failure_patterns.extend(knowledge['failure_patterns'])
            
            if 'context_associations' in knowledge:
                self._strategic_knowledge.context_associations.update(knowledge['context_associations'])
            
            self.logger.info("Strategic knowledge updated")
            
            self.queue_event({
                'type': 'knowledge_updated',
                'knowledge_keys': list(knowledge.keys()),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error updating strategic knowledge: {e}")    

    # Core monitoring and processing methods
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop for proactive opportunity detection."""
        self.logger.info("Agency Core monitoring loop started")
        
        while not self._stop_event.is_set():
            try:
                # Monitor environment for opportunities
                opportunities = self.monitor_environment()
                
                # Process detected opportunities
                for opp_dict in opportunities:
                    if self._stop_event.is_set():
                        break
                    
                    # Evaluate opportunity
                    assessment = self.evaluate_opportunity(opp_dict)
                    
                    if 'error' not in assessment and assessment.get('overall_score', 0) > 0.6:
                        # Generate suggestion if assessment is positive
                        suggestion = self.suggest_automation(assessment)
                        
                        if 'error' not in suggestion and suggestion.get('status') != 'cooldown_active':
                            # Present suggestion to user (would be handled by UI layer)
                            self._present_suggestion_to_user(suggestion)
                
                # Clean up expired suggestions
                self._cleanup_expired_suggestions()
                
                # Wait for next monitoring cycle
                monitoring_interval = getattr(self.agency_config, 'monitoring_interval_seconds', 5.0)
                self._stop_event.wait(timeout=monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                self._stop_event.wait(timeout=5.0)  # Wait before retrying
        
        self.logger.info("Agency Core monitoring loop stopped")
    
    def _get_recent_events(self) -> List[Dict[str, Any]]:
        """Get recent events from perception engine."""
        events = []
        try:
            if hasattr(self.perception_engine, 'perception_queue'):
                # Collect events from perception queue
                while not self.perception_engine.perception_queue.empty():
                    event = self.perception_engine.perception_queue.get()
                    events.append(event)
            
            return events
        except Exception as e:
            self.logger.error(f"Error getting recent events: {e}")
            return []
    
    def _build_current_context(self, recent_events: List[Dict[str, Any]]) -> Context:
        """Build current context from recent events."""
        try:
            # Extract visual data from events
            screen_state = None
            active_applications = []
            user_activity = None
            
            for event in recent_events:
                if event.get('type') == 'VISUAL_UPDATE':
                    screen_state = event.get('data')
                elif event.get('type') == 'APPLICATION_CHANGE':
                    active_applications.append(event.get('data', {}).get('application', ''))
                elif event.get('type') == 'USER_INPUT':
                    user_activity = event.get('data', {}).get('activity', '')
            
            # Calculate focus level
            focus_level = self._calculate_focus_level(recent_events)
            self._focus_level_history.append(focus_level)
            
            # Keep only recent focus history
            if len(self._focus_level_history) > 100:
                self._focus_level_history = self._focus_level_history[-100:]
            
            context = Context(
                timestamp=datetime.now(),
                screen_state=screen_state,
                active_applications=list(set(active_applications)),
                user_activity=user_activity,
                system_state={
                    'focus_level': focus_level,
                    'recent_events_count': len(recent_events),
                    'monitoring_active': self.is_running()
                }
            )
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error building context: {e}")
            return Context(timestamp=datetime.now())
    
    def _detect_opportunities(self, context: Context) -> List[Dict[str, Any]]:
        """Detect automation opportunities using AI analysis."""
        try:
            if not context.screen_state:
                return []
            
            # Prepare context for AI analysis
            events_summary = self._format_events_for_ai(context)
            activity_pattern = self._analyze_activity_pattern()
            focus_level = context.system_state.get('focus_level', 0.5)
            
            # Query AI for opportunity detection
            prompt = OPPORTUNITY_DETECTION_PROMPT.format(
                timestamp=context.timestamp.isoformat(),
                events_summary=events_summary,
                activity_pattern=activity_pattern,
                focus_level=focus_level
            )
            
            response = self.gemini_analyzer.query_vision_model(
                prompt=prompt,
                image_data=context.screen_state,
                model_preference=MODEL_PREFERENCE_REASONING
            )
            
            if response["status"] == "success" and response.get("json_content"):
                ai_response = response["json_content"]
                
                # Extract opportunities
                opportunities = ai_response.get('opportunities', [])
                
                # Update focus assessment
                focus_assessment = ai_response.get('user_focus_assessment', {})
                self._update_focus_assessment(focus_assessment)
                
                return opportunities
            else:
                self.logger.warning(f"AI opportunity detection failed: {response.get('error_message')}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error detecting opportunities: {e}")
            return []
    
    def _create_opportunity(self, opp_data: Dict[str, Any], context: Context) -> Opportunity:
        """Create an Opportunity object from AI-detected data."""
        opportunity = Opportunity(
            id=f"opp_{self._opportunity_counter}",
            type=OpportunityType(opp_data.get('type', 'workflow_optimization')),
            description=opp_data.get('description', ''),
            confidence=opp_data.get('confidence', 0.5),
            context={
                'detection_context': asdict(context),
                'ai_context': opp_data.get('context', {})
            },
            detected_at=datetime.now(),
            urgency=Priority[opp_data.get('urgency', 'medium').upper()],
            estimated_benefit=opp_data.get('estimated_benefit', 0.0)
        )
        
        self._opportunity_counter += 1
        return opportunity 
   
    # Assessment and suggestion methods
    
    def _assess_feasibility(self, opportunity: Opportunity) -> float:
        """Assess the feasibility of implementing the opportunity."""
        try:
            # Base feasibility on opportunity type and confidence
            base_score = opportunity.confidence
            
            # Adjust based on opportunity type
            type_multipliers = {
                OpportunityType.WORKFLOW_OPTIMIZATION: 0.8,
                OpportunityType.REPETITIVE_TASK: 0.9,
                OpportunityType.ERROR_ASSISTANCE: 0.95,
                OpportunityType.INFORMATION_PREPARATION: 0.7,
                OpportunityType.SYSTEM_MAINTENANCE: 0.6
            }
            
            multiplier = type_multipliers.get(opportunity.type, 0.7)
            
            # Consider system capabilities and current load
            system_factor = 0.9 if self.is_running() else 0.5
            
            feasibility = base_score * multiplier * system_factor
            return min(max(feasibility, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error assessing feasibility: {e}")
            return 0.5
    
    def _assess_benefit(self, opportunity: Opportunity) -> float:
        """Assess the potential benefit of the opportunity."""
        try:
            # Base benefit on estimated benefit and urgency
            base_score = opportunity.estimated_benefit
            
            # Adjust based on urgency
            urgency_multipliers = {
                Priority.LOW: 0.5,
                Priority.MEDIUM: 0.7,
                Priority.HIGH: 0.9,
                Priority.CRITICAL: 1.0
            }
            
            urgency_factor = urgency_multipliers.get(opportunity.urgency, 0.7)
            
            # Consider historical success with similar opportunities
            historical_factor = self._get_historical_success_rate(opportunity.type)
            
            benefit = (base_score * 0.6 + urgency_factor * 0.3 + historical_factor * 0.1)
            return min(max(benefit, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error assessing benefit: {e}")
            return 0.5
    
    def _assess_risk(self, opportunity: Opportunity) -> float:
        """Assess the risk of implementing the opportunity."""
        try:
            # Base risk assessment
            base_risk = 0.3  # Default moderate risk
            
            # Adjust based on opportunity type
            type_risks = {
                OpportunityType.WORKFLOW_OPTIMIZATION: 0.2,
                OpportunityType.REPETITIVE_TASK: 0.1,
                OpportunityType.ERROR_ASSISTANCE: 0.05,
                OpportunityType.INFORMATION_PREPARATION: 0.15,
                OpportunityType.SYSTEM_MAINTENANCE: 0.4
            }
            
            type_risk = type_risks.get(opportunity.type, 0.3)
            
            # Consider user focus level (higher risk if user is focused)
            focus_level = self._get_current_focus_level()
            focus_risk = focus_level * 0.3  # Higher focus = higher interruption risk
            
            # Consider confidence (lower confidence = higher risk)
            confidence_risk = (1.0 - opportunity.confidence) * 0.2
            
            total_risk = (base_risk + type_risk + focus_risk + confidence_risk) / 4
            return min(max(total_risk, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error assessing risk: {e}")
            return 0.5
    
    def _assess_user_preference_alignment(self, opportunity: Opportunity) -> float:
        """Assess how well the opportunity aligns with user preferences."""
        try:
            preferences = self._strategic_knowledge.user_preferences
            
            # Check preference for opportunity type
            type_preference = preferences.get(f'prefer_{opportunity.type.value}', 0.5)
            
            # Check preference for automation level
            automation_preference = preferences.get('automation_level', 0.5)
            
            # Check preference for interruption tolerance
            interruption_tolerance = preferences.get('interruption_tolerance', 0.5)
            
            # Calculate alignment score
            alignment = (type_preference * 0.4 +
                         automation_preference * 0.4 +
                         interruption_tolerance * 0.2)
            
            return min(max(alignment, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error assessing user preference alignment: {e}")
            return 0.5
    
    def _determine_recommended_action(self, opportunity: Opportunity, feasibility: float, benefit: float, risk: float) -> str:
        """Determine the recommended action based on assessment scores."""
        overall_score = (feasibility * 0.3 + benefit * 0.4 + (1 - risk) * 0.3)
        
        if overall_score > 0.8:
            return "immediate_suggestion"
        elif overall_score > 0.6:
            return "delayed_suggestion"
        elif overall_score > 0.4:
            return "conditional_suggestion"
        else:
            return "no_action"
    
    def _generate_assessment_reasoning(self, opportunity: Opportunity, feasibility: float, benefit: float, risk: float) -> str:
        """Generate human-readable reasoning for the assessment."""
        reasoning_parts = []
        
        if feasibility > 0.7:
            reasoning_parts.append("High feasibility due to system capabilities")
        elif feasibility < 0.4:
            reasoning_parts.append("Low feasibility due to system limitations")
        
        if benefit > 0.7:
            reasoning_parts.append("High potential benefit for user productivity")
        elif benefit < 0.4:
            reasoning_parts.append("Limited benefit expected")
        
        if risk > 0.6:
            reasoning_parts.append("Elevated risk due to potential user interruption")
        elif risk < 0.3:
            reasoning_parts.append("Low risk of negative impact")
        
        return "; ".join(reasoning_parts) if reasoning_parts else "Standard assessment completed"
    
    def _generate_alternatives(self, opportunity: Opportunity) -> List[str]:
        """Generate alternative approaches for the opportunity."""
        alternatives = []
        
        # Type-specific alternatives
        if opportunity.type == OpportunityType.WORKFLOW_OPTIMIZATION:
            alternatives.extend([
                "Suggest keyboard shortcuts",
                "Recommend workflow reorganization",
                "Propose batch processing"
            ])
        elif opportunity.type == OpportunityType.REPETITIVE_TASK:
            alternatives.extend([
                "Create automation script",
                "Suggest template usage",
                "Recommend tool integration"
            ])
        elif opportunity.type == OpportunityType.ERROR_ASSISTANCE:
            alternatives.extend([
                "Provide error explanation",
                "Suggest troubleshooting steps",
                "Offer automatic fix"
            ])
        
        return alternatives[:3]  # Limit to 3 alternatives
    
    def _generate_suggestion(self, opportunity: Opportunity, assessment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a specific automation suggestion using AI."""
        try:
            # Prepare context for suggestion generation
            opportunity_details = json.dumps(asdict(opportunity), default=str, indent=2)
            user_preferences = json.dumps(self._strategic_knowledge.user_preferences, indent=2)
            interaction_history = self._format_interaction_history()
            success_patterns = json.dumps(self._strategic_knowledge.success_metrics, indent=2)
            
            prompt = SUGGESTION_GENERATION_PROMPT.format(
                opportunity_details=opportunity_details,
                user_preferences=user_preferences,
                interaction_history=interaction_history,
                success_patterns=success_patterns
            )
            
            response = self.gemini_analyzer.query_vision_model(
                prompt=prompt,
                image_data=None,  # Text-only analysis
                model_preference=MODEL_PREFERENCE_REASONING
            )
            
            if response["status"] == "success" and response.get("json_content"):
                ai_response = response["json_content"]
                return ai_response.get('suggestion')
            else:
                self.logger.warning(f"AI suggestion generation failed: {response.get('error_message')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating suggestion: {e}")
            return None    

    # Helper and utility methods
    
    def _can_make_suggestion(self) -> bool:
        """Check if we can make a new suggestion (respecting cooldown)."""
        if not self._last_suggestion_time:
            return True
        
        cooldown_seconds = getattr(self.agency_config, 'suggestion_cooldown_seconds', 30.0)
        cooldown_period = timedelta(seconds=cooldown_seconds)
        return datetime.now() - self._last_suggestion_time > cooldown_period
    
    def _present_suggestion_to_user(self, suggestion: Dict[str, Any]) -> None:
        """Present suggestion to user (placeholder for UI integration)."""
        # This would be handled by the UI layer in a real implementation
        self.logger.info(f"Presenting suggestion to user: {suggestion.get('title', 'Unknown')}")
        
        # Queue event for UI to handle
        self.queue_event({
            'type': 'suggestion_ready',
            'suggestion': suggestion,
            'timestamp': datetime.now().isoformat()
        })
    
    def _cleanup_expired_suggestions(self) -> None:
        """Clean up expired suggestions."""
        current_time = datetime.now()
        expired_ids = []
        
        for suggestion_id, suggestion in self._suggestions.items():
            if suggestion.is_expired():
                expired_ids.append(suggestion_id)
                suggestion.status = SuggestionStatus.EXPIRED
        
        for suggestion_id in expired_ids:
            self.logger.debug(f"Suggestion {suggestion_id} expired")
        
        if expired_ids:
            self.queue_event({
                'type': 'suggestions_expired',
                'expired_count': len(expired_ids),
                'timestamp': current_time.isoformat()
            })
    
    def _calculate_focus_level(self, recent_events: List[Dict[str, Any]]) -> float:
        """Calculate user focus level based on recent events."""
        try:
            if not recent_events:
                return 0.5  # Default moderate focus
            
            # Analyze event patterns for focus indicators
            input_events = [e for e in recent_events if e.get('type') == 'USER_INPUT']
            app_changes = [e for e in recent_events if e.get('type') == 'APPLICATION_CHANGE']
            
            # High input activity suggests focus
            input_factor = min(len(input_events) / 10.0, 1.0)
            
            # Frequent app changes suggest low focus
            distraction_factor = max(0.0, 1.0 - (len(app_changes) / 5.0))
            
            # Combine factors
            focus_level = (input_factor * 0.6 + distraction_factor * 0.4)
            
            return min(max(focus_level, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating focus level: {e}")
            return 0.5
    
    def _get_current_focus_level(self) -> float:
        """Get the current user focus level."""
        if self._focus_level_history:
            return self._focus_level_history[-1]
        return 0.5
    
    def _analyze_activity_pattern(self) -> str:
        """Analyze recent activity patterns."""
        try:
            if len(self._activity_patterns) < 3:
                return "Insufficient data for pattern analysis"
            
            # Analyze recent patterns
            recent_patterns = self._activity_patterns[-10:]
            
            # Look for common patterns
            pattern_types = [p.get('type', 'unknown') for p in recent_patterns]
            most_common = max(set(pattern_types), key=pattern_types.count) if pattern_types else 'unknown'
            
            return f"Recent activity shows {most_common} pattern with {len(recent_patterns)} data points"
            
        except Exception as e:
            self.logger.error(f"Error analyzing activity pattern: {e}")
            return "Pattern analysis unavailable"
    
    def _format_events_for_ai(self, context: Context) -> str:
        """Format events for AI analysis."""
        try:
            events_summary = []
            
            if context.active_applications:
                events_summary.append(f"Active applications: {', '.join(context.active_applications)}")
            
            if context.user_activity:
                events_summary.append(f"User activity: {context.user_activity}")
            
            focus_level = context.system_state.get('focus_level', 0.5)
            events_summary.append(f"Focus level: {focus_level:.2f}")
            
            return "\n".join(events_summary) if events_summary else "No significant events detected"
            
        except Exception as e:
            self.logger.error(f"Error formatting events for AI: {e}")
            return "Event formatting error"
    
    def _update_focus_assessment(self, focus_assessment: Dict[str, Any]) -> None:
        """Update focus assessment from AI analysis."""
        try:
            # Store focus assessment for future reference
            assessment_data = {
                'timestamp': datetime.now(),
                'is_focused': focus_assessment.get('is_focused', False),
                'task_complexity': focus_assessment.get('task_complexity', 'medium'),
                'interruption_risk': focus_assessment.get('interruption_risk', 0.5),
                'reasoning': focus_assessment.get('reasoning', '')
            }
            
            self._activity_patterns.append(assessment_data)
            
            # Keep only recent patterns
            if len(self._activity_patterns) > 50:
                self._activity_patterns = self._activity_patterns[-50:]
                
        except Exception as e:
            self.logger.error(f"Error updating focus assessment: {e}")
    
    def _update_user_preferences(self, interaction: UserInteraction) -> None:
        """Update user preferences based on interaction."""
        try:
            preferences = self._strategic_knowledge.user_preferences
            
            # Update preferences based on response type
            if interaction.response_type == 'accept':
                # Increase preference for this type of suggestion
                suggestion = self._suggestions.get(interaction.suggestion_id)
                if suggestion:
                    opportunity = self._opportunities.get(suggestion.opportunity_id)
                    if opportunity:
                        pref_key = f'prefer_{opportunity.type.value}'
                        current_pref = preferences.get(pref_key, 0.5)
                        preferences[pref_key] = min(current_pref + 0.1, 1.0)
            
            elif interaction.response_type == 'decline':
                # Decrease preference for this type of suggestion
                suggestion = self._suggestions.get(interaction.suggestion_id)
                if suggestion:
                    opportunity = self._opportunities.get(suggestion.opportunity_id)
                    if opportunity:
                        pref_key = f'prefer_{opportunity.type.value}'
                        current_pref = preferences.get(pref_key, 0.5)
                        preferences[pref_key] = max(current_pref - 0.1, 0.0)
            
            # Update general automation preference
            if interaction.response_type in ['accept', 'modify']:
                current_auto_pref = preferences.get('automation_level', 0.5)
                preferences['automation_level'] = min(current_auto_pref + 0.05, 1.0)
            elif interaction.response_type == 'decline':
                current_auto_pref = preferences.get('automation_level', 0.5)
                preferences['automation_level'] = max(current_auto_pref - 0.05, 0.0)
                
        except Exception as e:
            self.logger.error(f"Error updating user preferences: {e}")
    
    def _learn_interaction_patterns(self, interaction: UserInteraction) -> None:
        """Learn patterns from user interactions."""
        try:
            # Update success metrics
            success_metrics = self._strategic_knowledge.success_metrics
            
            suggestion = self._suggestions.get(interaction.suggestion_id)
            if suggestion:
                opportunity = self._opportunities.get(suggestion.opportunity_id)
                if opportunity:
                    metric_key = f'{opportunity.type.value}_success_rate'
                    
                    if interaction.response_type in ['accept', 'modify']:
                        # Positive interaction
                        current_rate = success_metrics.get(metric_key, 0.5)
                        success_metrics[metric_key] = min(current_rate + 0.1, 1.0)
                    elif interaction.response_type == 'decline':
                        # Negative interaction
                        current_rate = success_metrics.get(metric_key, 0.5)
                        success_metrics[metric_key] = max(current_rate - 0.1, 0.0)
            
            # Store interaction pattern for future analysis
            pattern = {
                'timestamp': interaction.timestamp,
                'response_type': interaction.response_type,
                'context': interaction.context,
                'suggestion_confidence': suggestion.confidence if suggestion else 0.0
            }
            
            if interaction.response_type == 'decline':
                self._strategic_knowledge.failure_patterns.append(pattern)
            
            # Keep only recent patterns
            if len(self._strategic_knowledge.failure_patterns) > 100:
                self._strategic_knowledge.failure_patterns = self._strategic_knowledge.failure_patterns[-100:]
                
        except Exception as e:
            self.logger.error(f"Error learning interaction patterns: {e}")
    
    def _get_historical_success_rate(self, opportunity_type: OpportunityType) -> float:
        """Get historical success rate for opportunity type."""
        try:
            metric_key = f'{opportunity_type.value}_success_rate'
            return self._strategic_knowledge.success_metrics.get(metric_key, 0.5)
        except Exception as e:
            self.logger.error(f"Error getting historical success rate: {e}")
            return 0.5
    
    def _format_interaction_history(self) -> str:
        """Format interaction history for AI analysis."""
        try:
            if not self._interaction_history:
                return "No previous interactions"
            
            recent_interactions = self._interaction_history[-10:]  # Last 10 interactions
            
            summary = []
            for interaction in recent_interactions:
                summary.append(f"- {interaction.response_type} suggestion at {interaction.timestamp}")
            
            return "\n".join(summary)
            
        except Exception as e:
            self.logger.error(f"Error formatting interaction history: {e}")
            return "Interaction history unavailable"
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get Agency Core specific status information."""
        return {
            'opportunities_detected': len(self._opportunities),
            'active_suggestions': len([s for s in self._suggestions.values() if s.status == SuggestionStatus.PENDING]),
            'total_suggestions': len(self._suggestions),
            'interaction_history_size': len(self._interaction_history),
            'current_focus_level': self._get_current_focus_level(),
            'monitoring_interval': getattr(self.agency_config, 'monitoring_interval_seconds', 5.0),
            'last_suggestion_time': self._last_suggestion_time.isoformat() if self._last_suggestion_time else None
        }
    
    # Legacy compatibility methods (for existing code)
    
    def start(self) -> None:
        """Legacy start method for backward compatibility."""
        if not self.is_initialized():
            self.initialize()
        self.start_monitoring()
    
    def stop(self) -> None:
        """Legacy stop method for backward compatibility."""
        self.stop_monitoring()
        if self.is_initialized():
            self.shutdown()
    
    def reason_about_world(self, visual_event: Dict[str, Any], recent_events: List[Dict[str, Any]]) -> None:
        """Legacy method for backward compatibility."""
        try:
            # Convert to new format and process
            context = Context(
                timestamp=datetime.now(),
                screen_state=visual_event.get('data'),
                system_state={'legacy_events': recent_events}
            )
            
            # Detect opportunities
            opportunities = self._detect_opportunities(context)
            
            # Process opportunities
            for opp_data in opportunities:
                opportunity = self._create_opportunity(opp_data, context)
                self._opportunities[opportunity.id] = opportunity
                
                # Evaluate and potentially suggest
                assessment = self.evaluate_opportunity(opportunity.to_dict())
                if 'error' not in assessment and assessment.get('overall_score', 0) > 0.6:
                    suggestion = self.suggest_automation(assessment)
                    if 'error' not in suggestion:
                        self._present_suggestion_to_user(suggestion)
                        
        except Exception as e:
            self.logger.error(f"Error in legacy reason_about_world: {e}")

