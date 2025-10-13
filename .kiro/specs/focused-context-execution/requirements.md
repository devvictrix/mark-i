# Requirements Document

## Introduction

The Focused Context Execution feature enables the Mark-I AI agent to intelligently identify and focus on specific application windows during task execution, rather than processing full-screen captures. This optimization significantly improves performance by reducing API costs, decreasing latency, and increasing accuracy by eliminating visual distractions from irrelevant screen elements.

## Requirements

### Requirement 1

**User Story:** As a Mark-I user, I want the AI agent to automatically focus on the relevant application window when executing tasks, so that task execution is faster and more accurate.

#### Acceptance Criteria

1. WHEN a user provides a command that targets a specific application THEN the system SHALL identify the primary application window before generating the execution plan
2. WHEN the system identifies a target application window THEN it SHALL crop the visual context to that window's bounding box
3. WHEN executing actions within the focused context THEN the system SHALL translate relative coordinates to absolute screen positions
4. WHEN no specific application can be identified THEN the system SHALL fall back to full-screen context execution

### Requirement 2

**User Story:** As a Mark-I user, I want the system to reduce API costs and processing time, so that I can use the automation tool more efficiently.

#### Acceptance Criteria

1. WHEN using focused context execution THEN the system SHALL send smaller cropped images to the vision model API instead of full-screen captures
2. WHEN processing cropped images THEN the system SHALL complete analysis faster than full-screen processing
3. WHEN calculating costs THEN focused context execution SHALL result in measurably lower API usage costs
4. WHEN switching between focused and full-screen modes THEN the performance difference SHALL be transparent to the user

### Requirement 3

**User Story:** As a Mark-I user, I want the AI to avoid being distracted by irrelevant screen elements, so that task execution is more reliable and accurate.

#### Acceptance Criteria

1. WHEN executing tasks in focused context THEN the system SHALL exclude notifications, widgets, and other applications from analysis
2. WHEN the AI analyzes the cropped context THEN it SHALL focus only on elements within the target application window
3. WHEN multiple applications are visible THEN the system SHALL correctly identify and focus on the most relevant one for the given command
4. WHEN the focused context changes during execution THEN the system SHALL maintain accuracy within the defined boundaries

### Requirement 4

**User Story:** As a developer integrating with Mark-I, I want the focused context execution to work seamlessly with existing components, so that minimal code changes are required.

#### Acceptance Criteria

1. WHEN the StrategicExecutor determines focused context THEN it SHALL provide the cropped image and coordinate offset to the AgentCore
2. WHEN the AgentCore receives focused context THEN it SHALL operate normally without knowing whether the context is cropped or full-screen
3. WHEN the ActionExecutor processes actions THEN it SHALL automatically apply coordinate offsets to translate relative positions to absolute screen coordinates
4. WHEN integrating focused context THEN existing ReAct loop logic SHALL remain unchanged