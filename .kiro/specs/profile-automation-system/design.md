# Profile Automation System Design Document

## Overview

This design outlines a comprehensive Profile Automation System for MARK-I that enables users to create, manage, and execute intelligent automation workflows through a visual interface. The system integrates seamlessly with the Eye-Brain-Hand architecture, providing a user-friendly way to define regions, rules, and actions for complex automation tasks like email sending, web browsing, and data collection.

## Architecture

### System Components

```
mark_i/
├── profiles/                    # Profile management system
│   ├── __init__.py
│   ├── profile_manager.py       # Core profile management
│   ├── profile_executor.py      # Profile execution engine
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── profile.py           # Profile data model
│   │   ├── region.py            # Region definition model
│   │   ├── rule.py              # Rule and condition models
│   │   └── action.py            # Action definition models
│   ├── templates/               # Profile templates
│   │   ├── __init__.py
│   │   ├── email_templates.py
│   │   ├── web_templates.py
│   │   └── file_templates.py
│   ├── validation/              # Profile validation
│   │   ├── __init__.py
│   │   ├── profile_validator.py
│   │   └── rule_validator.py
│   └── ui/                      # Profile UI components
│       ├── __init__.py
│       ├── profile_editor.py    # Main profile editor
│       ├── region_selector.py   # Visual region selection
│       ├── rule_builder.py      # Rule creation interface
│       └── profile_manager_ui.py # Profile management UI
├── ui/gui/                      # Existing GUI components
│   ├── profile_editor_window.py # New profile editor window
│   └── profile_manager_window.py # New profile manager window
└── storage/profiles/            # Enhanced profile storage
    ├── email/                   # Email automation profiles
    ├── web/                     # Web browsing profiles
    ├── files/                   # File management profiles
    ├── templates/               # Template profiles
    └── custom/                  # User custom profiles
```

## Data Models

### Profile Model

```python
@dataclass
class AutomationProfile:
    """Complete automation profile definition"""
    id: str
    name: str
    description: str
    category: str
    target_application: str
    created_at: datetime
    modified_at: datetime
    version: str
    
    # Core components
    regions: List[Region]
    rules: List[Rule]
    settings: ProfileSettings
    
    # Metadata
    tags: List[str]
    author: str
    is_template: bool
    parent_template: Optional[str]
```

### Region Model

```python
@dataclass
class Region:
    """Screen region definition for automation"""
    name: str
    x: int
    y: int
    width: int
    height: int
    description: str
    
    # Region properties
    monitor_index: int = 0
    is_relative: bool = False
    parent_region: Optional[str] = None
    
    # Visual properties
    expected_colors: Optional[List[Tuple[int, int, int]]] = None
    template_image: Optional[str] = None
    ocr_enabled: bool = False
    
    # Behavior
    retry_count: int = 3
    timeout_seconds: int = 5
```

### Rule Model

```python
@dataclass
class Rule:
    """Automation rule with conditions and actions"""
    name: str
    description: str
    enabled: bool = True
    priority: int = 0
    
    # Conditions
    conditions: List[Condition]
    logical_operator: str = "AND"  # AND, OR
    
    # Actions
    actions: List[Action]
    
    # Execution settings
    max_retries: int = 3
    retry_delay: float = 1.0
    continue_on_failure: bool = False

@dataclass
class Condition:
    """Rule condition definition"""
    type: str  # visual_match, ocr_contains, template_match, system_state
    region: str
    parameters: Dict[str, Any]
    negate: bool = False

@dataclass
class Action:
    """Action definition"""
    type: str  # click, type_text, wait, ask_user, run_command
    region: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    delay_before: float = 0.0
    delay_after: float = 0.0
```

## Core Components

### 1. Profile Manager

**Purpose:** Central management of automation profiles

**Key Features:**
- CRUD operations for profiles
- Profile organization and categorization
- Template management
- Import/export functionality
- Version control

```python
class ProfileManager:
    def create_profile(self, name: str, category: str) -> AutomationProfile
    def load_profile(self, profile_id: str) -> AutomationProfile
    def save_profile(self, profile: AutomationProfile) -> bool
    def delete_profile(self, profile_id: str) -> bool
    def list_profiles(self, category: Optional[str] = None) -> List[AutomationProfile]
    def search_profiles(self, query: str) -> List[AutomationProfile]
    def duplicate_profile(self, profile_id: str, new_name: str) -> AutomationProfile
```

### 2. Profile Executor

**Purpose:** Execute automation profiles using Eye-Brain-Hand architecture

**Integration Points:**
- **Eye (CaptureEngine):** Screen capture and visual analysis
- **Brain (AgentCore):** Decision making and ReAct loops
- **Hand (ActionExecutor):** Precise action execution

