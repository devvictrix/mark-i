"""
Dynamic Tool Manager for MARK-I Tool Synthesis Engine.

This module provides dynamic tool integration and management capabilities including
tool validation pipelines, dynamic loading systems, and comprehensive performance monitoring.
"""

import importlib
import importlib.util
import logging
import os
import tempfile
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.interfaces import ExecutionResult
from mark_i.core.architecture_config import ComponentConfig

logger = logging.getLogger("mark_i.engines.dynamic_tool_manager")


class ToolStatus(Enum):
    """Status of a managed tool."""
    PENDING_VALIDATION = "pending_validation"
    VALIDATING = "validating"
    VALIDATION_FAILED = "validation_failed"
    VALIDATED = "validated"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEPRECATED = "deprecated"


class ValidationStage(Enum):
    """Stages of tool validation."""
    SYNTAX_CHECK = "syntax_check"
    SECURITY_SCAN = "security_scan"
    DEPENDENCY_CHECK = "dependency_check"
    INTERFACE_VALIDATION = "interface_validation"
    PERFORMANCE_TEST = "performance_test"
    INTEGRATION_TEST = "integration_test"


class PerformanceMetric(Enum):
    """Performance metrics tracked for tools."""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class ManagedTool:
    """Represents a dynamically managed tool."""
    tool_id: str
    tool_name: str
    tool_code: str
    code_hash: str
    status: ToolStatus
    metadata: Dict[str, Any]
    dependencies: List[str]
    validation_results: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    usage_statistics: Dict[str, Any]
    loaded_module: Optional[Any] = None
    created_at: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_updated is None:
            self.last_updated = self.created_at
        if not self.code_hash:
            self.code_hash = hashlib.sha256(self.tool_code.encode()).hexdigest()


