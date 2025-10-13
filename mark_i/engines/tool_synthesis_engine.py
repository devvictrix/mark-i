"""
Tool Synthesis Engine for MARK-I hierarchical AI architecture.

This module provides self-improvement capabilities through automated tool synthesis,
including capability gap analysis, tool specification design, code generation,
and security validation with sandboxing mechanisms.
"""

import ast
import logging
import subprocess
import tempfile
import os
import sys
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import IToolSynthesisEngine, ExecutionResult, Context
from mark_i.core.architecture_config import ToolSynthesisConfig

logger = logging.getLogger("mark_i.engines.tool_synthesis_engine")


class CapabilityGapType(Enum):
    """Types of capability gaps that can be identified."""
    MISSING_FUNCTIONALITY = "missing_functionality"
    PERFORMANCE_BOTTLENECK = "performance_bottleneck"
    INTEGRATION_GAP = "integration_gap"
    USER_WORKFLOW_GAP = "user_workflow_gap"
    AUTOMATION_OPPORTUNITY = "automation_opportunity"
    ERROR_HANDLING_GAP = "error_handling_gap"
    DATA_PROCESSING_GAP = "data_processing_gap"


class ToolComplexity(Enum):
    """Complexity levels for generated tools."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"


class SecurityRisk(Enum):
    """Security risk levels for tool validation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CapabilityGap:
    """Represents an identified capability gap."""
    gap_id: str
    gap_type: CapabilityGapType
    description: str
    problem_context: Dict[str, Any]
    impact_assessment: str
    urgency: str
    suggested_solutions: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ToolSpecification:
    """Specification for a tool to be synthesized."""
    spec_id: str
    gap_id: str
    tool_name: str
    tool_description: str
    functionality_requirements: List[str]
    input_parameters: Dict[str, str]
    output_format: str
    complexity: ToolComplexity
    dependencies: List[str]
    security_requirements: List[str]
    performance_requirements: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class GeneratedTool:
    """Represents a generated tool with its code and metadata."""
    tool_id: str
    spec_id: str
    tool_name: str
    generated_code: str
    code_hash: str
    dependencies: List[str]
    security_analysis: Dict[str, Any]
    validation_results: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if not self.code_hash:
            self.code_hash = hashlib.sha256(self.generated_code.encode()).hexdigest()


