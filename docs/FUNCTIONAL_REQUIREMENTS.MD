# Functional Requirements for Mark-I

This document outlines the functional requirements for the Mark-I visual automation tool, describing _what_ the system will do.
**This version reflects the completed capabilities of v5.0.0 and incorporates the new requirements for v6.0.0: Autonomous Assistant.**

## FR-CORE: Core System

- **FR-CORE-001: Cross-Platform Operation:** The bot's core runtime engine and GUI editor SHOULD operate on Windows, macOS, and Linux. (Primary development and testing on Windows).
- **FR-CORE-002: Configuration Files (JSON):** The system MUST use JSON for saving and loading bot configurations (profiles).
- **FR-CORE-003: Environment Configuration:** The system MUST read environment variables (e.g., from `.env` file via `python-dotenv`) for `APP_ENV` (influencing logging) and sensitive data like `GEMINI_API_KEY`.
- **FR-CORE-004: Logging:** The system MUST implement comprehensive, persistent, and configurable logging for all significant operations.

## FR-CAPTURE: Screen Region Capture Module

- **FR-CAPTURE-001: Define Target Region (Manual & AI-Assisted):** The user MUST be able to define specific, named rectangular regions on the screen for use in profiles.
- **FR-CAPTURE-002: Capture Specified Region (Runtime):** The system MUST capture image data from defined regions during profile-based bot runtime.
- **FR-CAPTURE-003: Real-time Capture (Runtime):** The system MUST support continuous real-time capture at a user-configurable interval for profile-based execution.
- **FR-CAPTURE-004: Full Screen/Window Capture:** The system MUST be able to capture the entire screen or a specified application window. This is used for context in AI Profile Generation (v5) and for the Observe phase of the Autonomous Assistant (v6).
- **FR-CAPTURE-005: Screen Dimension Detection:** The system (via `CaptureEngine`) MUST be able to programmatically determine the dimensions of the primary display to enable reliable full-screen captures.

## FR-ANALYZE: Region Analysis & AI Understanding Module

- **FR-ANALYZE-001 - FR-ANALYZE-009:** (Local analysis types, `gemini_vision_query`, `gemini_perform_task` NLU - as is for profile-based runtime).
- **FR-ANALYZE-010: AI Goal-to-Plan Generation (v5.0.0 - Profile Generation):** The `StrategyPlanner` module MUST accept a high-level user goal and generate a structured, intermediate plan of sub-steps.
- **FR-ANALYZE-011: AI Plan-Step-to-Profile-Element Suggestion (v5.0.0 - Profile Generation):** The `ProfileGenerator` module MUST be able to suggest specific Mark-I profile elements (regions, conditions, actions) to implement a given plan step.
- **FR-ANALYZE-012: AI Template Identification Hint (v5.0.0 - Profile Generation):** The system MUST be able to suggest when a visual template is the best tool for a given step during AI profile generation.

## FR-ACTION: Action Execution & Task Orchestration Module

- **FR-ACTION-001 - FR-ACTION-009:** (Primitive actions like click/type, `gemini_perform_task` execution - as is for profile-based runtime).
- **FR-ACTION-010: Assembling AI-Generated Profile Actions (v5.0.0 - Profile Generation):** The `ProfileGenerator` MUST correctly assemble user-confirmed and AI-assisted action specifications into the standard Mark-I action structure.

## FR-CONFIG: Configuration & Management (CLI, GUI, AI Generation)

- **FR-CONFIG-001 - FR-CONFIG-009:** (Profile I/O, variable capture, AI Profile Generation workflow - as is).

## FR-UI: User Interface

- **FR-UI-001 - FR-UI-008:** (CLI, `MainAppWindow`, `ProfileCreationWizardWindow`, and helper windows - as is).

## FR-AUTONOMY: Autonomous Assistant (v6.0.0)

- **FR-AUTONOMY-001: Independent Operation:** The Autonomous Assistant (managed by `AutonomyEngine`) MUST operate as a distinct mode, separate from the profile-based execution of `MainController`. It MUST run in its own background thread.
- **FR-AUTONOMY-002: Continuous Observation:** The `AutonomyEngine` MUST periodically capture an image of the full screen to serve as its observational context.
- **FR-AUTONOMY-003: Proactive Task Assessment:** The `AutonomyEngine` MUST use its `GeminiAnalyzer` to send the full screen capture to a multimodal AI model. The model MUST be prompted to analyze the visual context, infer user activity, and identify potential tasks that Mark-I can assist with.
- **FR-AUTONOMY-004: Task Identification:** The system MUST parse the AI's assessment response. If a task is identified with a confidence score above a configurable threshold, the system MUST extract a concise, actionable "derived goal" for that task.
- **FR-AUTONOMY-005: Dynamic Plan Generation:** For an identified task, the `AutonomyEngine` MUST pass the `derived_goal` to the `StrategyPlanner` to generate a dynamic, multi-step `IntermediatePlan`.
- **FR-AUTONOMY-006: User Confirmation (Safety Layer):** Before any execution, the system MUST present the generated plan to the user in a clear, non-blocking GUI dialog (`AutonomyConfirmationDialog`). This dialog MUST require explicit user consent ("Allow") to proceed. A "Deny" option or closing the dialog MUST cancel the proposed task.
- **FR-AUTONOMY-007: Autonomous Execution:** Upon user confirmation, the `AutonomyEngine` MUST pass the `derived_goal` and its context to the `GeminiDecisionModule` to orchestrate the execution of the task.
- **FR-AUTONOMY-008: GUI Control:** The main application GUI (`MainAppWindow`) MUST provide controls to manually start and stop the `AutonomyEngine`.
- **FR-AUTONOMY-009: GUI Status Feedback:** The main application GUI (`MainAppWindow`) MUST display the current status of the `AutonomyEngine` (e.g., "Inactive", "Active - Idle", "Assessing", "Awaiting Confirmation", "Executing").