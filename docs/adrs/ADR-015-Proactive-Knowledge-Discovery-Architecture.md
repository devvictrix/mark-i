# ADR-015: Proactive Knowledge Discovery Architecture

- **Status:** Approved
- **Date Decision Made:** 2025-08-30
- **Deciders:** DevLead

## Context and Problem Statement

Mark-I v8.0.0 introduced a powerful `KnowledgeBase` that allows the `StrategicExecutor` to perform complex, personalized, multi-step tasks. However, this knowledge base (`knowledge_base.json`) is currently static and must be manually created and maintained by the user. This places a significant burden on the user to identify and catalog all the relevant aliases, application details, and UI element descriptions the AI might need.

To make Mark-I truly intelligent and easy to use, we need a mechanism for the AI to **proactively learn about the user's environment** and assist in populating its own Knowledge Base. This feature is the core of the v9.0.0 epic.

We need to decide on an architecture that enables this "Knowledge Discovery" process, including how the AI identifies potential knowledge, how it is presented to the user for confirmation, and how it is saved.

## Considered Options

1.  **A Separate, Dedicated "Learning Mode" (Chosen):**
    - **Description:** Introduce a new, distinct operational mode, separate from the `AutonomyEngine` and `InteractiveCommand`. In this "Knowledge Discovery Mode," a new `KnowledgeDiscoveryEngine` runs in the background. It periodically captures the screen and sends it to a powerful multimodal model with a prompt specifically designed for reconnaissance—identifying common UI elements, icons, logos, and labeled data fields. These "knowledge candidates" are then presented to the user through a new GUI for confirmation, editing, and saving into the `knowledge_base.json`.
    - **Pros:**
        -   **Clean Separation of Concerns:** Keeps the logic for "doing tasks" (`StrategicExecutor`, `AutonomyEngine`) separate from the logic for "learning about the environment" (`KnowledgeDiscoveryEngine`).
        -   **User in Control:** The user explicitly enables this mode and has the final say on every piece of knowledge that gets saved, preventing the AI from making incorrect assumptions.
        -   **Focused Prompting:** Allows us to create highly specialized prompts for knowledge extraction without complicating the prompts used for task execution.
    - **Cons:** Introduces another major component (`KnowledgeDiscoveryEngine`) and a new GUI element for managing the discovered knowledge.

2.  **Integrate Learning into the `AutonomyEngine`:**
    - **Description:** Overload the existing `AutonomyEngine` from v6. Instead of just looking for tasks, its assessment prompt would be modified to *also* look for new, unknown UI elements.
    - **Pros:** Reuses an existing component's lifecycle (the background thread).
    - **Cons:** Violates the Single Responsibility Principle. The `AutonomyEngine`'s goal is to find and execute tasks; mixing this with a continuous learning process makes its objective unclear and its logic much more complex. The prompts would become convoluted, trying to ask the AI to both "find a task" and "catalog everything interesting" at the same time, likely reducing the quality of both outputs.

3.  **Implicit Learning from `InteractiveCommand`:**
    - **Description:** After the `StrategicExecutor` successfully completes a command, have it analyze the steps it took and ask the user, "I noticed I had to find the 'LINE' icon to complete your last command. Would you like me to save this icon and its location to the Knowledge Base for faster use next time?"
    - **Pros:** Learning is directly tied to user intent and successful actions, making it highly relevant.
    - **Cons:** This is a much more passive and less comprehensive way of learning. It would only learn about things the user explicitly interacts with, missing opportunities to learn about the entire environment. It also adds significant complexity to the end of every command execution flow.

## Decision Outcome

**Chosen Option:** **Option 1: A Separate, Dedicated "Learning Mode"**.

**Justification:**

This architecture provides the most robust, maintainable, and user-friendly solution.

-   **Clarity of Purpose:** Having a dedicated `KnowledgeDiscoveryEngine` makes the system's states clear. Mark-I is either *executing* (via Interactive Command or a profile), *proactively assisting* (via the Autonomous Engine), or *actively learning* (via the Knowledge Discovery Engine). This separation prevents complex, unpredictable interactions between different AI goals.
-   **User Control & Trust:** A dedicated mode that the user turns on and off gives them complete control over the learning process. The confirmation step, where users approve every piece of learned knowledge, is critical for building trust and ensuring the accuracy of the Knowledge Base.
-   **Scalability:** This modular approach is the most scalable. The `KnowledgeDiscoveryEngine` can be refined and made more intelligent over time without impacting the core execution engines. The GUI for knowledge management can also evolve independently.

## High-Level Implementation Plan

1.  **Create `mark_i/knowledge/discovery_engine.py`:**
    -   Define the `KnowledgeDiscoveryEngine` class. It will have its own thread and a start/stop lifecycle, similar to the `AutonomyEngine`.
    -   Its core loop will be `Observe -> Analyze for Knowledge -> Propose to User`.

2.  **Develop the "Assess for Knowledge" Prompt:**
    -   Create a new, sophisticated prompt that instructs the AI to act as a reconnaissance agent, identifying and cataloging elements from a screenshot and returning them in a structured JSON format.

3.  **Create `mark_i/ui/gui/knowledge_curator_window.py`:**
    -   Develop a new GUI window that can take the "knowledge candidates" from the `KnowledgeDiscoveryEngine`.
    -   It will display each candidate (e.g., showing a cropped image of a discovered icon or the label of a discovered field) and provide an interface for the user to:
        -   Confirm or reject the finding.
        -   Provide or edit the name/alias (e.g., naming the Slack icon "work chat").
        -   Provide the value for data fields (e.g., entering their first name for a "First Name" field).
        -   Save the confirmed knowledge to `knowledge_base.json`.

4.  **Integrate into `AppController` and `MainAppWindow`:**
    -   Add a new "Start Learning" button to the main GUI to control the `KnowledgeDiscoveryEngine`.
    -   Add a "Manage Knowledge" button that opens the `KnowledgeCuratorWindow` to view/edit both discovered and manually entered knowledge.

## Consequences

-   A new major operational mode will be added to Mark-I, solidifying its position as a learning assistant.
-   The `KnowledgeBase` becomes a dynamic entity, co-created by the user and the AI.
-   This significantly lowers the barrier to entry for personalizing Mark-I, as users no longer need to manually author the entire knowledge base from scratch.
-   New classes (`KnowledgeDiscoveryEngine`, `KnowledgeCuratorWindow`) and a new, complex AI prompt will need to be developed and thoroughly tested.