@dataclass
class SecurityValidation:
    """Results of security validation for a generated tool."""
    validation_id: str
    tool_id: str
    risk_level: SecurityRisk
    security_issues: List[str]
    recommendations: List[str]
    sandbox_test_results: Dict[str, Any]
    approved: bool
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ToolSynthesisEngine(ProcessingComponent, IToolSynthesisEngine):
    """
    Engine for automated tool synthesis and self-improvement.
    
    Analyzes capability gaps, designs tool specifications, generates code,
    and validates security with sandboxing mechanisms.
    """ 
   
    def __init__(self, config: Optional[ToolSynthesisConfig] = None):
        """Initialize the Tool Synthesis Engine."""
        super().__init__("tool_synthesis_engine", config)
        
        # Configuration
        self.synthesis_config = config or ToolSynthesisConfig()
        
        # Capability gap tracking
        self.capability_gaps: Dict[str, CapabilityGap] = {}
        self.tool_specifications: Dict[str, ToolSpecification] = {}
        self.generated_tools: Dict[str, GeneratedTool] = {}
        self.security_validations: Dict[str, SecurityValidation] = {}
        
        # Counters
        self.gap_counter = 0
        self.spec_counter = 0
        self.tool_counter = 0
        self.validation_counter = 0
        
        # Analysis data
        self.problem_patterns: List[Dict[str, Any]] = []
        self.solution_templates: Dict[str, str] = {}
        self.security_rules: List[Dict[str, Any]] = []
        
        # Sandbox configuration
        self.sandbox_timeout = getattr(self.synthesis_config, 'sandbox_timeout_seconds', 60.0)
        self.max_tool_complexity = getattr(self.synthesis_config, 'max_tool_complexity', 100)
        
    def _initialize_component(self) -> bool:
        """Initialize the Tool Synthesis Engine component."""
        try:
            # Initialize solution templates
            self._initialize_solution_templates()
            
            # Initialize security rules
            self._initialize_security_rules()
            
            self.logger.info("Tool Synthesis Engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Tool Synthesis Engine: {e}")
            return False
    
    def identify_capability_gap(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Identify capability gaps for a given problem."""
        try:
            # Analyze the problem to identify gaps
            gap_analysis = self._analyze_problem_for_gaps(problem)
            
            if not gap_analysis['gaps_found']:
                return {
                    'status': 'no_gaps_identified',
                    'message': 'No significant capability gaps found',
                    'analysis': gap_analysis
                }
            
            # Create capability gap objects
            identified_gaps = []
            for gap_data in gap_analysis['identified_gaps']:
                gap = CapabilityGap(
                    gap_id=f"gap_{self.gap_counter}",
                    gap_type=CapabilityGapType(gap_data['type']),
                    description=gap_data['description'],
                    problem_context=problem,
                    impact_assessment=gap_data['impact'],
                    urgency=gap_data['urgency'],
                    suggested_solutions=gap_data['solutions']
                )
                
                self.gap_counter += 1
                self.capability_gaps[gap.gap_id] = gap
                identified_gaps.append(asdict(gap))
            
            self.logger.info(f"Identified {len(identified_gaps)} capability gaps")
            
            return {
                'status': 'gaps_identified',
                'gaps': identified_gaps,
                'analysis': gap_analysis,
                'recommendations': self._generate_gap_recommendations(identified_gaps)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to identify capability gap: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def design_tool_specification(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """Design specification for a new tool."""
        try:
            gap_id = gap.get('gap_id')
            if not gap_id or gap_id not in self.capability_gaps:
                return {'status': 'error', 'message': 'Invalid or missing capability gap'}
            
            capability_gap = self.capability_gaps[gap_id]
            
            # Design tool specification
            spec_design = self._design_tool_for_gap(capability_gap)
            
            # Create tool specification
            tool_spec = ToolSpecification(
                spec_id=f"spec_{self.spec_counter}",
                gap_id=gap_id,
                tool_name=spec_design['tool_name'],
                tool_description=spec_design['description'],
                functionality_requirements=spec_design['requirements'],
                input_parameters=spec_design['input_params'],
                output_format=spec_design['output_format'],
                complexity=ToolComplexity(spec_design['complexity']),
                dependencies=spec_design['dependencies'],
                security_requirements=spec_design['security_requirements'],
                performance_requirements=spec_design['performance_requirements']
            )
            
            self.spec_counter += 1
            self.tool_specifications[tool_spec.spec_id] = tool_spec
            
            self.logger.info(f"Designed tool specification: {tool_spec.tool_name}")
            
            return {
                'status': 'specification_created',
                'specification': asdict(tool_spec),
                'design_rationale': spec_design['rationale']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to design tool specification: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def generate_tool_code(self, spec: Dict[str, Any]) -> str:
        """Generate code for a new tool."""
        try:
            spec_id = spec.get('spec_id')
            if not spec_id or spec_id not in self.tool_specifications:
                raise ValueError("Invalid or missing tool specification")
            
            tool_spec = self.tool_specifications[spec_id]
            
            # Check complexity limits
            if self._assess_tool_complexity(tool_spec) > self.max_tool_complexity:
                raise ValueError("Tool complexity exceeds maximum allowed limit")
            
            # Generate code based on specification
            generated_code = self._generate_code_from_spec(tool_spec)
            
            # Create generated tool object
            generated_tool = GeneratedTool(
                tool_id=f"tool_{self.tool_counter}",
                spec_id=spec_id,
                tool_name=tool_spec.tool_name,
                generated_code=generated_code,
                code_hash="",  # Will be set in __post_init__
                dependencies=tool_spec.dependencies,
                security_analysis={},  # Will be filled by validation
                validation_results={}  # Will be filled by validation
            )
            
            self.tool_counter += 1
            self.generated_tools[generated_tool.tool_id] = generated_tool
            
            self.logger.info(f"Generated code for tool: {tool_spec.tool_name}")
            
            return generated_code
            
        except Exception as e:
            self.logger.error(f"Failed to generate tool code: {e}")
            raise
    
    def validate_tool_safety(self, tool_code: str) -> Dict[str, Any]:
        """Validate tool safety and security."""
        try:
            # Find the generated tool by code hash
            code_hash = hashlib.sha256(tool_code.encode()).hexdigest()
            generated_tool = None
            
            for tool in self.generated_tools.values():
                if tool.code_hash == code_hash:
                    generated_tool = tool
                    break
            
            if not generated_tool:
                return {'status': 'error', 'message': 'Tool not found in generated tools'}
            
            # Perform security analysis
            security_analysis = self._analyze_code_security(tool_code)
            
            # Perform sandbox testing
            sandbox_results = self._test_in_sandbox(tool_code, generated_tool.tool_name)
            
            # Determine risk level and approval
            risk_level = self._determine_risk_level(security_analysis, sandbox_results)
            approved = risk_level in [SecurityRisk.LOW, SecurityRisk.MEDIUM]
            
            # Create security validation
            validation = SecurityValidation(
                validation_id=f"validation_{self.validation_counter}",
                tool_id=generated_tool.tool_id,
                risk_level=risk_level,
                security_issues=security_analysis['issues'],
                recommendations=security_analysis['recommendations'],
                sandbox_test_results=sandbox_results,
                approved=approved
            )
            
            self.validation_counter += 1
            self.security_validations[validation.validation_id] = validation
            
            # Update generated tool with validation results
            generated_tool.security_analysis = security_analysis
            generated_tool.validation_results = asdict(validation)
            
            self.logger.info(f"Validated tool safety: {risk_level.value} risk, {'approved' if approved else 'rejected'}")
            
            return asdict(validation)
            
        except Exception as e:
            self.logger.error(f"Failed to validate tool safety: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def integrate_tool(self, tool_code: str, validation: Dict[str, Any]) -> ExecutionResult:
        """Integrate a new tool into the system."""
        try:
            # Check if validation passed
            if not validation.get('approved', False):
                return ExecutionResult(
                    success=False,
                    message=f"Tool integration rejected due to security concerns: {validation.get('risk_level', 'unknown')}"
                )
            
            # Find the generated tool
            validation_id = validation.get('validation_id')
            if not validation_id or validation_id not in self.security_validations:
                return ExecutionResult(
                    success=False,
                    message="Invalid validation data"
                )
            
            security_validation = self.security_validations[validation_id]
            generated_tool = self.generated_tools.get(security_validation.tool_id)
            
            if not generated_tool:
                return ExecutionResult(
                    success=False,
                    message="Generated tool not found"
                )
            
            # Perform integration
            integration_result = self._perform_tool_integration(generated_tool, security_validation)
            
            if integration_result['success']:
                self.logger.info(f"Successfully integrated tool: {generated_tool.tool_name}")
                
                # Update problem patterns with successful solution
                self._update_solution_patterns(generated_tool)
                
                return ExecutionResult(
                    success=True,
                    message=f"Tool '{generated_tool.tool_name}' integrated successfully",
                    data=integration_result
                )
            else:
                return ExecutionResult(
                    success=False,
                    message=f"Tool integration failed: {integration_result.get('error', 'Unknown error')}"
                )
                
        except Exception as e:
            self.logger.error(f"Failed to integrate tool: {e}")
            return ExecutionResult(success=False, message=str(e))
    
    def get_synthesis_metrics(self) -> Dict[str, Any]:
        """Get metrics about tool synthesis performance."""
        try:
            total_gaps = len(self.capability_gaps)
            total_specs = len(self.tool_specifications)
            total_tools = len(self.generated_tools)
            total_validations = len(self.security_validations)
            
            approved_tools = len([v for v in self.security_validations.values() if v.approved])
            
            # Calculate success rates
            spec_success_rate = total_specs / total_gaps if total_gaps > 0 else 0.0
            generation_success_rate = total_tools / total_specs if total_specs > 0 else 0.0
            validation_success_rate = approved_tools / total_validations if total_validations > 0 else 0.0
            
            # Analyze gap types
            gap_type_distribution = {}
            for gap in self.capability_gaps.values():
                gap_type = gap.gap_type.value
                gap_type_distribution[gap_type] = gap_type_distribution.get(gap_type, 0) + 1
            
            # Analyze complexity distribution
            complexity_distribution = {}
            for spec in self.tool_specifications.values():
                complexity = spec.complexity.value
                complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
            
            # Analyze security risk distribution
            risk_distribution = {}
            for validation in self.security_validations.values():
                risk = validation.risk_level.value
                risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            
            return {
                'total_capability_gaps': total_gaps,
                'total_specifications': total_specs,
                'total_generated_tools': total_tools,
                'total_validations': total_validations,
                'approved_tools': approved_tools,
                'success_rates': {
                    'specification_creation': spec_success_rate,
                    'code_generation': generation_success_rate,
                    'security_validation': validation_success_rate
                },
                'distributions': {
                    'gap_types': gap_type_distribution,
                    'tool_complexity': complexity_distribution,
                    'security_risks': risk_distribution
                },
                'learned_patterns': len(self.problem_patterns),
                'solution_templates': len(self.solution_templates)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get synthesis metrics: {e}")
            return {}
    
    # Private helper methods
    
    def _initialize_solution_templates(self) -> None:
        """Initialize solution templates for common tool patterns."""
        self.solution_templates = {
            'data_processor': '''
def process_data(input_data, processing_options=None):
    """Process input data according to specified options."""
    try:
        # Validate input
        if not input_data:
            raise ValueError("Input data cannot be empty")
        
        # Apply processing options
        options = processing_options or {}
        
        # Process data (implementation depends on specific requirements)
        processed_data = input_data  # Placeholder
        
        return {"success": True, "data": processed_data}
    except Exception as e:
        return {"success": False, "error": str(e)}
''',
            
            'api_client': '''
import requests
from typing import Dict, Any, Optional

class APIClient:
    """Generic API client for external service integration."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request to API endpoint."""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            response = self.session.request(method, url, json=data, timeout=30)
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
''',
            
            'file_processor': '''
import os
from pathlib import Path
from typing import Union, Dict, Any

def process_file(file_path: Union[str, Path], operation: str = "read") -> Dict[str, Any]:
    """Process file operations safely."""
    try:
        path = Path(file_path)
        
        # Security check - ensure path is within allowed directories
        if not _is_safe_path(path):
            raise ValueError("File path not allowed for security reasons")
        
        if operation == "read":
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content}
        
        elif operation == "exists":
            return {"success": True, "exists": path.exists()}
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def _is_safe_path(path: Path) -> bool:
    """Check if path is safe for file operations."""
    # Implement security checks
    return True  # Placeholder - implement actual security logic
