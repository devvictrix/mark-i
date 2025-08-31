
# Functional Requirements for Mark-I

This document outlines the functional requirements for the Mark-I visual automation tool, describing _what_ the system will do.
**This version reflects the completed capabilities of v6.0.0 and incorporates the new requirements for v7.0.0: Interactive Command Mode.**

## FR-CORE: Core System

- **FR-CORE-001: Cross-Platform Operation:** The bot's core runtime engine and GUI editor SHOULD operate on Windows, macOS, and Linux. (Primary development and testing on Windows).
- **FR-CORE-002: Configuration Files (JSON):** The system MUST use JSON for saving and loading bot configurations (profiles).
- **FR-CORE-003: Environment Configuration:** The system MUST read environment variables (e.g., from `.env` file via `python-dotenv`) for `APP_ENV` (influencing logging) and sensitive data like `GEMINI_API_KEY`.
- **FR-CORE-004: Logging:** The system MUST implement comprehensive, persistent, and configurable logging for all significant operations.

## FR-CAPTURE: Screen Region Capture Module

- **FR-CAPTURE-001: Define Target Region (Manual & AI-Assisted):** The user MUST be able to define specific, named rectangular regions on the screen for use in profiles.
- **FR-CAPTURE-002: Capture Specified Region (Runtime):** The system MUST capture image data from defined regions during profile-based bot runtime.
- **FR-CAPTURE-003: Real-time Capture (Runtime):** The system MUST support continuous real-time capture at a user-configurable interval for profile-based execution.
- **FR-CAPTURE-004: Full Screen/Window Capture:** The system MUST be able to capture the entire screen or a specified application window. This is used for context in AI Profile Generation (v5), the Observe phase of the Autonomous Assistant (v6), and for Interactive Command Mode (v7).
- **FR-CAPTURE-005: Screen Dimension Detection:** The system (via `CaptureEngine`) MUST be able to programmatically determine the dimensions of the primary display.

## FR-ANALYZE: Region Analysis & AI Understanding Module

- **FR-ANALYZE-001 - FR-ANALYZE-012:** (Local analysis, profile-based AI analysis, profile generation AI - as is).

## FR-ACTION: Action Execution & Task Orchestration Module

- **FR-ACTION-001 - FR-ACTION-010:** (Primitive actions, `gemini_perform_task` execution, profile generation assembly - as is).

## FR-CONFIG: Configuration & Management

- **FR-CONFIG-001 - FR-CONFIG-009:** (Profile I/O, variable capture, AI Profile Generation workflow - as is).

## FR-UI: User Interface

- **FR-UI-001 - FR-UI-008:** (CLI, `MainAppWindow`, `ProfileCreationWizardWindow`, and helper windows - as is).

## FR-AUTONOMY: Autonomous Assistant (v6.0.0)

- **FR-AUTONOMY-001 - FR-AUTONOMY-009:** (Independent operation, Observe/Assess/Plan/Execute loop, safety confirmation, GUI controls - as is).

## FR-INTERACTIVE: Interactive Command Mode (v7.0.0)

- **FR-INTERACTIVE-001: Command Input:** The main GUI (`MainAppWindow`) MUST provide a text input field (command bar) where the user can type a natural language command.
- **FR-INTERACTIVE-002: Command Execution Trigger:** The GUI MUST provide a button to trigger the execution of the command in the command bar. Pressing "Enter" in the input field SHOULD also trigger execution.
- **FR-INTERACTIVE-003: On-Demand Context Capture:** Upon triggering command execution, the system MUST capture an image of the current full screen to use as visual context.
- **FR-INTERACTIVE-004: Direct Task Execution:** The system MUST pass the user's text command and the captured screen image directly to the `GeminiDecisionModule` to be parsed and executed.
- **FR-INTERACTIVE-005: Background Execution:** The entire interactive command task (capture, AI processing, action execution) MUST run in a background thread to keep the main GUI responsive.
- **FR-INTERACTIVE-006: Real-time Feedback:** The GUI MUST display real-time status updates to the user throughout the command execution lifecycle (e.g., "Capturing...", "Executing with AI...", "Task complete", "Error: ...").