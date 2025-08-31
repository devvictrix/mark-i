
# Non-Functional Requirements for Mark-I

This document outlines the non-functional requirements for the Mark-I visual automation tool, describing _how well_ the system should perform its functions, its qualities, and constraints.
**This version reflects requirements for v6.0.0 and incorporates new NFRs for v7.0.0: Interactive Command Mode.**

## NFR-PERF: Performance

- **NFR-PERF-001 - NFR-PERF-007:** (Capture, local analysis, GUI editor, AI profile generation performance - as is).
- **NFR-PERF-008: Autonomous Assistant Performance (v6.0.0):** (As is - low idle impact, acceptable background latency).
- **NFR-PERF-009: Interactive Command Latency (v7.0.0):**
  - The execution of an interactive command WILL have noticeable latency due to multiple sequential AI API calls made by the `GeminiDecisionModule`. This is an accepted trade-off for its power and flexibility.
  - The system's GUI MUST remain fully responsive during this latency.
  - The user MUST be kept informed of the progress via real-time status updates in the GUI.

## NFR-USAB: Usability

- **NFR-USAB-001 - NFR-USAB-017:** (Profile configuration, wizards, Autonomous Assistant controls and feedback - as is).
- **NFR-USAB-018: Interactive Command Interface (v7.0.0):** The command bar in the main GUI MUST be intuitive and easy to use. The "Execute" button and status label must be clearly associated with the command input field.
- **NFR-USAB-019: Clarity of Command Execution (v7.0.0):** The real-time status feedback for interactive commands MUST be clear and concise, providing the user with confidence that the system is working or informing them of any errors.

## NFR-ACCU: Accuracy

- **NFR-ACCU-001 - NFR-ACCU-006:** (Capture, analysis, profile generation, autonomous identification accuracy - as is).

## NFR-REL: Reliability & Robustness (System-Wide)

- **NFR-REL-001 - NFR-REL-009:** (Stable operation, error handling for runtime, profile generation, autonomy - as is).
- **NFR-REL-010: Interactive Command Robustness (v7.0.0):** The interactive command execution thread MUST handle errors gracefully (e.g., failed screen capture, API errors, AI failing to parse the command). Such errors MUST be reported to the user via the GUI status label and MUST NOT crash the main application. The command bar MUST re-enable itself after a task finishes, whether in success or failure.

## NFR-SEC: Security

- **NFR-SEC-001 - NFR-SEC-008:** (User control, data transmission, API keys, privacy, explicit consent for autonomous actions - as is).
- **NFR-SEC-009: User Responsibility for Interactive Commands (v7.0.0):** The user is in direct control and fully responsible for the commands they issue for immediate execution. Since there is no pre-vetted profile, the user must ensure their commands will not perform undesirable actions.

## NFR-CONF: Configurability

- **NFR-CONF-001 - NFR-CONF-010:** (Profile settings, AI generation, autonomy settings - as is).