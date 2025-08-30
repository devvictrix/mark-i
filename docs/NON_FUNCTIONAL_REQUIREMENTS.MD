# Non-Functional Requirements for Mark-I

This document outlines the non-functional requirements for the Mark-I visual automation tool, describing _how well_ the system should perform its functions, its qualities, and constraints.
**This version reflects requirements for v5.0.0 and incorporates new NFRs for v6.0.0: Autonomous Assistant.**

## NFR-PERF: Performance

- **NFR-PERF-001: Low Latency Capture (Bot Runtime):** (As is).
- **NFR-PERF-002: Efficient Analysis (Bot Runtime):** (As is).
- **NFR-PERF-003: Configurable Monitoring Interval (Bot Runtime):** (As is).
- **NFR-PERF-004: Minimal System Impact (Bot Runtime):** (As is).
- **NFR-PERF-005: Responsive GUI Profile Editor:** (As is).
- **NFR-PERF-006: Gemini Decision Module / NLU Task Latency (Runtime):** (As is).
- **NFR-PERF-007: AI Profile Generation Performance (v5.0.0):** (As is).
- **NFR-PERF-008: Autonomous Assistant Performance (v6.0.0):**
  - **Assessment Interval:** The `AutonomyEngine`'s observation/assessment loop SHOULD be configurable (e.g., 5-30 seconds) to balance responsiveness with system resource usage. The default should be non-intrusive (e.g., 10-15 seconds).
  - **Low Idle Impact:** When in its "Idle" state, the `AutonomyEngine`'s background thread SHOULD consume minimal CPU and memory resources.
  - **Assessment Latency:** The AI call for scene assessment (`_assess` phase) will have network latency. This is acceptable as it's a background task, but it should not block the main GUI thread.

## NFR-USAB: Usability

- **NFR-USAB-001 - NFR-USAB-013:** (Profile configuration, feedback, wizard usability, documentation - as is).
- **NFR-USAB-014: Autonomous Assistant Control (v6.0.0):** The main GUI (`MainAppWindow`) MUST provide simple and clear controls to start and stop the Autonomous Assistant. The user MUST be able to easily understand if the assistant is active or inactive.
- **NFR-USAB-015: Clear Confirmation Dialog (v6.0.0):** The `AutonomyConfirmationDialog` MUST be easy to understand. It MUST clearly and concisely display the proposed plan of action. The "Allow" and "Deny" buttons MUST be unambiguous.
- **NFR-USAB-016: Non-Intrusive Suggestions (v6.0.0):** The confirmation dialog SHOULD appear in a consistent screen location (e.g., center or corner) and should not steal focus in a disruptive way that interrupts typing. It is a suggestion, not a modal blocker.
- **NFR-USAB-017: Feedback on Autonomous Actions (v6.0.0):** The GUI's status indicator MUST provide real-time feedback on the `AutonomyEngine`'s state, so the user knows when it is observing, thinking, awaiting confirmation, or executing a task.

## NFR-ACCU: Accuracy

- **NFR-ACCU-001 - NFR-ACCU-005:** (Region capture, local/AI analysis, action execution, profile generation quality - as is).
- **NFR-ACCU-006: Autonomous Task Identification (v6.0.0):** The AI-driven assessment (`_assess` phase) SHOULD be accurate and conservative. It should have a low false-positive rate for identifying tasks to avoid proposing irrelevant or incorrect actions to the user. The confidence score mechanism MUST be used to filter out low-quality suggestions.

## NFR-REL: Reliability & Robustness (System-Wide)

- **NFR-REL-001 - NFR-REL-007:** (Stable operation, graceful error handling for runtime and profile generation - as is).
- **NFR-REL-008: Autonomous Engine Stability (v6.0.0):** The `AutonomyEngine`'s background thread MUST be stable and handle errors gracefully. An error during one assessment/planning cycle (e.g., a failed API call, unparseable AI response) MUST NOT crash the engine's loop. The engine should log the error and continue to the next cycle.
- **NFR-REL-009: Autonomous Confirmation Timeout (v6.0.0):** The confirmation dialog SHOULD have a timeout (e.g., 30-60 seconds), after which it automatically denies the proposal and disappears. This prevents stale suggestions from cluttering the screen.

## NFR-SEC: Security

- **NFR-SEC-001 - NFR-SEC-007:** (User control, data transmission, API keys, privacy, generated profiles - as is).
- **NFR-SEC-008: Explicit Consent for Autonomous Actions (v6.0.0):** The system MUST NOT perform any autonomously-derived action without explicit, real-time consent from the user for that specific plan. The "Allow" button in the confirmation dialog is the mechanism for this consent. There MUST NOT be an option to "always allow" actions, to prevent unintended behavior.

## NFR-CONF: Configurability

- **NFR-CONF-001 - NFR-CONF-009:** (Profile settings, AI generation params - as is).
- **NFR-CONF-010: Autonomous Assistant Settings (v6.0.0 - Future):** Future versions SHOULD allow users to configure the `AutonomyEngine`, for example, by setting the assessment interval, the confidence threshold for task suggestions, or creating "do not disturb" rules for certain applications. For the initial v6.0.0 release, reasonable defaults will be used.