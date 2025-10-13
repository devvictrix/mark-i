# Product Overview

MARK-I is an AI-powered visual automation agent that serves as a proactive desktop assistant. It uses Google Gemini to see, understand, and interact with any GUI, moving beyond simple automation to learn from its environment and execute complex, multi-step goals from natural language commands.

## Core Capabilities

- **Interactive Command Core**: Execute direct commands in plain English using ReAct (Reason+Act) cognitive loops
- **Proactive Agency Core**: Passively observe user's screen and proactively suggest automations based on core directives
- **Knowledge Discovery & Memory**: Learn about user's environment and store knowledge in persistent knowledge base
- **Self-Correcting Strategies**: Use Objective-Strategy-Tactic (OST) pattern with self-correction capabilities
- **Focused Context Execution**: Intelligently identify app windows and focus vision/actions for efficiency
- **AI-Driven Profile Creator**: Interactive wizard to translate high-level goals into reusable automation profiles

## Architecture Philosophy

The system uses a hierarchical, multi-core AI architecture where different agents handle distinct levels of cognition:
- **Agency Core**: The strategist - operates proactively, observing and generating goals
- **Strategic Executor**: The planner - creates high-level, multi-step plans
- **Agent Core**: The tactician - executes plans using ReAct loops and toolbelt capabilities

This separation of concerns enables highly complex, robust, and adaptive behavior while maintaining efficiency through focused context execution and perceptual filtering.