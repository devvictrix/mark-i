"""
Core interfaces and abstract base classes for MARK-I hierarchical AI architecture.

This module defines the foundational interfaces that all core components must implement,
ensuring consistent communication patterns and separation of concerns across the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np


# --- Core Data Models ---

class Priority(Enum):
    """Priority levels for tasks and operations."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class CollaborationStyle(Enum):
    """Collaboration styles for human-AI interaction."""
    AUTONOMOUS = "autonomous"
    COLLABORATIVE = "collaborative"
    SUPERVISED = "supervised"


@dataclass
class Context:
    """Represents the current environmental and task context."""
    timestamp: datetime
    screen_state: Optional[np.ndarray] = None
    active_applications: List[str] = None
    user_activity: Optional[str] = None
    system_state: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.active_applications is None:
            self.active_applications = []
        if self.system_state is None:
            self.system_state = {}


@dataclass
class Action:
    """Represents an action to be executed."""
    name: str
    parameters: Dict[str, Any]
    expected_outcome: Optional[str] = None
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class Observation:
    """Represents an observation from the environment."""
    timestamp: datetime
    data: Any
    source: str
    confidence: float = 1.0


@dataclass
class Goal:
    """Represents a goal to be achieved."""
    description: str
    priority: Priority = Priority.MEDIUM
    deadline: Optional[datetime] = None
    success_criteria: List[str] = None
    context: Optional[Context] = None
    
    def __post_init__(self):
        if self.success_criteria is None:
            self.success_criteria = []


@dataclass
class ExecutionResult:
    """Represents the result of an execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}


# --- Core Interfaces ---

class IComponent(ABC):
    """Base interface for all MARK-I components."""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the component. Returns True if successful."""
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """Shutdown the component gracefully. Returns True if successful."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current component status and health information."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the component name."""
        pass


