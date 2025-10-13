# Requirements Document

## Introduction

The Perceptual Filtering feature enables users to teach the Mark-I AI agent what visual elements to ignore during screen analysis. This system addresses the problem of "visual noise" from persistent but irrelevant screen elements (such as desktop widgets, floating video players, taskbar clocks, or notifications) that can clutter the AI's reasoning and create opportunities for distraction and error.

## Requirements

### Requirement 1

**User Story:** As a Mark-I user, I want to create a personalized ignore list of visual elements, so that the AI focuses only on relevant screen content during task execution.

#### Acceptance Criteria

1. WHEN I identify an irrelevant visual element THEN I SHALL be able to add a textual description of it to an ignore list
2. WHEN I add an element to the ignore list THEN it SHALL be persistently stored in the knowledge base
3. WHEN I view my ignore list THEN I SHALL see all previously added elements with their descriptions
4. WHEN I want to remove an element from the ignore list THEN I SHALL be able to delete it from the knowledge base

### Requirement 2

**User Story:** As a Mark-I user, I want the AI to automatically exclude ignored elements from its analysis, so that task execution is more focused and accurate.

#### Acceptance Criteria

1. WHEN the AI analyzes a screenshot THEN it SHALL exclude any elements that match descriptions in the ignore list
2. WHEN the WorldModel updates its entity graph THEN it SHALL not include entities that match ignore list criteria
3. WHEN generating reasoning prompts THEN the system SHALL filter out ignored elements before sending to the LLM
4. WHEN an ignored element appears on screen THEN it SHALL not influence the AI's decision-making process

### Requirement 3

**User Story:** As a Mark-I user, I want an intuitive interface to manage my perceptual filters, so that I can easily customize what the AI ignores.

#### Acceptance Criteria

1. WHEN I discover a new irrelevant element during AI operation THEN I SHALL be able to quickly add it to the ignore list through the Knowledge Curator interface
2. WHEN using the Knowledge Curator Window THEN I SHALL see an option to mark discovered elements as "Ignored" instead of saving them as named entities
3. WHEN managing my ignore list THEN I SHALL be able to view, edit, and delete existing filter entries
4. WHEN adding elements to ignore THEN the interface SHALL provide clear feedback about what was added

### Requirement 4

**User Story:** As a developer integrating with Mark-I, I want the perceptual filtering to work seamlessly with existing components, so that minimal code changes are required.

#### Acceptance Criteria

1. WHEN the KnowledgeBase loads THEN it SHALL automatically include the perceptual_filters section with an ignore_list
2. WHEN the AgentCore requests entity analysis THEN the WorldModel SHALL automatically apply ignore list filtering
3. WHEN the ignore list is updated THEN all subsequent AI analysis SHALL immediately use the new filters
4. WHEN integrating perceptual filtering THEN existing entity detection and reasoning logic SHALL remain unchanged