# ADR-028: Multiple Strategy Management and Contextual Selection

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The v14 `StrategicExecutor` and `KnowledgeBase` are powerful but have a key limitation in their learning model. When a new successful strategy is generated for an existing objective, it overwrites the previous strategy. This prevents the AI from retaining multiple valid methods to achieve the same goal.

An intelligent agent should be able to learn and store various strategies (e.g., using a hotkey vs. using the mouse via menus) and, more importantly, choose the most appropriate one based on the current visual context.

## Considered Options

1.  **Single Best Strategy (Current State):**
    - **Description:** Continue with the current model where only the most recent or highest-rated strategy is stored per objective.
    - **Pros:** Simple to manage.
    - **Cons:** Intellectually limiting. The AI cannot adapt its approach and loses valuable operational knowledge. It cannot choose a faster hotkey-based method when appropriate, for example.

2.  **Implement Multiple Strategy Storage and Contextual AI Selection (Chosen):**
    - **Description:**
      1.  **Modify `KnowledgeBase`:** The `save_strategy` method will be updated to append new, unique strategies to an objective's `strategies` list instead of overwriting. Logic will be added to manage this list (e.g., versioning similarly named strategies, pruning old/low-performing ones).
      2.  **Modify `StrategicExecutor`:** After matching a user command to an objective, the executor will retrieve *all* available strategies for it.
      3.  **Add a "Strategy Selection" Step:** Before execution, the `StrategicExecutor` will perform a new, lightweight AI call. It will provide the AI with the current screenshot and a summary of the available strategies, asking it to choose the most suitable one for the current visual context.
    - **Pros:**
        -   **Enables True Adaptability:** Allows the AI to choose the most efficient path based on the live UI state (e.g., choosing a hotkey when a menu is not visible).
        -   **Increases Resilience:** If one strategy starts failing (e.g., due to a UI update), the AI can fall back on other known, successful strategies.
        -   **Deepens AI Intelligence:** Moves the AI from simple plan recall to context-aware decision-making, a more sophisticated form of thought.
    - **Cons:** Adds one extra, lightweight AI call to the beginning of a task execution.

## Decision Outcome

**Chosen Option:** **Option 2: Implement Multiple Strategy Storage and Contextual AI Selection.**

**Justification:**

This is a critical evolution for the AI's learning and performance. Storing a single "best" plan is brittle and unrealistic for complex desktop environments where the optimal path can change based on the application's state. By giving the AI a library of potential solutions and the intelligence to choose among them contextually, we make it significantly more efficient, resilient, and intelligent. This aligns perfectly with the goal of creating a powerful and adaptive agent.