'''
        }
    
    def _initialize_security_rules(self) -> None:
        """Initialize security rules for code validation."""
        self.security_rules = [
            {
                'rule_id': 'no_exec_eval',
                'description': 'Prohibit use of exec() and eval() functions',
                'pattern': r'\b(exec|eval)\s*\(',
                'severity': 'high',
                'message': 'Use of exec() or eval() is prohibited for security reasons'
            },
            {
                'rule_id': 'no_subprocess_shell',
                'description': 'Prohibit subprocess calls with shell=True',
                'pattern': r'subprocess\.[^(]*\([^)]*shell\s*=\s*True',
                'severity': 'high',
                'message': 'Subprocess calls with shell=True are prohibited'
            },
            {
                'rule_id': 'no_file_system_access',
                'description': 'Restrict file system access to safe operations',
                'pattern': r'\b(open|file)\s*\([^)]*[\'"][^\'"]*(\.\.\/|\/etc\/|\/root\/)',
                'severity': 'medium',
                'message': 'Potentially unsafe file system access detected'
            },
            {
                'rule_id': 'no_network_without_validation',
                'description': 'Network operations should include validation',
                'pattern': r'(requests\.|urllib\.|socket\.)',
                'severity': 'medium',
                'message': 'Network operations detected - ensure proper validation'
            },
            {
                'rule_id': 'no_import_os_system',
                'description': 'Prohibit os.system() calls',
                'pattern': r'os\.system\s*\(',
                'severity': 'high',
                'message': 'Use of os.system() is prohibited'
            }
        ]
    
    def _analyze_problem_for_gaps(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a problem to identify capability gaps."""
        try:
            problem_description = problem.get('description', '')
            problem_context = problem.get('context', {})
            current_capabilities = problem.get('current_capabilities', [])
            desired_outcome = problem.get('desired_outcome', '')
            
            identified_gaps = []
            
            # Analyze for missing functionality
            if 'missing' in problem_description.lower() or 'cannot' in problem_description.lower():
                identified_gaps.append({
                    'type': 'missing_functionality',
                    'description': f"Missing functionality identified: {problem_description}",
                    'impact': 'Prevents task completion',
                    'urgency': 'high',
                    'solutions': ['Create new tool', 'Extend existing capability', 'Integrate external service']
                })
            
            # Analyze for performance issues
            if any(word in problem_description.lower() for word in ['slow', 'timeout', 'performance', 'bottleneck']):
                identified_gaps.append({
                    'type': 'performance_bottleneck',
                    'description': f"Performance issue identified: {problem_description}",
                    'impact': 'Reduces efficiency and user experience',
                    'urgency': 'medium',
                    'solutions': ['Optimize existing code', 'Create faster alternative', 'Implement caching']
                })
            
            # Analyze for integration gaps
            if any(word in problem_description.lower() for word in ['integrate', 'connect', 'api', 'service']):
                identified_gaps.append({
                    'type': 'integration_gap',
                    'description': f"Integration gap identified: {problem_description}",
                    'impact': 'Limits system connectivity and data flow',
                    'urgency': 'medium',
                    'solutions': ['Create API client', 'Build integration adapter', 'Implement protocol handler']
                })
            
            # Analyze for workflow gaps
            if any(word in problem_description.lower() for word in ['workflow', 'process', 'automation']):
                identified_gaps.append({
                    'type': 'user_workflow_gap',
                    'description': f"Workflow gap identified: {problem_description}",
                    'impact': 'Interrupts user workflow and productivity',
                    'urgency': 'high',
                    'solutions': ['Create workflow automation', 'Build process optimizer', 'Implement smart assistant']
                })
            
            # Analyze for error handling gaps
            if any(word in problem_description.lower() for word in ['error', 'fail', 'exception', 'crash']):
                identified_gaps.append({
                    'type': 'error_handling_gap',
                    'description': f"Error handling gap identified: {problem_description}",
                    'impact': 'Reduces system reliability and user confidence',
                    'urgency': 'high',
                    'solutions': ['Improve error detection', 'Add recovery mechanisms', 'Create diagnostic tools']
                })
            
            return {
                'gaps_found': len(identified_gaps) > 0,
                'identified_gaps': identified_gaps,
                'analysis_confidence': 0.8,
                'problem_complexity': self._assess_problem_complexity(problem)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze problem for gaps: {e}")
            return {'gaps_found': False, 'identified_gaps': [], 'analysis_confidence': 0.0}
    
    def _assess_problem_complexity(self, problem: Dict[str, Any]) -> str:
        """Assess the complexity of a problem."""
        try:
            complexity_factors = 0
            
            description = problem.get('description', '')
            context = problem.get('context', {})
            
            # Check description complexity
            if len(description.split()) > 20:
                complexity_factors += 1
            
            # Check context complexity
            if len(context) > 5:
                complexity_factors += 1
            
            # Check for technical terms
            technical_terms = ['api', 'database', 'algorithm', 'integration', 'performance', 'security']
            if any(term in description.lower() for term in technical_terms):
                complexity_factors += 1
            
            # Determine complexity level
            if complexity_factors >= 3:
                return 'high'
            elif complexity_factors >= 2:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            self.logger.error(f"Failed to assess problem complexity: {e}")
            return 'medium'
    
    def _generate_gap_recommendations(self, gaps: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for addressing capability gaps."""
        recommendations = []
        
        gap_types = [gap['gap_type'] for gap in gaps]
        
        if 'missing_functionality' in gap_types:
            recommendations.append("Consider developing new tools to fill functionality gaps")
        
        if 'performance_bottleneck' in gap_types:
            recommendations.append("Focus on performance optimization and efficient algorithms")
        
        if 'integration_gap' in gap_types:
            recommendations.append("Prioritize API clients and integration adapters")
        
        if len(gaps) > 3:
            recommendations.append("Consider breaking down complex problems into smaller, manageable gaps")
        
        return recommendations
    
    def _design_tool_for_gap(self, gap: CapabilityGap) -> Dict[str, Any]:
        """Design a tool specification for a capability gap."""
        try:
            gap_type = gap.gap_type
            
            # Base design based on gap type
            if gap_type == CapabilityGapType.MISSING_FUNCTIONALITY:
                return self._design_functionality_tool(gap)
            elif gap_type == CapabilityGapType.PERFORMANCE_BOTTLENECK:
                return self._design_performance_tool(gap)
            elif gap_type == CapabilityGapType.INTEGRATION_GAP:
                return self._design_integration_tool(gap)
            elif gap_type == CapabilityGapType.USER_WORKFLOW_GAP:
                return self._design_workflow_tool(gap)
            elif gap_type == CapabilityGapType.ERROR_HANDLING_GAP:
                return self._design_error_handling_tool(gap)
            elif gap_type == CapabilityGapType.DATA_PROCESSING_GAP:
                return self._design_data_processing_tool(gap)
            else:
                return self._design_generic_tool(gap)
                
        except Exception as e:
            self.logger.error(f"Failed to design tool for gap: {e}")
            return self._design_generic_tool(gap)
    
    def _design_functionality_tool(self, gap: CapabilityGap) -> Dict[str, Any]:
        """Design a tool for missing functionality."""
        return {
            'tool_name': f"functionality_tool_{gap.gap_id}",
            'description': f"Tool to address missing functionality: {gap.description}",
            'requirements': [
                'Implement core functionality',
                'Handle input validation',
                'Provide error handling',
                'Return structured output'
            ],
            'input_params': {'input_data': 'Any', 'options': 'Dict[str, Any]'},
            'output_format': 'Dict[str, Any]',
            'complexity': 'moderate',
            'dependencies': ['typing'],
            'security_requirements': ['Input validation', 'Safe error handling'],
            'performance_requirements': {'max_execution_time': 30.0, 'memory_limit': '100MB'},
            'rationale': f"Addresses missing functionality gap: {gap.description}"
        }
    
    def _design_performance_tool(self, gap: CapabilityGap) -> Dict[str, Any]:
        """Design a tool for performance optimization."""
        return {
            'tool_name': f"performance_optimizer_{gap.gap_id}",
            'description': f"Performance optimization tool: {gap.description}",
            'requirements': [
                'Optimize critical operations',
                'Implement efficient algorithms',
                'Add performance monitoring',
                'Provide optimization metrics'
            ],
            'input_params': {'data': 'Any', 'optimization_level': 'str'},
            'output_format': 'Dict[str, Any]',
            'complexity': 'complex',
            'dependencies': ['typing', 'time'],
            'security_requirements': ['Resource limits', 'Safe operations'],
            'performance_requirements': {'max_execution_time': 10.0, 'memory_limit': '50MB'},
            'rationale': f"Addresses performance bottleneck: {gap.description}"
        }
    
    def _design_integration_tool(self, gap: CapabilityGap) -> Dict[str, Any]:
        """Design a tool for integration needs."""
        return {
            'tool_name': f"integration_client_{gap.gap_id}",
            'description': f"Integration client tool: {gap.description}",
            'requirements': [
                'Handle external API communication',
                'Implement authentication',
                'Provide error recovery',
                'Support multiple data formats'
            ],
            'input_params': {'endpoint': 'str', 'data': 'Dict[str, Any]', 'auth': 'Optional[str]'},
            'output_format': 'Dict[str, Any]',
            'complexity': 'moderate',
            'dependencies': ['requests', 'typing'],
            'security_requirements': ['Secure authentication', 'Input sanitization', 'Network security'],
            'performance_requirements': {'max_execution_time': 60.0, 'memory_limit': '200MB'},
            'rationale': f"Addresses integration gap: {gap.description}"
        }
    
    def _design_workflow_tool(self, gap: CapabilityGap) -> Dict[str, Any]:
        """Design a tool for workflow automation."""
        return {
            'tool_name': f"workflow_automator_{gap.gap_id}",
            'description': f"Workflow automation tool: {gap.description}",
            'requirements': [
                'Automate repetitive tasks',
                'Handle workflow steps',
                'Provide progress tracking',
                'Support error recovery'
            ],
            'input_params': {'workflow_steps': 'List[Dict[str, Any]]', 'options': 'Dict[str, Any]'},
            'output_format': 'Dict[str, Any]',
            'complexity': 'complex',
            'dependencies': ['typing', 'time'],
            'security_requirements': ['Step validation', 'Safe execution'],
            'performance_requirements': {'max_execution_time': 120.0, 'memory_limit': '300MB'},
            'rationale': f"Addresses workflow gap: {gap.description}"
        }
    
    def _design_error_handling_tool(self, gap: CapabilityGap) -> Dict[str, Any]:
        """Design a tool for error handling improvement."""
        return {
            'tool_name': f"error_handler_{gap.gap_id}",
            'description': f"Error handling tool: {gap.description}",
            'requirements': [
                'Detect and classify errors',
                'Provide recovery suggestions',
                'Log error details',
                'Support error reporting'
            ],
            'input_params': {'error_data': 'Any', 'context': 'Dict[str, Any]'},
            'output_format': 'Dict[str, Any]',
            'complexity': 'moderate',
            'dependencies': ['typing', 'logging'],
            'security_requirements': ['Safe error logging', 'Data sanitization'],
            'performance_requirements': {'max_execution_time': 15.0, 'memory_limit': '100MB'},
            'rationale': f"Addresses error handling gap: {gap.description}"
        }
    
    def _design_data_processing_tool(self, gap: CapabilityGap) -> Dict[str, Any]:
        """Design a tool for data processing needs."""
        return {
            'tool_name': f"data_processor_{gap.gap_id}",
            'description': f"Data processing tool: {gap.description}",
            'requirements': [
                'Process various data formats',
                'Implement data validation',
                'Support data transformation',
                'Provide processing metrics'
            ],
            'input_params': {'data': 'Any', 'processing_config': 'Dict[str, Any]'},
            'output_format': 'Dict[str, Any]',
            'complexity': 'moderate',
            'dependencies': ['typing'],
            'security_requirements': ['Data validation', 'Safe processing'],
            'performance_requirements': {'max_execution_time': 45.0, 'memory_limit': '500MB'},
            'rationale': f"Addresses data processing gap: {gap.description}"
        }
    
    def _design_generic_tool(self, gap: CapabilityGap) -> Dict[str, Any]:
        """Design a generic tool for unspecified gaps."""
        return {
            'tool_name': f"generic_tool_{gap.gap_id}",
            'description': f"Generic tool: {gap.description}",
            'requirements': [
                'Address identified gap',
                'Provide basic functionality',
                'Handle common use cases',
                'Support extensibility'
            ],
            'input_params': {'input_data': 'Any', 'options': 'Optional[Dict[str, Any]]'},
            'output_format': 'Dict[str, Any]',
            'complexity': 'simple',
            'dependencies': ['typing'],
            'security_requirements': ['Basic validation', 'Safe operations'],
            'performance_requirements': {'max_execution_time': 30.0, 'memory_limit': '100MB'},
            'rationale': f"Generic solution for gap: {gap.description}"
        }
    
    def _assess_tool_complexity(self, spec: ToolSpecification) -> int:
        """Assess the complexity score of a tool specification."""
        complexity_score = 0
        
        # Base complexity by type
        complexity_mapping = {
            ToolComplexity.SIMPLE: 10,
            ToolComplexity.MODERATE: 30,
            ToolComplexity.COMPLEX: 60,
            ToolComplexity.ADVANCED: 90
        }
        
        complexity_score += complexity_mapping.get(spec.complexity, 30)
        
        # Add complexity for requirements
        complexity_score += len(spec.functionality_requirements) * 5
        
        # Add complexity for dependencies
        complexity_score += len(spec.dependencies) * 3
        
        # Add complexity for security requirements
        complexity_score += len(spec.security_requirements) * 2
        
        return complexity_score
    
    def _generate_code_from_spec(self, spec: ToolSpecification) -> str:
        """Generate code based on tool specification."""
        try:
            # Select appropriate template
            template_key = self._select_template_for_spec(spec)
            base_template = self.solution_templates.get(template_key, self.solution_templates['data_processor'])
            
            # Customize template based on specification
            customized_code = self._customize_template(base_template, spec)
            
            # Add security measures
            secured_code = self._add_security_measures(customized_code, spec)
            
            # Add documentation
            documented_code = self._add_documentation(secured_code, spec)
            
            return documented_code
            
        except Exception as e:
            self.logger.error(f"Failed to generate code from spec: {e}")
            raise
    
    def _select_template_for_spec(self, spec: ToolSpecification) -> str:
        """Select the most appropriate template for a specification."""
        spec_name = spec.tool_name.lower()
        
        if 'integration' in spec_name or 'client' in spec_name or 'api' in spec_name:
            return 'api_client'
        elif 'file' in spec_name or 'processor' in spec_name:
            return 'file_processor'
        else:
            return 'data_processor'
    
    def _customize_template(self, template: str, spec: ToolSpecification) -> str:
        """Customize template based on specification."""
        # Simple customization - replace placeholders
        customized = template.replace('process_data', spec.tool_name.lower())
        customized = customized.replace('Process input data according to specified options.', spec.tool_description)
        
        return customized
    
    def _add_security_measures(self, code: str, spec: ToolSpecification) -> str:
        """Add security measures to generated code."""
        security_additions = []
        
        # Add input validation if required
        if 'Input validation' in spec.security_requirements:
            security_additions.append("""
    # Security: Input validation
    if not isinstance(input_data, (str, dict, list)):
        raise ValueError("Invalid input data type")
""")
        
        # Add resource limits if required
        if 'Resource limits' in spec.security_requirements:
            security_additions.append("""
    # Security: Resource limits
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (100*1024*1024, 100*1024*1024))  # 100MB memory limit
""")
        
        # Insert security measures at the beginning of functions
        if security_additions:
            security_code = '\n'.join(security_additions)
            # Simple insertion - in practice, would use AST manipulation
            code = code.replace('try:', f'{security_code}\n    try:')
        
        return code
    
    def _add_documentation(self, code: str, spec: ToolSpecification) -> str:
        """Add comprehensive documentation to generated code."""
        doc_header = f'''"""
{spec.tool_description}

Generated tool for capability gap: {spec.gap_id}
Complexity: {spec.complexity.value}
Dependencies: {', '.join(spec.dependencies)}

Requirements:
{chr(10).join(f"- {req}" for req in spec.functionality_requirements)}

Security Requirements:
{chr(10).join(f"- {req}" for req in spec.security_requirements)}

Generated on: {datetime.now().isoformat()}
"""