class IConfigurable(ABC):
    """Interface for components that can be configured."""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> bool:
        """Configure the component with provided settings."""
        pass
    
    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration."""
        pass
    
    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """Validate a configuration before applying it."""
        pass


class IObservable(ABC):
    """Interface for components that can be observed."""
    
    @abstractmethod
    def add_observer(self, observer: Callable[[Dict[str, Any]], None]) -> None:
        """Add an observer callback."""
        pass
    
    @abstractmethod
    def remove_observer(self, observer: Callable[[Dict[str, Any]], None]) -> None:
        """Remove an observer callback."""
        pass
    
    @abstractmethod
    def notify_observers(self, event: Dict[str, Any]) -> None:
        """Notify all observers of an event."""
        pass


# --- Cognitive Layer Interfaces ---

class IAgencyCore(IComponent, IConfigurable, IObservable):
    """Interface for the Agency Core (Strategic/Proactive reasoning)."""
    
    @abstractmethod
    def monitor_environment(self) -> List[Dict[str, Any]]:
        """Monitor environment for opportunities. Returns list of opportunities."""
        pass
    
    @abstractmethod
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate an opportunity and return assessment."""
        pass
    
    @abstractmethod
    def suggest_automation(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate automation suggestion based on assessment."""
        pass
    
    @abstractmethod
    def learn_from_interaction(self, interaction: Dict[str, Any]) -> None:
        """Learn from user interaction to improve future suggestions."""
        pass
    
    @abstractmethod
    def update_strategic_knowledge(self, knowledge: Dict[str, Any]) -> None:
        """Update strategic knowledge base."""
        pass


class IAgentCore(IComponent, IConfigurable, IObservable):
    """Interface for the Agent Core (Tactical/Reactive execution)."""
    
    @abstractmethod
    def execute_command(self, command: str, context: Optional[Context] = None) -> ExecutionResult:
        """Execute a direct command."""
        pass
    
    @abstractmethod
    def execute_goal(self, goal: Goal) -> ExecutionResult:
        """Execute a goal using ReAct loops."""
        pass
    
    @abstractmethod
    def think(self, context: Context) -> Dict[str, Any]:
        """Perform reasoning step in ReAct loop."""
        pass
    
    @abstractmethod
    def act(self, action: Action, context: Context) -> ExecutionResult:
        """Perform action step in ReAct loop."""
        pass
    
    @abstractmethod
    def observe(self, result: ExecutionResult) -> Observation:
        """Perform observation step in ReAct loop."""
        pass
    
    @abstractmethod
    def handle_uncertainty(self, uncertainty: Dict[str, Any]) -> Dict[str, Any]:
        """Handle uncertainty by asking for clarification or making assumptions."""
        pass


class IStrategicExecutor(IComponent, IConfigurable):
    """Interface for strategic planning and execution coordination."""
    
    @abstractmethod
    def create_plan(self, goal: Goal, context: Context) -> Dict[str, Any]:
        """Create a strategic plan for achieving a goal."""
        pass
    
    @abstractmethod
    def execute_plan(self, plan: Dict[str, Any]) -> ExecutionResult:
        """Execute a strategic plan."""
        pass
    
    @abstractmethod
    def adapt_plan(self, plan: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt a plan based on execution feedback."""
        pass


# --- Processing Engine Interfaces ---

class IProcessingEngine(IComponent, IConfigurable):
    """Base interface for specialized processing engines."""
    
    @abstractmethod
    def process(self, input_data: Any, context: Optional[Context] = None) -> Dict[str, Any]:
        """Process input data and return results."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of processing capabilities."""
        pass


class IToolSynthesisEngine(IProcessingEngine):
    """Interface for tool synthesis and self-improvement."""
    
    @abstractmethod
    def identify_capability_gap(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Identify capability gaps for a given problem."""
        pass
    
    @abstractmethod
    def design_tool_specification(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """Design specification for a new tool."""
        pass
    
    @abstractmethod
    def generate_tool_code(self, spec: Dict[str, Any]) -> str:
        """Generate code for a new tool."""
        pass
    
    @abstractmethod
    def validate_tool_safety(self, tool_code: str) -> Dict[str, Any]:
        """Validate tool safety and security."""
        pass
    
    @abstractmethod
    def integrate_tool(self, tool_code: str, validation: Dict[str, Any]) -> ExecutionResult:
        """Integrate a new tool into the system."""
        pass


class IPerceptualFilter(IProcessingEngine):
    """Interface for perceptual filtering and attention management."""
    
    @abstractmethod
    def identify_focus_targets(self, context: Context) -> List[Dict[str, Any]]:
        """Identify targets that should receive attention."""
        pass
    
    @abstractmethod
    def apply_attention_filter(self, image: np.ndarray, targets: List[Dict[str, Any]]) -> np.ndarray:
        """Apply attention filtering to an image."""
        pass
    
    @abstractmethod
    def learn_ignore_patterns(self, patterns: List[Dict[str, Any]]) -> None:
        """Learn patterns that should be ignored."""
        pass
    
    @abstractmethod
    def adapt_focus_strategy(self, feedback: Dict[str, Any]) -> None:
        """Adapt focus strategy based on feedback."""
        pass
    
    @abstractmethod
    def optimize_processing_efficiency(self) -> Dict[str, Any]:
        """Optimize processing efficiency and return metrics."""
        pass


class ISelfCorrectionEngine(IProcessingEngine):
    """Interface for self-correction and learning from failures."""
    
    @abstractmethod
    def detect_failure(self, execution_result: ExecutionResult) -> Dict[str, Any]:
        """Detect and analyze failures."""
        pass
    
    @abstractmethod
    def analyze_failure_cause(self, failure: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the root cause of a failure."""
        pass
    
    @abstractmethod
    def generate_alternative_strategies(self, cause: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alternative strategies to address the failure."""
        pass
    
    @abstractmethod
    def test_strategy_viability(self, strategy: Dict[str, Any]) -> float:
        """Test the viability of a strategy and return confidence score."""
        pass
    
    @abstractmethod
    def implement_correction(self, strategy: Dict[str, Any]) -> ExecutionResult:
        """Implement a correction strategy."""
        pass
    
    @abstractmethod
    def update_strategy_knowledge(self, correction: Dict[str, Any]) -> None:
        """Update strategy knowledge based on correction results."""
        pass


# --- Perception Layer Interfaces ---

class IPerceptionEngine(IComponent, IConfigurable, IObservable):
    """Interface for multi-modal environmental sensing."""
    
    @abstractmethod
    def capture_visual(self, region: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """Capture visual information from the environment."""
        pass
    
    @abstractmethod
    def analyze_visual(self, image: np.ndarray, context: Optional[Context] = None) -> Dict[str, Any]:
        """Analyze visual information."""
        pass
    
    @abstractmethod
    def detect_changes(self, previous: np.ndarray, current: np.ndarray) -> Dict[str, Any]:
        """Detect changes between two visual states."""
        pass
    
    @abstractmethod
    def extract_text(self, image: np.ndarray) -> str:
        """Extract text from visual information."""
        pass


class ICaptureEngine(IComponent, IConfigurable):
    """Interface for screen capture functionality."""
    
    @abstractmethod
    def capture_screen(self) -> np.ndarray:
        """Capture the entire screen."""
        pass
    
    @abstractmethod
    def capture_region(self, region: Dict[str, Any]) -> np.ndarray:
        """Capture a specific region of the screen."""
        pass
    
    @abstractmethod
    def capture_window(self, window_id: str) -> np.ndarray:
        """Capture a specific window."""
        pass


# --- Action Layer Interfaces ---

class IActionExecutor(IComponent, IConfigurable):
    """Interface for GUI interaction and action execution."""
    
    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> ExecutionResult:
        """Perform a click action."""
        pass
    
    @abstractmethod
    def type_text(self, text: str) -> ExecutionResult:
        """Type text."""
        pass
    
    @abstractmethod
    def key_press(self, key: str) -> ExecutionResult:
        """Press a key."""
        pass
    
    @abstractmethod
    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> ExecutionResult:
        """Perform a drag action."""
        pass
    
    @abstractmethod
    def scroll(self, x: int, y: int, direction: str, amount: int) -> ExecutionResult:
        """Perform a scroll action."""
        pass


class IToolbelt(IComponent, IConfigurable):
    """Interface for tool management and execution."""
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """Get list of available tools."""
        pass
    
    @abstractmethod
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Execute a tool with given parameters."""
        pass
    
    @abstractmethod
    def add_tool(self, tool_name: str, tool_implementation: Any) -> bool:
        """Add a new tool to the toolbelt."""
        pass
    
    @abstractmethod
    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from the toolbelt."""
        pass
    
    @abstractmethod
    def get_tool_description(self, tool_name: str) -> str:
        """Get description of a specific tool."""
        pass
    
    @abstractmethod
    def get_tools_description(self) -> str:
        """Get description of all available tools."""
        pass


class IWorldModel(IComponent, IConfigurable):
    """Interface for world state tracking and modeling."""
    
    @abstractmethod
    def update_state(self, observation: Observation) -> None:
        """Update world state with new observation."""
        pass
    
    @abstractmethod
    def get_current_state(self) -> Dict[str, Any]:
        """Get current world state."""
        pass
    
    @abstractmethod
    def predict_state_change(self, action: Action) -> Dict[str, Any]:
        """Predict how an action will change the world state."""
        pass
    
    @abstractmethod
    def get_entities(self) -> List[Dict[str, Any]]:
        """Get all tracked entities in the world."""
        pass
    
    @abstractmethod
    def add_entity(self, entity: Dict[str, Any]) -> None:
        """Add a new entity to track."""
        pass
    
    @abstractmethod
    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from tracking."""
        pass


# --- Knowledge & Memory Interfaces ---

class IKnowledgeBase(IComponent, IConfigurable):
    """Interface for learning and memory management."""
    
    @abstractmethod
    def store_experience(self, experience: Dict[str, Any]) -> None:
        """Store a new experience."""
        pass
    
    @abstractmethod
    def retrieve_similar_experiences(self, context: Context, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve similar experiences based on context."""
        pass
    
    @abstractmethod
    def update_application_knowledge(self, app_info: Dict[str, Any]) -> None:
        """Update knowledge about an application."""
        pass
    
    @abstractmethod
    def learn_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """Learn and update user preferences."""
        pass
    
    @abstractmethod
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get current user preferences."""
        pass
    
    @abstractmethod
    def organize_knowledge_graph(self) -> Dict[str, Any]:
        """Organize and return knowledge graph structure."""
        pass


class IEnhancedSystemContext(IComponent, IConfigurable, IObservable):
    """Interface for enhanced system context awareness."""
    
    @abstractmethod
    def track_system_state(self) -> Dict[str, Any]:
        """Track comprehensive system state."""
        pass
    
    @abstractmethod
    def analyze_application_context(self) -> Dict[str, Any]:
        """Analyze current application context."""
        pass
    
    @abstractmethod
    def detect_environmental_changes(self) -> List[Dict[str, Any]]:
        """Detect changes in the environment."""
        pass
    
    @abstractmethod
    def adapt_to_context(self, context: Context) -> None:
        """Adapt behavior based on context."""
        pass


# --- Interface Layer ---

class ISymbiosisInterface(IComponent, IConfigurable, IObservable):
    """Interface for human-AI collaboration."""
    
    @abstractmethod
    def communicate_with_user(self, message: str, message_type: str = "info") -> Optional[str]:
        """Communicate with the user and optionally get response."""
        pass
    
    @abstractmethod
    def ask_for_clarification(self, question: str, options: Optional[List[str]] = None) -> str:
        """Ask user for clarification."""
        pass
    
    @abstractmethod
    def request_permission(self, action: str, risk_level: str = "low") -> bool:
        """Request permission from user for an action."""
        pass
    
    @abstractmethod
    def adapt_communication_style(self, feedback: Dict[str, Any]) -> None:
        """Adapt communication style based on user feedback."""
        pass
    
    @abstractmethod
    def assess_trust_level(self) -> float:
        """Assess current trust level with user."""
        pass
    
    @abstractmethod
    def manage_autonomy_boundaries(self, boundaries: Dict[str, Any]) -> None:
        """Manage autonomy boundaries based on trust and user preferences."""
        pass


class IEthicalReasoningEngine(IProcessingEngine):
    """Interface for ethical reasoning and decision making."""
    
    @abstractmethod
    def evaluate_action_ethics(self, action: Action, context: Context) -> Dict[str, Any]:
        """Evaluate the ethical implications of an action."""
        pass
    
    @abstractmethod
    def assess_risk_level(self, action: Action, context: Context) -> str:
        """Assess the risk level of an action."""
        pass
    
    @abstractmethod
    def suggest_alternatives(self, action: Action, ethical_issues: Dict[str, Any]) -> List[Action]:
        """Suggest alternative actions when ethical issues are detected."""
        pass
    
    @abstractmethod
    def update_ethical_guidelines(self, guidelines: Dict[str, Any]) -> None:
        """Update ethical guidelines."""
        pass
    
    @abstractmethod
    def get_ethical_guidelines(self) -> Dict[str, Any]:
        """Get current ethical guidelines."""
        pass


# --- Extensibility Interfaces ---

class IPlugin(IComponent, IConfigurable):
    """Interface for plugin system."""
    
    @abstractmethod
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin information including name, version, capabilities."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get list of plugin dependencies."""
        pass
    
    @abstractmethod
    def validate_compatibility(self, system_version: str) -> bool:
        """Validate compatibility with system version."""
        pass


class IPluginManager(IComponent, IConfigurable):
    """Interface for plugin management."""
    
    @abstractmethod
    def load_plugin(self, plugin_path: str) -> bool:
        """Load a plugin from path."""
        pass
    
    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        pass
    
    @abstractmethod
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugins."""
        pass
    
    @abstractmethod
    def validate_plugin(self, plugin_path: str) -> Dict[str, Any]:
        """Validate a plugin before loading."""
        pass
    
    @abstractmethod
    def resolve_dependencies(self, plugin_name: str) -> List[str]:
        """Resolve plugin dependencies."""
        pass


# --- Event System ---

@dataclass
class Event:
    """Represents a system event."""
    type: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime = None
    priority: Priority = Priority.MEDIUM
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}


class IEventBus(IComponent):
    """Interface for event-driven communication between components."""
    
    @abstractmethod
    def publish(self, event: Event) -> None:
        """Publish an event."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to events of a specific type."""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from events."""
        pass
    
    @abstractmethod
    def get_subscribers(self, event_type: str) -> List[Callable[[Event], None]]:
        """Get list of subscribers for an event type."""
        pass