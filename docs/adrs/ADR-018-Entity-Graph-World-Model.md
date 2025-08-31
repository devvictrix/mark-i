# ADR-018: Evolving the WorldModel to an Entity-Graph Structure

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The v11 "Cognitive Core" uses a `WorldModel` that stores a running text transcript of (Thought, Action, Observation). The agent's understanding of the screen is based on a flat screenshot, which it must re-analyze from scratch at every step. This has two key limitations:

1.  **Lack of Object Permanence:** The agent has no memory of an object from one step to the next. If a button is visible in two consecutive frames, the agent treats it as a completely new discovery each time.
2.  **Inefficient Reasoning:** The AI's prompt is burdened with re-describing the entire visual scene in its "Thought" process. It cannot reason about objects directly (e.g., "the value of the 'Username' text field" or "the button to the right of the 'Cancel' button").

To achieve a deeper, more efficient form of reasoning (sentience), the agent needs a structured, persistent internal representation of the screen's contents.

## Considered Options

1.  **Continue with Transcript-Based WorldModel:**
    - **Description:** Keep the current v11 `WorldModel`. All world understanding remains implicit in the AI's "Thought" process based on raw pixels.
    - **Pros:** No architectural changes required. Simple.
    - **Cons:** Fails to address the stated problems. Places a massive cognitive load on the LLM for every step and prevents more sophisticated reasoning about UI elements and their relationships. This is an intelligence ceiling.

2.  **Implement an Entity-Graph World Model (Chosen):**
    - **Description:** Evolve the `WorldModel`. In addition to the history transcript, it will now maintain a structured list (or graph) of **"Entities"** perceived on the screen.
      - At the beginning of each ReAct loop, a dedicated AI call (`world_model_update`) will analyze the screenshot and output a structured list of all visible UI elements (buttons, text fields, icons, windows, etc.), including their bounding boxes, labels, states (e.g., "disabled," "checked"), and values.
      - The `AgentCore`'s "Thought" process will then reason about this structured list of entities, not just the raw image.
    - **Pros:**
        -   **Creates Structured Understanding:** Transforms the AI's perception from "a collection of pixels" to "a window containing a login button and a text field."
        -   **Enables Sophisticated Reasoning:** The AI can now form thoughts like, "The `login_button` is currently `disabled`. I must first fill the `username_field` and `password_field` to enable it."
        -   **Increases Efficiency:** The main reasoning prompt no longer needs to waste tokens describing what's on screen; it can simply refer to the pre-processed list of entities.
        -   Provides a foundation for object permanence and tracking elements across screen changes.
    - **Cons:** Adds an extra AI call at the beginning of each loop to update the entity graph, potentially increasing latency. Requires significant new prompting and parsing logic.

3.  **Use Traditional Computer Vision for Entity Detection:**
    - **Description:** Instead of an AI call, use traditional CV techniques (e.g., edge detection, contour finding, OCR) to try and identify UI elements.
    - **Pros:** Potentially faster and cheaper than an LLM call.
    - **Cons:** Extremely brittle and unreliable. Traditional CV struggles with the vast diversity of UI designs, themes, and custom widgets. It cannot provide the semantic understanding (e.g., knowing that an icon of a floppy disk means "Save") that an LLM can. This approach is a step backward from the project's AI-first philosophy.

## Decision Outcome

**Chosen Option:** **Option 2: Implement an Entity-Graph World Model.**

**Justification:**

This is the most powerful and logical next step to elevate MARK-I's intelligence. By giving the agent a structured, real-time "mental map" of the screen, we fundamentally upgrade its ability to reason.

-   **Unlocks Deeper Context:** The agent can understand not just *what* is on the screen, but how the elements relate to each other and what state they are in.
-   **Focuses the AI's Reasoning:** The main ReAct prompt becomes much more efficient. The agent's "Thought" can be focused on strategy and what to do *with* the elements, rather than first having to identify them from scratch.
-   **Foundation for Sentience:** This is the absolute prerequisite for the more advanced features of the Sentience Core, like the Intentional Core and Executive Function. An agent cannot form complex intentions without a structured understanding of its world.

## High-Level Implementation Plan (v12.0.0)

1.  **Design the `world_model_update` Prompt:** Create a new, highly-specialized prompt that instructs the LLM to act as a UI parser, taking a screenshot and returning a structured JSON list of all perceived UI entities.
2.  **Evolve the `WorldModel` Class:** Add a new attribute, `self.entities`, to the `WorldModel` class. Create a new method, `update_entities(screenshot)`, which will use the `GeminiAnalyzer` and the new prompt to populate `self.entities`.
3.  **Update the `AgentCore` Loop:** The ReAct loop in `AgentCore` will be modified. The very first action of every step will now be to call `world_model.update_entities(observation_image)`.
4.  **Update the Main ReAct Prompt:** The main prompt will be updated to instruct the AI to use the now-populated entity list from the `WorldModel` as its primary source of world knowledge for its "Thought" process.

## Consequences

-   The `WorldModel` becomes a much more complex and central component.
-   Each ReAct step will now incur the cost and latency of two LLM calls: one for entity detection, and one for reasoning/action. This is an accepted trade-off for the massive increase in reasoning quality.
-   The success of this architecture will depend heavily on the quality and reliability of the new `world_model_update` prompt.
-   This successfully lays the groundwork for the agent to reason about the world in a way that approaches human-level contextual understanding.