```python
class ProfileExecutor:
    def __init__(self, capture_engine, agent_core, action_executor):
        self.eye = capture_engine
        self.brain = agent_core  
        self.hand = action_executor
    
    def execute_profile(self, profile: AutomationProfile) -> ExecutionResult
    def execute_rule(self, rule: Rule, context: ExecutionContext) -> RuleResult
    def evaluate_condition(self, condition: Condition, region_data: Any) -> bool
    def perform_action(self, action: Action, context: ExecutionContext) -> ActionResult
```

### 3. Visual Profile Editor

**Purpose:** User-friendly interface for creating and editing profiles

**Key Features:**
- Drag-and-drop region selection
- Visual rule builder
- Real-time preview
- Template integration
- Validation feedback

```python
class ProfileEditorWindow(customtkinter.CTkToplevel):
    def __init__(self):
        # Main editor interface
        self.region_selector = RegionSelector()
        self.rule_builder = RuleBuilder()
        self.action_configurator = ActionConfigurator()
        
    def create_new_profile(self)
    def load_profile_for_editing(self, profile_id: str)
    def save_current_profile(self)
    def preview_profile_execution(self)
```

## Profile Templates

### Email Automation Template

```python
EMAIL_TEMPLATE = AutomationProfile(
    name="Email Automation Template",
    description="Template for email sending automation",
    category="email",
    regions=[
        Region("recipient_field", 100, 200, 300, 30, "Email recipient input field"),
        Region("subject_field", 100, 240, 300, 30, "Email subject input field"),
        Region("body_field", 100, 280, 400, 200, "Email body text area"),
        Region("send_button", 350, 500, 80, 30, "Send email button")
    ],
    rules=[
        Rule(
            name="Fill Email Form",
            conditions=[
                Condition("visual_match", "recipient_field", {"visible": True})
            ],
            actions=[
                Action("click", "recipient_field"),
                Action("type_text", parameters={"text": "{recipient}"}),
                Action("click", "subject_field"),
                Action("type_text", parameters={"text": "{subject}"}),
                Action("click", "body_field"),
                Action("type_text", parameters={"text": "{body}"}),
                Action("wait", parameters={"seconds": 1}),
                Action("click", "send_button")
            ]
        )
    ]
)
```

### Web Search Template

```python
WEB_SEARCH_TEMPLATE = AutomationProfile(
    name="Web Search Template",
    description="Template for web search automation",
    category="web",
    regions=[
        Region("search_box", 300, 100, 400, 40, "Search input box"),
        Region("search_button", 720, 100, 80, 40, "Search submit button"),
        Region("results_area", 200, 200, 800, 600, "Search results area"),
        Region("first_result", 200, 220, 600, 80, "First search result")
    ],
    rules=[
        Rule(
            name="Perform Search",
            conditions=[
                Condition("visual_match", "search_box", {"visible": True})
            ],
            actions=[
                Action("click", "search_box"),
                Action("type_text", parameters={"text": "{search_query}"}),
                Action("click", "search_button"),
                Action("wait_for_visual_cue", parameters={
                    "region": "results_area",
                    "cue_description": "Search results loaded"
                })
            ]
        ),
        Rule(
            name="Click First Result",
            conditions=[
                Condition("visual_match", "first_result", {"visible": True})
            ],
            actions=[
                Action("click", "first_result")
            ]
        )
    ]
)
```

## Integration with Eye-Brain-Hand Architecture

### Eye Integration (Visual Perception)

```python
class ProfileVisualAnalyzer:
    def __init__(self, capture_engine, gemini_analyzer):
        self.capture_engine = capture_engine
        self.gemini_analyzer = gemini_analyzer
    
    def analyze_region(self, region: Region) -> RegionAnalysis:
        """Analyze a specific region using visual AI"""
        screenshot = self.capture_engine.capture_region(
            region.x, region.y, region.width, region.height
        )
        
        analysis = self.gemini_analyzer.analyze_image(
            screenshot, 
            f"Analyze this region: {region.description}"
        )
        
        return RegionAnalysis(
            region=region,
            visual_elements=analysis.elements,
            text_content=analysis.text if region.ocr_enabled else None,
            confidence=analysis.confidence
        )
```

### Brain Integration (Decision Making)

```python
class ProfileDecisionEngine:
    def __init__(self, agent_core):
        self.agent_core = agent_core
    
    def evaluate_rule_conditions(self, rule: Rule, context: ExecutionContext) -> bool:
        """Use AI to evaluate complex rule conditions"""
        
        # Gather visual data for all regions referenced in conditions
        region_data = {}
        for condition in rule.conditions:
            if condition.region:
                region_data[condition.region] = context.get_region_analysis(condition.region)
        
        # Use AgentCore to make intelligent decisions
        decision_prompt = self._create_decision_prompt(rule, region_data)
        decision = self.agent_core.make_decision(decision_prompt)
        
        return decision.should_execute
    
    def handle_uncertainty(self, context: ExecutionContext, uncertainty: str) -> str:
        """Handle uncertain situations using ask_user"""
        return self.agent_core.ask_user(
            f"I'm uncertain about: {uncertainty}. How should I proceed?"
        )
```

