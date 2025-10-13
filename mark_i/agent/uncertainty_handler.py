"""
Uncertainty Handler for MARK-I Agent Core.

This module provides comprehensive uncertainty handling capabilities including
user clarification mechanisms, confidence assessment, and uncertainty resolution strategies.
"""

import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from mark_i.core.base_component import BaseComponent
from mark_i.core.interfaces import Context, ExecutionResult
from mark_i.core.architecture_config import ComponentConfig

logger = logging.getLogger("mark_i.agent.uncertainty_handler")


class UncertaintyLevel(Enum):
    """Levels of uncertainty."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClarificationMethod(Enum):
    """Methods for seeking clarification."""
    USER_PROMPT = "user_prompt"
    CONTEXT_ANALYSIS = "context_analysis"
    ASSUMPTION_MAKING = "assumption_making"
    ALTERNATIVE_EXPLORATION = "alternative_exploration"
    EXPERT_CONSULTATION = "expert_consultation"


@dataclass
class UncertaintyAssessment:
    """Assessment of uncertainty in a situation."""
    uncertainty_id: str
    level: UncertaintyLevel
    confidence_score: float
    uncertainty_sources: List[str]
    impact_assessment: str
    resolution_urgency: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ClarificationRequest:
    """Request for clarification from user or system."""
    request_id: str
    uncertainty_id: str
    method: ClarificationMethod
    question: str
    options: List[str]
    context: Dict[str, Any]
    timeout_seconds: float
    priority: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ClarificationResponse:
    """Response to a clarification request."""
    response_id: str
    request_id: str
    response_type: str  # answer, timeout, skip, error
    response_data: Dict[str, Any]
    confidence: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class UncertaintyHandler(BaseComponent):
    """
    Handles uncertainty detection, assessment, and resolution.
    
    Provides mechanisms for detecting uncertain situations, assessing their impact,
    and implementing appropriate resolution strategies including user clarification.
    """   
 
    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize the Uncertainty Handler."""
        super().__init__("uncertainty_handler", config)
        
        # Uncertainty tracking
        self.uncertainty_assessments: Dict[str, UncertaintyAssessment] = {}
        self.clarification_requests: Dict[str, ClarificationRequest] = {}
        self.clarification_responses: Dict[str, ClarificationResponse] = {}
        
        # Counters
        self.uncertainty_counter = 0
        self.clarification_counter = 0
        self.response_counter = 0
        
        # Configuration
        self.confidence_threshold = 0.7
        self.uncertainty_timeout = 30.0  # seconds
        self.max_clarification_attempts = 3
        
        # User interaction callbacks
        self.user_interaction_callbacks: List[Callable[[ClarificationRequest], Optional[ClarificationResponse]]] = []
        
        # Resolution strategies
        self.resolution_strategies: Dict[str, Callable] = {
            'ambiguous_command': self._resolve_ambiguous_command,
            'unclear_context': self._resolve_unclear_context,
            'multiple_options': self._resolve_multiple_options,
            'missing_information': self._resolve_missing_information,
            'conflicting_requirements': self._resolve_conflicting_requirements,
            'insufficient_permissions': self._resolve_insufficient_permissions,
            'resource_unavailable': self._resolve_resource_unavailable,
            'unexpected_state': self._resolve_unexpected_state
        }
    
    def _initialize_component(self) -> bool:
        """Initialize the Uncertainty Handler component."""
        try:
            self.logger.info("Uncertainty Handler initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Uncertainty Handler: {e}")
            return False
    
    def assess_uncertainty(self, context: Context, situation_data: Dict[str, Any]) -> UncertaintyAssessment:
        """Assess the level of uncertainty in a given situation."""
        try:
            uncertainty_sources = []
            confidence_scores = []
            
            # Analyze various uncertainty sources
            
            # 1. Command clarity
            command_clarity = self._assess_command_clarity(situation_data)
            if command_clarity < 0.8:
                uncertainty_sources.append("unclear_command")
                confidence_scores.append(command_clarity)
            
            # 2. Context completeness
            context_completeness = self._assess_context_completeness(context)
            if context_completeness < 0.7:
                uncertainty_sources.append("incomplete_context")
                confidence_scores.append(context_completeness)
            
            # 3. Available options
            options_clarity = self._assess_available_options(situation_data)
            if options_clarity < 0.6:
                uncertainty_sources.append("unclear_options")
                confidence_scores.append(options_clarity)
            
            # 4. Resource availability
            resource_availability = self._assess_resource_availability(situation_data)
            if resource_availability < 0.8:
                uncertainty_sources.append("resource_constraints")
                confidence_scores.append(resource_availability)
            
            # Calculate overall confidence
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 1.0
            
            # Determine uncertainty level
            uncertainty_level = self._determine_uncertainty_level(overall_confidence, len(uncertainty_sources))
            
            # Create assessment
            assessment = UncertaintyAssessment(
                uncertainty_id=f"uncertainty_{self.uncertainty_counter}",
                level=uncertainty_level,
                confidence_score=overall_confidence,
                uncertainty_sources=uncertainty_sources,
                impact_assessment=self._assess_impact(uncertainty_level, uncertainty_sources),
                resolution_urgency=self._assess_resolution_urgency(uncertainty_level, situation_data)
            )
            
            self.uncertainty_counter += 1
            self.uncertainty_assessments[assessment.uncertainty_id] = assessment
            
            self.logger.debug(f"Uncertainty assessed: {uncertainty_level.value} (confidence: {overall_confidence:.2f})")
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Failed to assess uncertainty: {e}")
            return UncertaintyAssessment(
                uncertainty_id=f"error_{self.uncertainty_counter}",
                level=UncertaintyLevel.HIGH,
                confidence_score=0.0,
                uncertainty_sources=["assessment_error"],
                impact_assessment="Unable to assess impact",
                resolution_urgency="immediate"
            )
    
    def request_clarification(self, 
                            uncertainty_assessment: UncertaintyAssessment,
                            method: ClarificationMethod = ClarificationMethod.USER_PROMPT,
                            custom_question: Optional[str] = None) -> ClarificationRequest:
        """Request clarification for an uncertain situation."""
        try:
            # Generate appropriate question and options
            question, options = self._generate_clarification_content(uncertainty_assessment, method, custom_question)
            
            # Determine timeout based on urgency
            timeout = self._calculate_clarification_timeout(uncertainty_assessment.resolution_urgency)
            
            # Create clarification request
            request = ClarificationRequest(
                request_id=f"clarification_{self.clarification_counter}",
                uncertainty_id=uncertainty_assessment.uncertainty_id,
                method=method,
                question=question,
                options=options,
                context={
                    'uncertainty_level': uncertainty_assessment.level.value,
                    'sources': uncertainty_assessment.uncertainty_sources,
                    'impact': uncertainty_assessment.impact_assessment
                },
                timeout_seconds=timeout,
                priority=uncertainty_assessment.resolution_urgency
            )
            
            self.clarification_counter += 1
            self.clarification_requests[request.request_id] = request
            
            self.logger.info(f"Clarification requested: {method.value} for {uncertainty_assessment.uncertainty_id}")
            
            # Notify observers
            self._notify_observers({
                'type': 'clarification_requested',
                'request': asdict(request),
                'timestamp': datetime.now().isoformat()
            })
            
            return request
            
        except Exception as e:
            self.logger.error(f"Failed to request clarification: {e}")
            raise
    
    def handle_clarification_response(self, response: ClarificationResponse) -> Dict[str, Any]:
        """Handle a response to a clarification request."""
        try:
            # Store response
            self.clarification_responses[response.response_id] = response
            
            # Get original request
            request = self.clarification_requests.get(response.request_id)
            if not request:
                return {'status': 'error', 'message': 'Original request not found'}
            
            # Get uncertainty assessment
            uncertainty = self.uncertainty_assessments.get(request.uncertainty_id)
            if not uncertainty:
                return {'status': 'error', 'message': 'Original uncertainty not found'}
            
            # Process response based on type
            if response.response_type == 'answer':
                resolution = self._process_clarification_answer(request, response, uncertainty)
            elif response.response_type == 'timeout':
                resolution = self._handle_clarification_timeout(request, uncertainty)
            elif response.response_type == 'skip':
                resolution = self._handle_clarification_skip(request, uncertainty)
            else:
                resolution = self._handle_clarification_error(request, response, uncertainty)
            
            self.logger.info(f"Clarification response processed: {response.response_type}")
            
            # Notify observers
            self._notify_observers({
                'type': 'clarification_response_processed',
                'response': asdict(response),
                'resolution': resolution,
                'timestamp': datetime.now().isoformat()
            })
            
            return resolution
            
        except Exception as e:
            self.logger.error(f"Failed to handle clarification response: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def resolve_uncertainty(self, uncertainty_assessment: UncertaintyAssessment, 
                          resolution_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolve uncertainty using appropriate strategy."""
        try:
            # Determine primary uncertainty source
            primary_source = self._identify_primary_uncertainty_source(uncertainty_assessment)
            
            # Get resolution strategy
            strategy = self.resolution_strategies.get(primary_source, self._resolve_generic_uncertainty)
            
            # Execute resolution strategy
            resolution = strategy(uncertainty_assessment, resolution_data or {})
            
            self.logger.info(f"Uncertainty resolved using {primary_source} strategy")
            
            return resolution
            
        except Exception as e:
            self.logger.error(f"Failed to resolve uncertainty: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'fallback_action': 'request_human_intervention'
            }
    
    def add_user_interaction_callback(self, callback: Callable[[ClarificationRequest], Optional[ClarificationResponse]]) -> None:
        """Add a callback for user interaction."""
        if callback not in self.user_interaction_callbacks:
            self.user_interaction_callbacks.append(callback)
    
    def remove_user_interaction_callback(self, callback: Callable[[ClarificationRequest], Optional[ClarificationResponse]]) -> None:
        """Remove a user interaction callback."""
        if callback in self.user_interaction_callbacks:
            self.user_interaction_callbacks.remove(callback)
    
    # Private helper methods
    
    def _assess_command_clarity(self, situation_data: Dict[str, Any]) -> float:
        """Assess the clarity of the command or instruction."""
        try:
            command = situation_data.get('command', '')
            
            # Simple heuristics for command clarity
            clarity_score = 1.0
            
            # Check for ambiguous words
            ambiguous_words = ['maybe', 'perhaps', 'might', 'could', 'possibly', 'something', 'anything']
            for word in ambiguous_words:
                if word in command.lower():
                    clarity_score -= 0.2
            
            # Check for missing key information
            if len(command.split()) < 3:
                clarity_score -= 0.3
            
            # Check for question marks (indicating uncertainty)
            if '?' in command:
                clarity_score -= 0.1
            
            return max(clarity_score, 0.0)
            
        except Exception as e:
            self.logger.error(f"Failed to assess command clarity: {e}")
            return 0.5
    
    def _assess_context_completeness(self, context: Context) -> float:
        """Assess the completeness of the available context."""
        try:
            completeness_score = 0.0
            
            # Check for various context elements
            if context.screen_state is not None:
                completeness_score += 0.3
            
            if context.active_applications:
                completeness_score += 0.2
            
            if context.user_activity:
                completeness_score += 0.2
            
            if context.system_state:
                completeness_score += 0.3
            
            return min(completeness_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Failed to assess context completeness: {e}")
            return 0.5
    
    def _assess_available_options(self, situation_data: Dict[str, Any]) -> float:
        """Assess the clarity of available options."""
        try:
            options = situation_data.get('available_options', [])
            
            if not options:
                return 0.3  # No clear options available
            
            if len(options) == 1:
                return 0.9  # Clear single option
            
            if len(options) <= 3:
                return 0.7  # Manageable number of options
            
            return 0.5  # Too many options, potentially confusing
            
        except Exception as e:
            self.logger.error(f"Failed to assess available options: {e}")
            return 0.5
    
    def _assess_resource_availability(self, situation_data: Dict[str, Any]) -> float:
        """Assess the availability of required resources."""
        try:
            required_resources = situation_data.get('required_resources', [])
            available_resources = situation_data.get('available_resources', [])
            
            if not required_resources:
                return 1.0  # No specific resources required
            
            available_count = len(set(required_resources) & set(available_resources))
            required_count = len(required_resources)
            
            return available_count / required_count if required_count > 0 else 1.0
            
        except Exception as e:
            self.logger.error(f"Failed to assess resource availability: {e}")
            return 0.5
    
    def _determine_uncertainty_level(self, confidence_score: float, source_count: int) -> UncertaintyLevel:
        """Determine the uncertainty level based on confidence and sources."""
        if confidence_score >= 0.8 and source_count <= 1:
            return UncertaintyLevel.LOW
        elif confidence_score >= 0.6 and source_count <= 2:
            return UncertaintyLevel.MEDIUM
        elif confidence_score >= 0.4 or source_count <= 3:
            return UncertaintyLevel.HIGH
        else:
            return UncertaintyLevel.CRITICAL
    
    def _assess_impact(self, uncertainty_level: UncertaintyLevel, sources: List[str]) -> str:
        """Assess the impact of uncertainty on task execution."""
        impact_descriptions = {
            UncertaintyLevel.LOW: "Minimal impact on task execution",
            UncertaintyLevel.MEDIUM: "Moderate impact, may require minor adjustments",
            UncertaintyLevel.HIGH: "Significant impact, likely to affect task success",
            UncertaintyLevel.CRITICAL: "Critical impact, task execution may fail"
        }
        
        base_impact = impact_descriptions[uncertainty_level]
        
        # Add specific impact based on sources
        if 'unclear_command' in sources:
            base_impact += "; Command interpretation may be incorrect"
        if 'resource_constraints' in sources:
            base_impact += "; Required resources may not be available"
        
        return base_impact
    
    def _assess_resolution_urgency(self, uncertainty_level: UncertaintyLevel, situation_data: Dict[str, Any]) -> str:
        """Assess how urgently the uncertainty needs to be resolved."""
        urgency_mapping = {
            UncertaintyLevel.LOW: "low",
            UncertaintyLevel.MEDIUM: "medium", 
            UncertaintyLevel.HIGH: "high",
            UncertaintyLevel.CRITICAL: "immediate"
        }
        
        base_urgency = urgency_mapping[uncertainty_level]
        
        # Adjust based on situation
        if situation_data.get('time_sensitive', False):
            if base_urgency == "low":
                base_urgency = "medium"
            elif base_urgency == "medium":
                base_urgency = "high"
        
        return base_urgency
    
    def _generate_clarification_content(self, uncertainty: UncertaintyAssessment, 
                                      method: ClarificationMethod, 
                                      custom_question: Optional[str]) -> Tuple[str, List[str]]:
        """Generate appropriate clarification question and options."""
        if custom_question:
            return custom_question, []
        
        # Generate question based on uncertainty sources
        primary_source = uncertainty.uncertainty_sources[0] if uncertainty.uncertainty_sources else "unknown"
        
        question_templates = {
            'unclear_command': "The command is ambiguous. Could you please clarify what you want me to do?",
            'incomplete_context': "I need more information about the current situation. Can you provide additional context?",
            'unclear_options': "There are multiple ways to proceed. Which approach would you prefer?",
            'resource_constraints': "Some required resources may not be available. How should I proceed?",
            'assessment_error': "I'm having trouble understanding the situation. Could you help me understand what you need?"
        }
        
        question = question_templates.get(primary_source, "I need clarification to proceed effectively. Can you help?")
        
        # Generate options based on method
        options = []
        if method == ClarificationMethod.USER_PROMPT:
            options = ["Provide more details", "Choose different approach", "Skip this step", "Cancel task"]
        elif method == ClarificationMethod.ALTERNATIVE_EXPLORATION:
            options = ["Try alternative method", "Use different tool", "Modify parameters", "Seek help"]
        
        return question, options
    
    def _calculate_clarification_timeout(self, urgency: str) -> float:
        """Calculate appropriate timeout for clarification based on urgency."""
        timeout_mapping = {
            'low': 60.0,      # 1 minute
            'medium': 30.0,   # 30 seconds
            'high': 15.0,     # 15 seconds
            'immediate': 5.0  # 5 seconds
        }
        
        return timeout_mapping.get(urgency, 30.0)
    
    def _identify_primary_uncertainty_source(self, uncertainty: UncertaintyAssessment) -> str:
        """Identify the primary source of uncertainty."""
        if not uncertainty.uncertainty_sources:
            return 'unknown'
        
        # Map uncertainty sources to resolution strategies
        source_mapping = {
            'unclear_command': 'ambiguous_command',
            'incomplete_context': 'unclear_context',
            'unclear_options': 'multiple_options',
            'resource_constraints': 'resource_unavailable'
        }
        
        primary_source = uncertainty.uncertainty_sources[0]
        return source_mapping.get(primary_source, 'unknown')
    
    def _process_clarification_answer(self, request: ClarificationRequest, 
                                    response: ClarificationResponse, 
                                    uncertainty: UncertaintyAssessment) -> Dict[str, Any]:
        """Process a clarification answer from the user."""
        try:
            answer_data = response.response_data
            
            return {
                'status': 'resolved',
                'resolution_type': 'user_clarification',
                'action': answer_data.get('selected_action', 'proceed'),
                'parameters': answer_data.get('parameters', {}),
                'confidence': response.confidence,
                'message': 'Uncertainty resolved through user clarification'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process clarification answer: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_clarification_timeout(self, request: ClarificationRequest, 
                                    uncertainty: UncertaintyAssessment) -> Dict[str, Any]:
        """Handle clarification request timeout."""
        return {
            'status': 'timeout',
            'resolution_type': 'assumption_based',
            'action': 'proceed_with_best_guess',
            'confidence': 0.3,
            'message': 'Proceeding with best available option due to timeout'
        }
    
    def _handle_clarification_skip(self, request: ClarificationRequest, 
                                 uncertainty: UncertaintyAssessment) -> Dict[str, Any]:
        """Handle user choosing to skip clarification."""
        return {
            'status': 'skipped',
            'resolution_type': 'user_skip',
            'action': 'continue_without_resolution',
            'confidence': 0.4,
            'message': 'Continuing without resolving uncertainty as requested by user'
        }
    
    def _handle_clarification_error(self, request: ClarificationRequest, 
                                  response: ClarificationResponse, 
                                  uncertainty: UncertaintyAssessment) -> Dict[str, Any]:
        """Handle clarification error."""
        return {
            'status': 'error',
            'resolution_type': 'error_fallback',
            'action': 'request_human_intervention',
            'confidence': 0.1,
            'message': f'Clarification failed: {response.response_data.get("error", "Unknown error")}'
        }
    
    # Resolution strategy methods
    
    def _resolve_ambiguous_command(self, uncertainty: UncertaintyAssessment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve ambiguous command uncertainty."""
        return {
            'status': 'resolved',
            'resolution_type': 'command_interpretation',
            'action': 'interpret_most_likely_meaning',
            'confidence': 0.6,
            'message': 'Interpreting command based on context and common patterns'
        }
    
    def _resolve_unclear_context(self, uncertainty: UncertaintyAssessment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve unclear context uncertainty."""
        return {
            'status': 'resolved',
            'resolution_type': 'context_gathering',
            'action': 'gather_additional_context',
            'confidence': 0.7,
            'message': 'Gathering additional context information'
        }
    
    def _resolve_multiple_options(self, uncertainty: UncertaintyAssessment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve multiple options uncertainty."""
        return {
            'status': 'resolved',
            'resolution_type': 'option_selection',
            'action': 'select_most_appropriate_option',
            'confidence': 0.5,
            'message': 'Selecting most appropriate option based on available information'
        }
    
    def _resolve_missing_information(self, uncertainty: UncertaintyAssessment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve missing information uncertainty."""
        return {
            'status': 'resolved',
            'resolution_type': 'information_gathering',
            'action': 'gather_missing_information',
            'confidence': 0.6,
            'message': 'Attempting to gather missing information'
        }
    
    def _resolve_conflicting_requirements(self, uncertainty: UncertaintyAssessment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve conflicting requirements uncertainty."""
        return {
            'status': 'resolved',
            'resolution_type': 'requirement_prioritization',
            'action': 'prioritize_requirements',
            'confidence': 0.5,
            'message': 'Prioritizing requirements based on importance'
        }
    
    def _resolve_insufficient_permissions(self, uncertainty: UncertaintyAssessment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve insufficient permissions uncertainty."""
        return {
            'status': 'resolved',
            'resolution_type': 'permission_handling',
            'action': 'request_elevated_permissions',
            'confidence': 0.4,
            'message': 'Requesting necessary permissions'
        }
    
    def _resolve_resource_unavailable(self, uncertainty: UncertaintyAssessment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve resource unavailable uncertainty."""
        return {
            'status': 'resolved',
            'resolution_type': 'resource_substitution',
            'action': 'find_alternative_resources',
            'confidence': 0.5,
            'message': 'Finding alternative resources or methods'
        }
    
    def _resolve_unexpected_state(self, uncertainty: UncertaintyAssessment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve unexpected state uncertainty."""
        return {
            'status': 'resolved',
            'resolution_type': 'state_recovery',
            'action': 'attempt_state_recovery',
            'confidence': 0.4,
            'message': 'Attempting to recover from unexpected state'
        }
    
    def _resolve_generic_uncertainty(self, uncertainty: UncertaintyAssessment, data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve generic uncertainty with fallback strategy."""
        return {
            'status': 'resolved',
            'resolution_type': 'generic_fallback',
            'action': 'proceed_with_caution',
            'confidence': 0.3,
            'message': 'Proceeding with caution using generic fallback strategy'
        }
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get Uncertainty Handler specific status."""
        return {
            'total_uncertainties': len(self.uncertainty_assessments),
            'pending_clarifications': len([r for r in self.clarification_requests.values() 
                                         if r.request_id not in self.clarification_responses]),
            'resolved_uncertainties': len(self.clarification_responses),
            'confidence_threshold': self.confidence_threshold,
            'max_clarification_attempts': self.max_clarification_attempts,
            'user_interaction_callbacks': len(self.user_interaction_callbacks),
        }