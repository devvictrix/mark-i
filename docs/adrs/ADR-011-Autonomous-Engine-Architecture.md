# ADR-011: Architecture for the Autonomous Assistant Engine

- **Status:** Approved
- **Date Decision Made:** 2025-08-30
- **Deciders:** DevLead

## Context and Problem Statement

Mark-I has evolved into a powerful AI-assisted tool that can execute user-defined automation profiles (v1-v3), interpret complex Natural Language commands within a rule (`gemini_perform_task` in v4), and assist in creating profiles from high-level goals (`AI Profile Creator` in v5).

The current operational paradigm is still fundamentally reactive: Mark-I acts when a user explicitly runs a profile or initiates profile creation. The strategic vision for v6.0.0 is to evolve Mark-I into a proactive, **Autonomous Assistant**. This requires a new "meta-controller" or engine that can:

1.  Continuously and holistically observe the screen context without being limited to pre-defined regions.
2.  Proactively identify potential tasks, goals, or actionable situations based on this general observation.
3.  Dynamically generate and execute a plan to handle the identified situation, leveraging Mark-I's existing planning (`StrategyPlanner`) and execution (`GeminiDecisionModule`) capabilities.
4.  Operate independently of the profile-based `MainController` loop.
5.  Include robust safety mechanisms, such as requiring user confirmation before executing autonomously-derived plans.

We need to decide on the core architecture for this new "Autonomy Engine".

## Considered Options

1.  **Extend `MainController` with an "Autonomous Mode":**
    - **Description:** Modify the existing `MainController` and its monitoring loop. A special "autonomous" profile could trigger a different logic path within the loop that performs full-screen analysis and dynamic planning instead of evaluating a fixed rule set.
    - **Pros:** Reuses the existing `MainController` structure and threading model. Might seem simpler initially.
    - **Cons:** Tightly couples profile-driven execution with autonomous operation, violating the Single Responsibility Principle. `MainController` would become bloated and complex. The concepts of a fixed "monitoring interval" and "pre-defined regions" are less relevant to a continuous, holistic observer. State management for autonomous tasks would be messy within a profile-centric structure.

2.  **Create a Separate, High-Level `AutonomyEngine` Module (Chosen):**
    - **Description:** Implement a new, dedicated `AutonomyEngine` class in its own module (`mark_i.autonomy.engine`). This engine would run in its own thread, completely separate from the `MainController`.
      - Its core loop would be: Observe (capture full screen) -> Assess (use Gemini for high-level scene understanding and task identification) -> Plan (if a task is identified, use `StrategyPlanner`) -> Execute (use `GeminiDecisionModule` to carry out the dynamic plan, with a safety confirmation layer).
    - **Pros:** Clean separation of concerns between reactive, profile-based automation and proactive, autonomous assistance. Allows for a tailored lifecycle and state management specific to autonomous tasks. Highly modular, leveraging existing engines as tools (`StrategyPlanner`, `GeminiDecisionModule`) without modifying them extensively. More scalable and maintainable.
    - **Cons:** Requires a new top-level class and threading management. Introduces a new primary operational mode for the application to manage.

3.  **Integrate a Full External Agent Framework (e.g., LangChain, AutoGPT concepts):**
    - **Description:** Re-architect Mark-I to be a tool within a larger, third-party agentic framework. The external framework would handle the core loop of observation, thought, and action, calling Mark-I's capture and action capabilities as needed.
    - **Pros:** Potentially leverages powerful, pre-built agent logic for planning and memory.
    - **Cons:** Introduces heavy, complex external dependencies that may not be tailored for visual desktop automation. Drastically changes the project's architecture and increases its footprint. Loses the benefit of our custom-built, lightweight, and tightly integrated engine stack. Overkill for the defined scope of v6.0.0.

## Decision Outcome

**Chosen Option:** **Option 2: Create a Separate, High-Level `AutonomyEngine` Module.**

**Justification:**

This option provides the clearest and most robust path forward, aligning with Mark-I's established principles of modularity and separation of concerns.

-   **Maintainability & Scalability:** A dedicated `AutonomyEngine` keeps the logic for proactive assistance cleanly separated from the existing, stable logic for reactive profile execution in `MainController`. This makes both systems easier to understand, debug, and extend independently.
-   **Leverages Existing Strengths:** This approach perfectly reuses our battle-tested v4/v5 engines as components. The `AutonomyEngine` becomes an intelligent orchestrator that uses `GeminiAnalyzer` for scene assessment, `StrategyPlanner` for dynamic planning, and `GeminiDecisionModule` for plan execution. This maximizes code reuse and builds on a solid foundation.
-   **Appropriate Complexity:** It introduces the necessary components for autonomy without the massive overhead and potential architectural mismatch of integrating a generic external agent framework.
-   **Clear Execution Model:** Having two distinct, user-selectable modes—"Run Profile" (using `MainController`) and "Start Autonomous Assistant" (using `AutonomyEngine`)—provides a clear and understandable user experience.

## High-Level Implementation Plan

1.  **Create `mark_i/autonomy/engine.py`:** This will house the new `AutonomyEngine` class.
2.  **Implement `AutonomyEngine` Core Loop:**
    - It will run in a `threading.Thread`.
    - A `_stop_event` will be used for graceful shutdown.
    - The loop will consist of `_observe()`, `_assess()`, `_plan()`, and `_execute()` phases.
3.  **`_observe()` Phase:** Use `CaptureEngine` to take a snapshot of the full screen.
4.  **`_assess()` Phase:** Use `GeminiAnalyzer` with a specialized prompt to analyze the screenshot. The prompt will ask Gemini to describe the scene, identify the user's likely current goal, and suggest any potential tasks that Mark-I could assist with (e.g., "It looks like a file download has completed. A potential task is to move it to the Desktop.").
5.  **`_plan()` Phase:** If the assessment identifies a high-confidence task, the `AutonomyEngine` will feed a derived goal (e.g., "Move the recently downloaded file to the Desktop") to the existing `StrategyPlanner` to generate an intermediate plan.
6.  **`_execute()` Phase:**
    - **Safety First:** Before execution, the plan will be presented to the user in a simple, non-intrusive GUI prompt (e.g., "MARK-I proposes to: [Show Plan]. Allow / Deny?").
    - If allowed, the `AutonomyEngine` will pass the plan (as a natural language command or structured steps) to the `GeminiDecisionModule` for execution, similar to how the `gemini_perform_task` action works.
7.  **GUI Integration:** The `MainAppWindow` will be updated with a new control (e.g., a "Start Assistant" button) to instantiate and start the `AutonomyEngine`.

## Consequences

-   A new package, `mark_i.autonomy`, will be created.
-   The `AutonomyEngine` will become a new primary entry point for bot functionality, alongside `MainController`.
-   The project's AI capabilities will shift from being purely reactive tools to include a proactive assistance layer.
-   Significant prompt engineering will be required for the `_assess()` phase to reliably identify tasks from raw screen captures.
-   A new, simple, and robust GUI component for the user confirmation/safety layer must be designed and built.
-   The overall complexity of the application will increase, but in a structured and modular way.