### Hand Integration (Action Execution)

```python
class ProfileActionExecutor:
    def __init__(self, action_executor):
        self.action_executor = action_executor
    
    def execute_action(self, action: Action, context: ExecutionContext) -> ActionResult:
        """Execute profile action with precise control"""
        
        if action.delay_before > 0:
            time.sleep(action.delay_before)
        
        result = None
        
        if action.type == "click":
            region = context.get_region(action.region)
            result = self.action_executor.click(
                region.x + region.width // 2,
                region.y + region.height // 2
            )
        
        elif action.type == "type_text":
            text = action.parameters.get("text", "")
            # Support parameter substitution
            text = self._substitute_parameters(text, context.variables)
            result = self.action_executor.type_text(text)
        
        elif action.type == "wait_for_visual_cue":
            cue_description = action.parameters.get("cue_description")
            region = context.get_region(action.parameters.get("region"))
            result = self._wait_for_visual_cue(region, cue_description)
        
        elif action.type == "ask_user":
            question = action.parameters.get("question")
            result = self.action_executor.ask_user(question)
        
        if action.delay_after > 0:
            time.sleep(action.delay_after)
        
        return ActionResult(action=action, success=result.success, data=result.data)
```

## User Interface Design

### Profile Editor Interface

```
┌─────────────────────────────────────────────────────────────┐
│ MARK-I Profile Editor - Email Automation                    │
├─────────────────────────────────────────────────────────────┤
│ Profile Info │ Regions │ Rules │ Actions │ Test │ Save      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─── Screen Preview ────────────────────────────────────┐   │
│ │                                                       │   │
│ │  [Recipient Field Region]                             │   │
│ │  [Subject Field Region]                               │   │
│ │  [Body Field Region]                                  │   │
│ │                                                       │   │
│ │  [Send Button Region]                                 │   │
│ │                                                       │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─── Region Properties ─────────────────────────────────┐   │
│ │ Name: recipient_field                                 │   │
│ │ Position: (100, 200) Size: 300x30                    │   │
│ │ Description: Email recipient input field              │   │
│ │ ☑ OCR Enabled  ☐ Template Match                      │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─── Rules ─────────────────────────────────────────────┐   │
│ │ Rule 1: Fill Email Form                               │   │
│ │ ├─ Condition: recipient_field is visible             │   │
│ │ ├─ Action: Click recipient_field                      │   │
│ │ ├─ Action: Type {recipient}                           │   │
│ │ └─ Action: Click send_button                          │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling and Validation

### Profile Validation

```python
class ProfileValidator:
    def validate_profile(self, profile: AutomationProfile) -> ValidationResult:
        errors = []
        warnings = []
        
        # Validate regions
        for region in profile.regions:
            if region.width <= 0 or region.height <= 0:
                errors.append(f"Region '{region.name}' has invalid dimensions")
        
        # Validate rules
        for rule in profile.rules:
            for condition in rule.conditions:
                if condition.region not in [r.name for r in profile.regions]:
                    errors.append(f"Rule '{rule.name}' references unknown region '{condition.region}'")
        
        # Validate actions
        for rule in profile.rules:
            for action in rule.actions:
                if action.region and action.region not in [r.name for r in profile.regions]:
                    errors.append(f"Action in rule '{rule.name}' references unknown region '{action.region}'")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

## Testing and Debugging

### Profile Testing Framework

```python
class ProfileTester:
    def __init__(self, profile_executor):
        self.executor = profile_executor
    
    def test_profile(self, profile: AutomationProfile, test_mode: str = "simulation") -> TestResult:
        """Test profile execution in different modes"""
        
        if test_mode == "simulation":
            return self._simulate_execution(profile)
        elif test_mode == "step_by_step":
            return self._step_through_execution(profile)
        elif test_mode == "visual_validation":
            return self._validate_visual_recognition(profile)
    
    def _simulate_execution(self, profile: AutomationProfile) -> TestResult:
        """Simulate profile execution without performing actual actions"""
        results = []
        
        for rule in profile.rules:
            # Simulate condition evaluation
            condition_results = []
            for condition in rule.conditions:
                # Mock condition evaluation
                result = self._mock_condition_evaluation(condition)
                condition_results.append(result)
            
            # Simulate action execution
            if all(condition_results):
                action_results = []
                for action in rule.actions:
                    result = self._mock_action_execution(action)
                    action_results.append(result)
                results.append(RuleTestResult(rule, True, action_results))
            else:
                results.append(RuleTestResult(rule, False, []))
        
        return TestResult(profile, results)
```

This comprehensive design provides a complete foundation for the Profile Automation System that integrates seamlessly with MARK-I's Eye-Brain-Hand architecture while providing an intuitive user interface for creating and managing automation workflows.