'''
        
        return doc_header + code
    
    def _analyze_code_security(self, code: str) -> Dict[str, Any]:
        """Analyze code for security issues."""
        try:
            issues = []
            recommendations = []
            
            # Check against security rules
            import re
            for rule in self.security_rules:
                if re.search(rule['pattern'], code):
                    issues.append({
                        'rule_id': rule['rule_id'],
                        'severity': rule['severity'],
                        'message': rule['message'],
                        'description': rule['description']
                    })
            
            # Generate recommendations based on issues
            if issues:
                high_severity_issues = [i for i in issues if i['severity'] == 'high']
                if high_severity_issues:
                    recommendations.append("Address high-severity security issues before deployment")
                
                medium_severity_issues = [i for i in issues if i['severity'] == 'medium']
                if medium_severity_issues:
                    recommendations.append("Review and mitigate medium-severity security concerns")
            
            # AST-based analysis for additional security checks
            try:
                tree = ast.parse(code)
                ast_issues = self._analyze_ast_security(tree)
                issues.extend(ast_issues)
            except SyntaxError as e:
                issues.append({
                    'rule_id': 'syntax_error',
                    'severity': 'high',
                    'message': f'Syntax error in generated code: {e}',
                    'description': 'Code contains syntax errors'
                })
            
            return {
                'issues': issues,
                'recommendations': recommendations,
                'security_score': self._calculate_security_score(issues),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze code security: {e}")
            return {
                'issues': [{'rule_id': 'analysis_error', 'severity': 'high', 'message': str(e)}],
                'recommendations': ['Manual security review required'],
                'security_score': 0.0
            }
    
    def _analyze_ast_security(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Analyze AST for security issues."""
        issues = []
        
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['exec', 'eval', 'compile']:
                        issues.append({
                            'rule_id': 'dangerous_function',
                            'severity': 'high',
                            'message': f'Dangerous function call: {node.func.id}',
                            'description': 'Code uses potentially dangerous functions'
                        })
            
            # Check for file operations
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    issues.append({
                        'rule_id': 'file_operation',
                        'severity': 'medium',
                        'message': 'File operation detected',
                        'description': 'Code performs file operations - ensure proper validation'
                    })
        
        return issues
    
    def _calculate_security_score(self, issues: List[Dict[str, Any]]) -> float:
        """Calculate security score based on issues."""
        if not issues:
            return 1.0
        
        severity_weights = {'low': 0.1, 'medium': 0.3, 'high': 0.7, 'critical': 1.0}
        
        total_weight = sum(severity_weights.get(issue['severity'], 0.5) for issue in issues)
        max_possible_weight = len(issues) * 1.0
        
        security_score = max(0.0, 1.0 - (total_weight / max_possible_weight))
        return security_score
    
    def _test_in_sandbox(self, code: str, tool_name: str) -> Dict[str, Any]:
        """Test code in a sandboxed environment."""
        try:
            # Create temporary file for testing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Run basic syntax check
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=self.sandbox_timeout
                )
                
                syntax_valid = result.returncode == 0
                
                # Run basic import test
                import_test_code = f"""
import sys
sys.path.insert(0, '{os.path.dirname(temp_file_path)}')
try:
    import {os.path.basename(temp_file_path)[:-3]}
    print("IMPORT_SUCCESS")
except Exception as e:
    print(f"IMPORT_ERROR: {{e}}")
"""
                
                import_result = subprocess.run(
                    [sys.executable, '-c', import_test_code],
                    capture_output=True,
                    text=True,
                    timeout=self.sandbox_timeout
                )
                
                import_success = 'IMPORT_SUCCESS' in import_result.stdout
                
                return {
                    'syntax_valid': syntax_valid,
                    'syntax_errors': result.stderr if not syntax_valid else None,
                    'import_success': import_success,
                    'import_errors': import_result.stderr if not import_success else None,
                    'test_timestamp': datetime.now().isoformat(),
                    'sandbox_timeout': self.sandbox_timeout
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except subprocess.TimeoutExpired:
            return {
                'syntax_valid': False,
                'syntax_errors': 'Sandbox test timed out',
                'import_success': False,
                'import_errors': 'Test execution timed out',
                'test_timestamp': datetime.now().isoformat(),
                'timeout': True
            }
        except Exception as e:
            return {
                'syntax_valid': False,
                'syntax_errors': str(e),
                'import_success': False,
                'import_errors': str(e),
                'test_timestamp': datetime.now().isoformat(),
                'test_error': True
            }
    
    def _determine_risk_level(self, security_analysis: Dict[str, Any], sandbox_results: Dict[str, Any]) -> SecurityRisk:
        """Determine overall risk level based on analysis results."""
        try:
            issues = security_analysis.get('issues', [])
            security_score = security_analysis.get('security_score', 1.0)
            
            # Check for critical issues
            critical_issues = [i for i in issues if i['severity'] == 'critical']
            if critical_issues:
                return SecurityRisk.CRITICAL
            
            # Check for high severity issues
            high_issues = [i for i in issues if i['severity'] == 'high']
            if high_issues:
                return SecurityRisk.HIGH
            
            # Check sandbox results
            if not sandbox_results.get('syntax_valid', True) or not sandbox_results.get('import_success', True):
                return SecurityRisk.HIGH
            
            # Check security score
            if security_score < 0.3:
                return SecurityRisk.HIGH
            elif security_score < 0.6:
                return SecurityRisk.MEDIUM
            else:
                return SecurityRisk.LOW
                
        except Exception as e:
            self.logger.error(f"Failed to determine risk level: {e}")
            return SecurityRisk.HIGH  # Default to high risk on error
    
    def _perform_tool_integration(self, tool: GeneratedTool, validation: SecurityValidation) -> Dict[str, Any]:
        """Perform the actual tool integration."""
        try:
            # In a real implementation, this would:
            # 1. Create tool file in appropriate directory
            # 2. Register tool with toolbelt
            # 3. Update tool registry
            # 4. Perform integration tests
            
            # For now, simulate successful integration
            integration_result = {
                'success': True,
                'tool_id': tool.tool_id,
                'tool_name': tool.tool_name,
                'integration_timestamp': datetime.now().isoformat(),
                'validation_id': validation.validation_id,
                'status': 'integrated'
            }
            
            self.logger.info(f"Tool integration simulated for: {tool.tool_name}")
            
            return integration_result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool_id': tool.tool_id,
                'integration_timestamp': datetime.now().isoformat()
            }
    
    def _update_solution_patterns(self, tool: GeneratedTool) -> None:
        """Update solution patterns based on successful tool integration."""
        try:
            # Extract pattern from successful tool
            pattern = {
                'tool_name': tool.tool_name,
                'spec_id': tool.spec_id,
                'code_hash': tool.code_hash,
                'success_timestamp': datetime.now().isoformat(),
                'dependencies': tool.dependencies
            }
            
            self.problem_patterns.append(pattern)
            
            # Keep only recent patterns
            if len(self.problem_patterns) > 1000:
                self.problem_patterns = self.problem_patterns[-1000:]
                
        except Exception as e:
            self.logger.error(f"Failed to update solution patterns: {e}")
    
    def process(self, input_data: Any, context: Optional[Context] = None) -> Dict[str, Any]:
        """Process input data for tool synthesis."""
        try:
            # Determine processing type based on input data
            if isinstance(input_data, dict):
                if 'description' in input_data:
                    # Treat as problem for capability gap analysis
                    return self.identify_capability_gap(input_data)
                elif 'gap_id' in input_data:
                    # Treat as gap for tool specification
                    return self.design_tool_specification(input_data)
                elif 'spec_id' in input_data:
                    # Treat as specification for code generation
                    try:
                        code = self.generate_tool_code(input_data)
                        return {'status': 'code_generated', 'code': code}
                    except Exception as e:
                        return {'status': 'error', 'message': str(e)}
            
            return {'status': 'error', 'message': 'Unsupported input data format'}
            
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_capabilities(self) -> List[str]:
        """Get list of processing capabilities."""
        return [
            'capability_gap_analysis',
            'tool_specification_design',
            'code_generation',
            'security_validation',
            'tool_integration',
            'problem_pattern_analysis',
            'solution_template_management'
        ]
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get Tool Synthesis Engine specific status."""
        base_status = super()._get_component_status()
        
        synthesis_status = {
            'capability_gaps': len(self.capability_gaps),
            'tool_specifications': len(self.tool_specifications),
            'generated_tools': len(self.generated_tools),
            'security_validations': len(self.security_validations),
            'approved_tools': len([v for v in self.security_validations.values() if v.approved]),
            'solution_templates': len(self.solution_templates),
            'security_rules': len(self.security_rules),
            'max_tool_complexity': self.max_tool_complexity,
            'sandbox_timeout': self.sandbox_timeout,
        }
        
        base_status.update(synthesis_status)
        return base_status