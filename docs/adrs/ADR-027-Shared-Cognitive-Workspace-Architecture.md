# ADR-027: Shared Cognitive Workspace Architecture

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

With a BCI providing a high-speed data link, we need a formal structure to represent the shared mental "space" where the user and AI can collaborate on ideas. A simple text log or key-value store is insufficient to model the complex, non-linear nature of thought.

## Decision Outcome

**Chosen Option:** A new **`SharedCognitiveWorkspace`** class will be implemented. This class will manage an in-memory **graph database** (e.g., using a library like `networkx`).

**Justification:**

A graph is the ideal data structure for representing a mental model.

-   **Nodes** can represent concepts, ideas, memories, or data points.
-   **Edges** can represent the relationships between them (e.g., "is a cause of," "is an example of," "is a counter-argument to").

The `AgencyCore` will be responsible for managing this workspace. When the user "thinks" a new idea, the `BCIEngine` will signal the `AgencyCore` to add a new node to the graph. The AI can then autonomously explore connections, add related data nodes, and structure the graph, effectively organizing the user's thoughts in real-time. This provides the foundational structure for Synergistic Problem Solving.
