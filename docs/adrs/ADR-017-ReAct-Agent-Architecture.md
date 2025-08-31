# ADR-017: ReAct Agent Architecture for the Cognitive Core

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The v10 "J.A.R.V.I.S. Core" with its Objective-Strategy-Tactic (OST) pattern is highly effective for automating tasks for which a complete plan can be generated upfront. The `StrategicExecutor` excels at creating a multi-step strategy and following it, even performing self-correction if a single step fails.

However, this architecture has a fundamental limitation: the plan is static. It is generated once at the beginning of a task. The AI's intelligence is front-loaded into the planning phase. It cannot dynamically adapt its high-level strategy to unexpected changes in the middle of a task, beyond the rigid self-correction loop. For complex, long-running tasks where the state of the desktop can change unpredictably, this model is not sufficiently adaptive or intelligent.

To achieve a higher level of cognitive function, we need to transition from a "plan-and-execute" model to a continuous "think-and-act" loop.

## Considered Options

1.  **Enhance the Existing OST Self-Correction Loop:**
    - **Description:** Keep the `StrategicExecutor` but make its self-correction logic more powerful, perhaps allowing it to re-plan more than just the immediate next step.
    - **Pros:** Builds on the stable v10 codebase. Less disruptive architecturally.
    - **Cons:** Fails to address the core problem. It remains a reactive, exception-handling mechanism rather than a proactive, continuous reasoning process. It's an incremental improvement that doesn't unlock true dynamic intelligence.

2.  **Adopt the ReAct (Reason + Act) Pattern (Chosen):**
    - **Description:** Re-architect the core AI into a ReAct agent. Instead of generating a full plan, the AI will operate in a continuous loop for each task:
      1.  **Reason (Thought):** Given the goal and the current screen (Observation), the AI generates a "Thought" - an internal monologue about its analysis of the situation and what it should do *next*.
      2.  **Act (Tool Use):** Based on its Thought, it selects a single Tool from a pre-defined `Toolbelt` (e.g., `click`, `type_text`) and specifies the parameters for that tool.
      3.  **Observe:** The tool is executed, and the AI captures a new screenshot to get a new Observation of the result. This observation is then fed back into the next Reason step.
    - **Pros:**
        -   **Highly Adaptive:** The AI makes a new, context-aware decision at every single step. It can handle unexpected events naturally as part of its loop.
        -   **Transparent Reasoning:** The "Thought" process can be logged, giving unprecedented insight into the AI's "mind."
        -   **Extensible:** The `Toolbelt` concept makes it incredibly easy to add new capabilities (e.g., `search_web`, `read_file`) without changing the core reasoning loop.
        -   This is the state-of-the-art architecture for building powerful, generalist agents.
    - **Cons:** Requires a significant refactoring of the `StrategicExecutor` into a new `AgentCore`. It is more "chatty" with the LLM, potentially increasing latency and cost for very simple tasks (a trade-off for greater power on complex ones).

3.  **Integrate an External Agent Framework (e.g., LangChain):**
    - **Description:** Rebuild MARK-I on top of a third-party agent framework, using our visual tools as the custom components.
    - **Pros:** Leverages a pre-built, powerful agent engine.
    - **Cons:** Introduces a massive, heavy dependency. We lose the fine-grained control we have over our custom-built core. It can be complex to integrate our specific visual-first tooling into a generic text-first framework. This is over-engineering and sacrifices the lightweight, bespoke nature of the project.

## Decision Outcome

**Chosen Option:** **Option 2: Adopt the ReAct (Reason + Act) Pattern.**

**Justification:**

The ReAct pattern is the logical and necessary evolution for MARK-I to transcend its current limitations and become a truly intelligent agent. It directly addresses the problem of static planning by making reasoning a continuous, dynamic process.

-   **Unlocks True Adaptability:** This architecture allows the AI to handle complex, multi-stage tasks where the environment can change at any moment. It stops being a script-follower and starts being a problem-solver.
-   **Increases Intelligence & Power:** By forcing the AI to reason about its actions step-by-step, we unlock a more sophisticated and robust form of intelligence. The ability to add new tools to its `Toolbelt` provides a clear path for exponential growth in its capabilities.
-   **Architectural Clarity:** The concepts of an `AgentCore` (the brain), a `WorldModel` (short-term memory), and a `Toolbelt` (its hands) create a clean, maintainable, and highly advanced architecture that aligns with cutting-edge AI research.

This decision moves MARK-I from its "J.A.R.V.I.S. Core" to the even more powerful **"Cognitive Core."**

## High-Level Implementation Plan (v11.0.0)

1.  **Refactor Primitives into a `Toolbelt`:** The existing `PrimitiveExecutors` will be restructured into a formal `Toolbelt` class. Each tool will have a clear name, description, and parameter schema that the AI can reason about.
2.  **Implement the `WorldModel`:** A new class will be created to manage the agent's "scratchpad" for a given task. It will store the running list of (Thought, Action, Observation) triplets.
3.  **Evolve `StrategicExecutor` to `AgentCore`:** The `StrategicExecutor` will be replaced by a new `AgentCore`. Its primary `execute_command` method will be re-implemented to run the ReAct loop:
    -   Construct a prompt containing the user's goal, the `Toolbelt` description, and the current `WorldModel` history.
    -   Call the LLM to generate the next `Thought` and `Action`.
    -   Parse the response, invoke the chosen tool from the `Toolbelt`.
    -   Capture the new visual `Observation`.
    -   Append the new (Thought, Action, Observation) to the `WorldModel`.
    -   Repeat until the AI's "Thought" concludes the task is finished.
4.  **Update GUI:** The `VisualLogPanel` will be enhanced to display not just the Action and Observation, but the AI's "Thought" process for each step.

## Consequences

-   The core logic of the application will be fundamentally changed from a planner to a step-by-step reasoner.
-   The `StrategicExecutor` will be deprecated and replaced by the `AgentCore`.
-   A new `Toolbelt` and `WorldModel` system will be created.
-   The nature of prompting the LLM will shift from a one-shot plan generation to an iterative, conversational interaction for each task.
-   This lays the foundation for all future advanced AI features, including the Sentience, God, and Genesis Cores.