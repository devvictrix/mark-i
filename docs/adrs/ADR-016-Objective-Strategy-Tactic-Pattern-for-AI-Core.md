# ADR-016: Objective-Strategy-Tactic (OST) Pattern for the AI Core

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The Mark-I project has successfully evolved through multiple stages, culminating in a powerful `StrategicExecutor` capable of dynamic, multi-step task execution from a single command. However, this executor is still fundamentally reactive and stateless in its planning phase; for every complex command, it generates a new strategic plan from scratch. This has several limitations:

1.  **Inefficiency:** Repeatedly solving the same problem (e.g., "log into the app") is computationally expensive and incurs unnecessary API costs and latency.
2.  **Lack of Learning:** The system does not learn from its successes or failures. A plan that fails due to a transient issue will be generated again, and a particularly effective plan is not remembered.
3.  **Implicit Logic:** The AI's "plans" are ephemeral artifacts of a single execution. There is no formal structure for saving, reviewing, or reusing this intelligence.

To transition Mark-I into a truly intelligent and self-improving assistant as per the `v10.0.0` vision, we need to move beyond ad-hoc planning and implement a concrete pattern for storing, reusing, and refining the AI's operational knowledge.

## Considered Options

1.  **Ad-Hoc Dynamic Planning (Current State):**
    - **Description:** Continue with the current `StrategicExecutor` model. For every command, it generates a new plan by querying the Gemini API.
    - **Pros:** Maximally flexible in the short term, as it always reacts to the immediate visual context.
    - **Cons:** Fails to address any of the problems of inefficiency, lack of learning, or reusability. It represents a performance and intelligence ceiling.

2.  **Formalized Objective-Strategy-Tactic (OST) Pattern (Chosen):**
    - **Description:** Implement a formal, hierarchical pattern for the AI's knowledge and behavior.
        -   **Objective:** A named, high-level user goal (e.g., "Send Daily Report").
        -   **Strategy:** A stored, reusable, versioned plan (a sequence of steps) that is known to achieve an Objective. An Objective can have multiple competing Strategies.
        -   **Tactic:** A single, executable step within a Strategy, delegated to the `GeminiDecisionModule`.
    - This pattern would be stored in and managed by an evolved `KnowledgeBase`. The `StrategicExecutor` would first try to use a stored Strategy before resorting to generating a new one.
    - **Pros:**
        -   **Enables Reusability & Efficiency:** Drastically reduces API calls and latency for known tasks.
        -   **Facilitates Learning:** By tracking metadata (e.g., `success_rate`) on Strategies and saving refined plans, the system can demonstrably improve over time.
        -   **Structured & Debuggable:** Makes the AI's "thought process" explicit and reviewable within the `knowledge_base.json`.
    - **Cons:** Adds complexity to the `StrategicExecutor` and `KnowledgeBase` to manage this new data structure.

3.  **External Behavior Tree Engine:**
    - **Description:** Integrate a third-party library for behavior trees to manage the AI's logic. Objectives and Strategies would be modeled as nodes and branches in the tree.
    - **Pros:** Behavior trees are a powerful and established pattern for complex AI logic.
    - **Cons:** Introduces a significant and potentially heavy external dependency. It would require a major re-architecture of the `StrategicExecutor` and would likely be over-engineering for the current scope. The OST pattern provides similar benefits with a more lightweight, custom implementation.

## Decision Outcome

**Chosen Option:** **Option 2: Formalized Objective-Strategy-Tactic (OST) Pattern.**

**Justification:**

The OST pattern is the most logical and efficient evolution for the Mark-I architecture. It directly addresses the current system's primary limitations and provides the necessary framework for the desired features of learning and self-correction.

-   **Efficiency and Reusability:** It avoids redundant planning, making the assistant faster and more cost-effective for recurring tasks.
-   **Structured Learning:** It provides a concrete data structure (`Strategy`) that can be measured, versioned, and refined. This moves "learning" from an abstract concept into a tangible engineering task.
-   **Architectural Cohesion:** It builds directly upon the existing strengths of the `StrategicExecutor` (strategic brain), `GeminiDecisionModule` (tactical expert), and `KnowledgeBase` (memory) without requiring a disruptive, ground-up rewrite.
-   **Balance:** It provides the power of a formal AI pattern without the excessive complexity or dependency risk of integrating a full external engine like a behavior tree.

## High-Level Implementation Plan & Consequences

### 1. Evolve the `knowledge_base.json` Schema

The `knowledge_base.json` file will be updated with a new top-level key, `"objectives"`. This will store the core data for the OST pattern.

**New Schema Example:**
```json
{
  "aliases": { ... },
  "user_data": { ... },
  "objectives": [
    {
      "objective_name": "Send Daily Report to Manager",
      "goal_prompt": "Open the sales dashboard, generate the daily report, and email it to my manager.",
      "strategies": [
        {
          "strategy_name": "Standard Report Strategy v2",
          "success_rate": 0.98,
          "last_used": "2025-08-31T12:10:46Z",
          "steps": [
            { "tactical_goal": "Click the 'OK' button on the update dialog." },
            { "tactical_goal": "Open Chrome and navigate to the sales dashboard." },
            { "tactical_goal": "Click the button labeled 'Generate Daily Report'." }
          ]
        }
      ]
    }
  ]
}