# ADR-023: Proactive Agency Core Architecture

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The `AgentCore` is a powerful *reactive* executor. It brilliantly executes tasks that are given to it. However, it lacks any form of internal motivation or proactivity. It will never act unless explicitly commanded by the user.

To become a true assistant, the AI needs to be able to generate its own goals based on a continuous understanding of the user's context and a set of intrinsic objectives.

## Considered Options

1.  **Overload the `AgentCore` with Proactive Logic:**
    - **Description:** Modify the `AgentCore`'s main prompt and logic. In addition to executing a given goal, it would also be asked to look for new task opportunities.
    - **Pros:** Reuses the existing class.
    - **Cons:** Creates a confusing cognitive model where the AI is trying to do two things at once: reactively execute a specific command and proactively look for new work. This would lead to convoluted prompts and unreliable behavior.

2.  **Implement a Hierarchical `AgencyCore` Orchestrator (Chosen):**
    - **Description:** Create a new, top-level AI orchestrator, the `AgencyCore`. This core does not execute low-level actions. Its job is to "think" at a strategic level. It will:
      1.  Consume the continuous context stream from the `PerceptionEngine`.
      2.  Operate on its own loop, driven by a set of high-level **"Core Directives"** (e.g., "Optimize user workflow," "Anticipate needs").
      3.  When its reasoning identifies a situation where it can act, its output is not a low-level tool command, but a high-level **task goal** (e.g., "Automate the weekly report generation I just observed").
      4.  This generated goal is then passed to the existing `AgentCore` for tactical execution.
    - **Pros:**
        -   **Creates a Clear Cognitive Hierarchy:** Mimics higher-order thinking. The `AgencyCore` is the strategist; the `AgentCore` is the tactician.
        -   **Clean Separation of Concerns:** Proactive goal generation is cleanly separated from reactive goal execution.
        -   **Powerful and Scalable:** The Core Directives can be refined over time to make the AI's proactive behavior more sophisticated, without ever touching the robust `AgentCore` execution logic.
    - **Cons:** Introduces a new top-level class, adding another layer to the AI's architecture.

## Decision Outcome

**Chosen Option:** **Option 2: Implement a Hierarchical `AgencyCore` Orchestrator.**

**Justification:**

This hierarchical model is the correct way to implement true agency. It allows the AI to operate on two distinct cognitive levels: a slow, deliberate, strategic level (`AgencyCore`) that decides *what* needs to be done, and a fast, tactical level (`AgentCore`) that determines *how* to do it. This is a powerful, scalable, and maintainable architecture for a proactive agent.

## High-Level Implementation Plan

1.  **Create `mark_i/agency/agency_core.py`:** This will house the new `AgencyCore` class.
2.  **Define the Core Directives Prompt:** A new, high-level prompt will be created that defines the AI's intrinsic purpose.
3.  **Implement the Proactive Loop:** The `AgencyCore` will have its own `start()`/`stop()` lifecycle. Its main loop will continuously get the latest context from the `PerceptionEngine`, inject it into the Core Directives prompt, and query an LLM to see if any self-generated tasks are warranted.
4.  **Integrate with `AgentCore`:** If the `AgencyCore` generates a task, it will present it to the user for confirmation (via a GUI callback) and, if approved, will invoke `agent_core.execute_goal()` to carry out the task.