@dataclass
class ValidationResult:
    """Result of tool validation."""
    validation_id: str
    tool_id: str
    stage: ValidationStage
    success: bool
    details: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class PerformanceSnapshot:
    """Snapshot of tool performance metrics."""
    snapshot_id: str
    tool_id: str
    metrics: Dict[PerformanceMetric, float]
    context: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class DynamicToolManager(ProcessingComponent):
    """
    Manages dynamic tool integration, validation, and performance monitoring.
    
    Provides comprehensive tool lifecycle management including validation pipelines,
    dynamic loading, integration testing, and continuous performance monitoring.
    """
    
    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.managed_tools: Dict[str, ManagedTool] = {}
        self.validation_pipeline: List[Callable] = []
        self.performance_monitors: Dict[str, threading.Thread] = {}
        self.validation_lock = threading.Lock()
        self.tool_registry_lock = threading.Lock()
        self.temp_dir = tempfile.mkdtemp(prefix="mark_i_tools_")
        
        # Initialize validation pipeline
        self._setup_validation_pipeline()
        
        # Performance monitoring settings
        self.monitoring_interval = getattr(config, "monitoring_interval", 30)  # seconds
        self.performance_history_limit = getattr(config, "performance_history_limit", 1000)
        self.performance_data: Dict[str, List[PerformanceSnapshot]] = {}
        
        logger.info(f"DynamicToolManager initialized with temp dir: {self.temp_dir}")
    
    def _setup_validation_pipeline(self):
        """Set up the tool validation pipeline stages."""
        self.validation_pipeline = [
            self._validate_syntax,
            self._validate_security,
            self._validate_dependencies,
            self._validate_interface,
            self._validate_performance,
            self._validate_integration
        ]
        logger.debug(f"Validation pipeline configured with {len(self.validation_pipeline)} stages")
    
    def register_tool(self, tool_code: str, tool_name: str, metadata: Dict[str, Any] = None) -> str:
        """
        Register a new tool for validation and integration.
        
        Args:
            tool_code: The Python code for the tool
            tool_name: Name of the tool
            metadata: Additional metadata about the tool
            
        Returns:
            Tool ID for tracking
        """
        tool_id = f"tool_{int(time.time() * 1000)}_{hashlib.md5(tool_name.encode()).hexdigest()[:8]}"
        
        managed_tool = ManagedTool(
            tool_id=tool_id,
            tool_name=tool_name,
            tool_code=tool_code,
            code_hash="",  # Will be set in __post_init__
            status=ToolStatus.PENDING_VALIDATION,
            metadata=metadata or {},
            dependencies=[],
            validation_results={},
            performance_metrics={},
            usage_statistics={"usage_count": 0, "last_used": None}
        )
        
        with self.tool_registry_lock:
            self.managed_tools[tool_id] = managed_tool
        
        logger.info(f"Registered tool '{tool_name}' with ID: {tool_id}")
        
        # Start validation process asynchronously
        validation_thread = threading.Thread(
            target=self._validate_tool_async,
            args=(tool_id,),
            daemon=True
        )
        validation_thread.start()
        
        return tool_id
    
    def _validate_tool_async(self, tool_id: str):
        """Asynchronously validate a tool through the validation pipeline."""
        try:
            with self.validation_lock:
                tool = self.managed_tools.get(tool_id)
                if not tool:
                    logger.error(f"Tool {tool_id} not found for validation")
                    return
                
                tool.status = ToolStatus.VALIDATING
                logger.info(f"Starting validation for tool {tool_id}")
                
                # Run through validation pipeline
                all_passed = True
                for stage_func in self.validation_pipeline:
                    try:
                        result = stage_func(tool)
                        tool.validation_results[result.stage.value] = asdict(result)
                        
                        if not result.success:
                            all_passed = False
                            logger.warning(f"Tool {tool_id} failed validation stage {result.stage.value}: {result.issues}")
                            break
                        else:
                            logger.debug(f"Tool {tool_id} passed validation stage {result.stage.value}")
                            
                    except Exception as e:
                        logger.error(f"Validation stage failed for tool {tool_id}: {e}")
                        all_passed = False
                        break
                
                # Update tool status based on validation results
                if all_passed:
                    tool.status = ToolStatus.VALIDATED
                    logger.info(f"Tool {tool_id} successfully validated")
                    # Attempt to load the tool
                    self._load_tool(tool_id)
                else:
                    tool.status = ToolStatus.VALIDATION_FAILED
                    logger.error(f"Tool {tool_id} failed validation")
                
                tool.last_updated = datetime.now()
                
        except Exception as e:
            logger.error(f"Error during tool validation for {tool_id}: {e}")
            if tool_id in self.managed_tools:
                self.managed_tools[tool_id].status = ToolStatus.ERROR
    
    def _validate_syntax(self, tool: ManagedTool) -> ValidationResult:
        """Validate tool code syntax."""
        issues = []
        recommendations = []
        
        try:
            # Attempt to compile the code
            compile(tool.tool_code, f"<tool_{tool.tool_id}>", "exec")
            success = True
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
            success = False
        except Exception as e:
            issues.append(f"Compilation error: {e}")
            success = False
        
        return ValidationResult(
            validation_id=f"syntax_{tool.tool_id}_{int(time.time())}",
            tool_id=tool.tool_id,
            stage=ValidationStage.SYNTAX_CHECK,
            success=success,
            details={"code_length": len(tool.tool_code)},
            issues=issues,
            recommendations=recommendations
        )
    
    def _validate_security(self, tool: ManagedTool) -> ValidationResult:
        """Validate tool security - check for dangerous operations."""
        issues = []
        recommendations = []
        
        # List of potentially dangerous operations
        dangerous_patterns = [
            "exec(", "eval(", "__import__", "open(", "file(",
            "subprocess", "os.system", "os.popen", "os.remove",
            "shutil.rmtree", "socket.", "urllib", "requests"
        ]
        
        security_score = 100
        for pattern in dangerous_patterns:
            if pattern in tool.tool_code:
                issues.append(f"Potentially dangerous operation detected: {pattern}")
                security_score -= 10
        
        # Check for imports that might be risky
        risky_imports = ["os", "sys", "subprocess", "socket", "urllib", "requests"]
        for imp in risky_imports:
            if f"import {imp}" in tool.tool_code or f"from {imp}" in tool.tool_code:
                recommendations.append(f"Consider restricting access to {imp} module")
                security_score -= 5
        
        success = security_score >= 70  # Threshold for acceptable security
        
        return ValidationResult(
            validation_id=f"security_{tool.tool_id}_{int(time.time())}",
            tool_id=tool.tool_id,
            stage=ValidationStage.SECURITY_SCAN,
            success=success,
            details={"security_score": security_score},
            issues=issues,
            recommendations=recommendations
        )
    
    def _validate_dependencies(self, tool: ManagedTool) -> ValidationResult:
        """Validate tool dependencies."""
        issues = []
        recommendations = []
        dependencies = []
        
        # Extract import statements
        lines = tool.tool_code.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                # Extract module name
                if line.startswith('import '):
                    module = line.replace('import ', '').split()[0].split('.')[0]
                else:  # from ... import
                    module = line.split()[1].split('.')[0]
                
                if module not in dependencies:
                    dependencies.append(module)
        
        # Check if dependencies are available
        missing_deps = []
        for dep in dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing_deps.append(dep)
        
        tool.dependencies = dependencies
        
        if missing_deps:
            issues.extend([f"Missing dependency: {dep}" for dep in missing_deps])
            success = False
        else:
            success = True
        
        return ValidationResult(
            validation_id=f"deps_{tool.tool_id}_{int(time.time())}",
            tool_id=tool.tool_id,
            stage=ValidationStage.DEPENDENCY_CHECK,
            success=success,
            details={"dependencies": dependencies, "missing": missing_deps},
            issues=issues,
            recommendations=recommendations
        )
    
    def _validate_interface(self, tool: ManagedTool) -> ValidationResult:
        """Validate tool interface compliance."""
        issues = []
        recommendations = []
        
        # Check if tool defines required interface elements
        found_elements = []
        
        # Check for execute function
        if "def execute(" in tool.tool_code:
            found_elements.append("execute")
        else:
            issues.append("Missing required element: execute function")
        
        # Check for documentation (more flexible check)
        if ('"""' in tool.tool_code or "'''" in tool.tool_code or 
            "__doc__" in tool.tool_code or "def execute(" in tool.tool_code):
            found_elements.append("__doc__")
        else:
            recommendations.append("Consider adding documentation for better maintainability")
        
        success = "execute" in found_elements  # Only require execute function
        
        return ValidationResult(
            validation_id=f"interface_{tool.tool_id}_{int(time.time())}",
            tool_id=tool.tool_id,
            stage=ValidationStage.INTERFACE_VALIDATION,
            success=success,
            details={"found_elements": found_elements},
            issues=issues,
            recommendations=recommendations
        )
    
    def _validate_performance(self, tool: ManagedTool) -> ValidationResult:
        """Validate tool performance characteristics."""
        issues = []
        recommendations = []
        
        # Basic performance validation - check code complexity
        code_lines = len([line for line in tool.tool_code.split('\n') if line.strip()])
        complexity_score = min(100, max(0, 100 - (code_lines / 10)))  # Simple heuristic
        
        if code_lines > 500:
            issues.append("Tool code is very long, may impact performance")
        elif code_lines > 200:
            recommendations.append("Consider breaking down large functions")
        
        # Check for potential performance issues
        performance_concerns = ["while True:", "for i in range(", "time.sleep("]
        for concern in performance_concerns:
            if concern in tool.tool_code:
                recommendations.append(f"Potential performance concern: {concern}")
        
        success = len(issues) == 0
        
        return ValidationResult(
            validation_id=f"perf_{tool.tool_id}_{int(time.time())}",
            tool_id=tool.tool_id,
            stage=ValidationStage.PERFORMANCE_TEST,
            success=success,
            details={"code_lines": code_lines, "complexity_score": complexity_score},
            issues=issues,
            recommendations=recommendations
        )
    
    def _validate_integration(self, tool: ManagedTool) -> ValidationResult:
        """Validate tool integration capabilities."""
        issues = []
        recommendations = []
        
        # Check if tool can be integrated with existing system
        integration_score = 100
        
        # Check for MARK-I specific patterns
        mark_i_patterns = ["mark_i", "ExecutionResult", "logger"]
        found_patterns = sum(1 for pattern in mark_i_patterns if pattern in tool.tool_code)
        
        if found_patterns == 0:
            recommendations.append("Consider using MARK-I specific interfaces for better integration")
            integration_score -= 20
        
        success = integration_score >= 60
        
        return ValidationResult(
            validation_id=f"integration_{tool.tool_id}_{int(time.time())}",
            tool_id=tool.tool_id,
            stage=ValidationStage.INTEGRATION_TEST,
            success=success,
            details={"integration_score": integration_score, "mark_i_patterns": found_patterns},
            issues=issues,
            recommendations=recommendations
        )
    
    def _load_tool(self, tool_id: str) -> bool:
        """Load a validated tool into the system."""
        tool = self.managed_tools.get(tool_id)
        if not tool or tool.status != ToolStatus.VALIDATED:
            logger.error(f"Cannot load tool {tool_id}: not validated")
            return False
        
        try:
            tool.status = ToolStatus.LOADING
            
            # Create a temporary file for the tool code
            tool_file = os.path.join(self.temp_dir, f"{tool.tool_name}_{tool_id}.py")
            with open(tool_file, 'w') as f:
                f.write(tool.tool_code)
            
            # Load the module
            spec = importlib.util.spec_from_file_location(f"dynamic_tool_{tool_id}", tool_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            tool.loaded_module = module
            tool.status = ToolStatus.LOADED
            tool.last_updated = datetime.now()
            
            logger.info(f"Successfully loaded tool {tool_id}")
            
            # Start performance monitoring
            self._start_performance_monitoring(tool_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load tool {tool_id}: {e}")
            tool.status = ToolStatus.ERROR
            return False
    
    def _start_performance_monitoring(self, tool_id: str):
        """Start performance monitoring for a loaded tool."""
        if tool_id in self.performance_monitors:
            return  # Already monitoring
        
        def monitor_performance():
            while tool_id in self.managed_tools and self.managed_tools[tool_id].status in [ToolStatus.LOADED, ToolStatus.ACTIVE]:
                try:
                    tool = self.managed_tools[tool_id]
                    
                    # Collect performance metrics
                    metrics = {
                        PerformanceMetric.MEMORY_USAGE: self._get_memory_usage(tool_id),
                        PerformanceMetric.SUCCESS_RATE: self._calculate_success_rate(tool_id),
                        PerformanceMetric.ERROR_RATE: self._calculate_error_rate(tool_id)
                    }
                    
                    snapshot = PerformanceSnapshot(
                        snapshot_id=f"perf_{tool_id}_{int(time.time())}",
                        tool_id=tool_id,
                        metrics=metrics,
                        context={"status": tool.status.value}
                    )
                    
                    # Store performance data
                    if tool_id not in self.performance_data:
                        self.performance_data[tool_id] = []
                    
                    self.performance_data[tool_id].append(snapshot)
                    
                    # Limit history size
                    if len(self.performance_data[tool_id]) > self.performance_history_limit:
                        self.performance_data[tool_id] = self.performance_data[tool_id][-self.performance_history_limit:]
                    
                    time.sleep(self.monitoring_interval)
                    
                except Exception as e:
                    logger.error(f"Error monitoring tool {tool_id}: {e}")
                    break
        
        monitor_thread = threading.Thread(target=monitor_performance, daemon=True)
        monitor_thread.start()
        self.performance_monitors[tool_id] = monitor_thread
        
        logger.debug(f"Started performance monitoring for tool {tool_id}")
    
    def _get_memory_usage(self, tool_id: str) -> float:
        """Get memory usage for a tool (placeholder implementation)."""
        # In a real implementation, you'd measure actual memory usage
        return 0.0
    
    def _calculate_success_rate(self, tool_id: str) -> float:
        """Calculate success rate for a tool."""
        tool = self.managed_tools.get(tool_id)
        if not tool:
            return 0.0
        
        usage_stats = tool.usage_statistics
        total_uses = usage_stats.get("usage_count", 0)
        successful_uses = usage_stats.get("successful_uses", 0)
        
        if total_uses == 0:
            return 100.0  # No uses yet, assume perfect
        
        return (successful_uses / total_uses) * 100.0
    
    def _calculate_error_rate(self, tool_id: str) -> float:
        """Calculate error rate for a tool."""
        return 100.0 - self._calculate_success_rate(tool_id)
    
    def get_tool_status(self, tool_id: str) -> Optional[ToolStatus]:
        """Get the current status of a tool."""
        tool = self.managed_tools.get(tool_id)
        return tool.status if tool else None
    
    def get_tool_performance(self, tool_id: str) -> Optional[List[PerformanceSnapshot]]:
        """Get performance history for a tool."""
        return self.performance_data.get(tool_id)
    
    def execute_tool(self, tool_id: str, *args, **kwargs) -> ExecutionResult:
        """Execute a loaded tool."""
        tool = self.managed_tools.get(tool_id)
        if not tool:
            return ExecutionResult(
                success=False,
                message=f"Tool {tool_id} not found",
                data={}
            )
        
        if tool.status != ToolStatus.LOADED:
            return ExecutionResult(
                success=False,
                message=f"Tool {tool_id} not loaded (status: {tool.status.value})",
                data={}
            )
        
        try:
            tool.status = ToolStatus.ACTIVE
            start_time = time.time()
            
            # Execute the tool
            if hasattr(tool.loaded_module, 'execute'):
                result = tool.loaded_module.execute(*args, **kwargs)
            else:
                return ExecutionResult(
                    success=False,
                    message="Tool does not have execute method",
                    data={}
                )
            
            execution_time = time.time() - start_time
            
            # Update usage statistics
            tool.usage_statistics["usage_count"] = tool.usage_statistics.get("usage_count", 0) + 1
            tool.usage_statistics["last_used"] = datetime.now()
            tool.usage_statistics["successful_uses"] = tool.usage_statistics.get("successful_uses", 0) + 1
            tool.usage_statistics["total_execution_time"] = tool.usage_statistics.get("total_execution_time", 0) + execution_time
            
            tool.status = ToolStatus.LOADED
            
            return ExecutionResult(
                success=True,
                message="Tool executed successfully",
                data={"result": result, "execution_time": execution_time, "tool_id": tool_id}
            )
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_id}: {e}")
            tool.status = ToolStatus.LOADED
            
            # Update error statistics
            tool.usage_statistics["usage_count"] = tool.usage_statistics.get("usage_count", 0) + 1
            tool.usage_statistics["error_count"] = tool.usage_statistics.get("error_count", 0) + 1
            
            return ExecutionResult(
                success=False,
                message=f"Tool execution failed: {str(e)}",
                data={"tool_id": tool_id}
            )
    
    def list_tools(self, status_filter: Optional[ToolStatus] = None) -> List[Dict[str, Any]]:
        """List all managed tools with optional status filtering."""
        tools = []
        for tool_id, tool in self.managed_tools.items():
            if status_filter is None or tool.status == status_filter:
                tools.append({
                    "tool_id": tool_id,
                    "tool_name": tool.tool_name,
                    "status": tool.status.value,
                    "created_at": tool.created_at.isoformat(),
                    "last_updated": tool.last_updated.isoformat(),
                    "usage_count": tool.usage_statistics.get("usage_count", 0),
                    "success_rate": self._calculate_success_rate(tool_id)
                })
        return tools
    
    def remove_tool(self, tool_id: str) -> bool:
        """Remove a tool from management."""
        if tool_id not in self.managed_tools:
            return False
        
        try:
            # Stop performance monitoring
            if tool_id in self.performance_monitors:
                # The monitoring thread will stop when the tool is removed
                del self.performance_monitors[tool_id]
            
            # Remove performance data
            if tool_id in self.performance_data:
                del self.performance_data[tool_id]
            
            # Remove tool file if it exists
            tool = self.managed_tools[tool_id]
            tool_file = os.path.join(self.temp_dir, f"{tool.tool_name}_{tool_id}.py")
            if os.path.exists(tool_file):
                os.remove(tool_file)
            
            # Remove from registry
            del self.managed_tools[tool_id]
            
            logger.info(f"Removed tool {tool_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing tool {tool_id}: {e}")
            return False
    
    def process(self, input_data: Any) -> ExecutionResult:
        """Process input through the dynamic tool manager."""
        # This could be used for batch operations or management commands
        if isinstance(input_data, dict):
            command = input_data.get("command")
            
            if command == "list_tools":
                tools = self.list_tools()
                return ExecutionResult(
                    success=True,
                    message="Tools listed successfully",
                    data={"tools": tools, "command": "list_tools", "count": len(tools)}
                )
            elif command == "get_status":
                tool_id = input_data.get("tool_id")
                status = self.get_tool_status(tool_id)
                return ExecutionResult(
                    success=status is not None,
                    message="Tool status retrieved" if status else "Tool not found",
                    data={"status": status.value if status else None, "command": "get_status", "tool_id": tool_id}
                )
        
        return ExecutionResult(
            success=False,
            message="Invalid input for DynamicToolManager",
            data={}
        )
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop all monitoring threads
            for tool_id in list(self.performance_monitors.keys()):
                if tool_id in self.managed_tools:
                    del self.managed_tools[tool_id]  # This will stop monitoring
            
            # Clean up temporary directory
            if os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
            
            logger.info("DynamicToolManager cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()