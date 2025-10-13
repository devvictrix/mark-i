"""
Engines module for MARK-I hierarchical AI architecture.

This module contains specialized processing engines that handle specific
aspects of the MARK-I system, including analysis, capture, decision making,
and tool synthesis for self-improvement.

Components:
- ToolSynthesisEngine: Automated tool synthesis and self-improvement
- GeminiAnalyzer: AI-powered analysis using Google Gemini
- CaptureEngine: Screen and environment capture
- AnalysisEngine: General analysis and processing
- RulesEngine: Rule-based decision making
"""

from .tool_synthesis_engine import ToolSynthesisEngine
from .dynamic_tool_manager import DynamicToolManager
from .ethical_reasoning_engine import EthicalReasoningEngine
from .safety_prioritization_engine import SafetyPrioritizationEngine

__all__ = [
    'ToolSynthesisEngine',
    'DynamicToolManager',
    'EthicalReasoningEngine',
    'SafetyPrioritizationEngine'
]