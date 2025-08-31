# ADR-030: Perceptual Filtering via Knowledge Base

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The `AgentCore`'s perception, driven by its Entity-Graph `WorldModel`, is powerful but indiscriminate. It attempts to identify _every_ UI element on the screen. This can be problematic when the screen contains persistent but irrelevant elements (e.g., desktop widgets, a floating video player, a taskbar clock). This "visual noise" clutters the AI's reasoning prompt and creates opportunities for distraction and error.

We need a way for the user to teach the AI what to ignore, thereby clarifying its perception.

## Decision Outcome

**Chosen Option:** A new **"perceptual filter"** system will be implemented, managed by the `KnowledgeBase`.

- A new top-level key, `perceptual_filters`, will be added to `knowledge_base.json`. This will contain an `ignore_list` of textual descriptions of elements the AI should disregard.
- The prompt for the `WorldModel`'s entity-graph update will be modified to include this ignore list, instructing the AI to exclude any matching elements from its analysis.
- The `KnowledgeCuratorWindow` GUI will be updated to allow users to easily add discovered elements to this ignore list.

**Justification:**

- **User-Driven and Persistent:** This solution empowers the user to permanently customize the AI's perception, making it more effective in their specific environment.
- **Leverages Existing Systems:** It builds directly upon the `KnowledgeBase` (memory) and `KnowledgeDiscoveryEngine` (learning) systems, creating a cohesive and integrated feature.
- **Improves AI Focus:** By removing irrelevant data at the earliest stage (perception), we reduce the cognitive load on the main reasoning LLM calls, which can improve both the speed and quality of its "Thought" process.

## High-Level Implementation Plan

1.  **Update `knowledge_base.json` Schema:** Add the `perceptual_filters` key with an empty `ignore_list`.
2.  **Update `KnowledgeBase` Class:** Add new methods (`add_to_ignore_list`, `get_ignore_list`) to manage the filter list.
3.  **Update `AgentCore` Prompt:** The prompt that drives the `world_model.update_entities` call will be modified to accept and use the `ignore_list` from the `KnowledgeBase`.
4.  **Update `KnowledgeCuratorWindow` GUI:** A new button or checkbox will be added to the curator dialog, allowing a user to mark a discovered knowledge candidate as "Ignored" instead of saving it as a named entity.

---

### **Phase 2: Implementation**

I will now implement the required changes across the codebase, starting with the documentation and configuration updates.
