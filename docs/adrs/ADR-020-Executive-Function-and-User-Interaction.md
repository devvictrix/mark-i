# ADR-020: Executive Function with Confidence Scoring and an Interactive `ask_user` Tool

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The v12 agent, with its Entity-Graph and Intentional Core, can now form sophisticated, multi-stage plans. However, its execution is still entirely autonomous within each ReAct step. If the AI's "Thought" process generates an action based on ambiguous visual information (e.g., multiple buttons are labeled "Submit") or an incomplete understanding of the user's intent (e.g., the user says "email the team" but the team members are not defined in the `KnowledgeBase`), the agent is forced to make a guess. This guess is often wrong, leading to task failure and eroding user trust.

To achieve true sentience and become a reliable partner, the agent needs two things:
1.  The ability to assess its own uncertainty (metacognition).
2.  A direct channel to resolve that uncertainty by communicating with the user *mid-task*.

## Considered Options

1.  **Implicit Failure Detection (Current State):**
    - **Description:** Rely on the existing `finish_intention` mechanism. The agent makes its best guess. If the action fails to produce the expected outcome, the user goal fails, and the user must start over with a more specific command.
    - **Pros:** No new components needed.
    - **Cons:** Inefficient and frustrating for the user. It puts the entire burden of ambiguity resolution on the user by forcing them to craft perfectly precise initial prompts. It is not a characteristic of an intelligent assistant.

2.  **Implement an Executive Function and an `ask_user` Tool (Chosen):**
    - **Description:** This approach introduces two new interconnected components to the `AgentCore`.
      1.  **Executive Function:** After the LLM generates a "Thought" and a proposed "Action," this new function within the `AgentCore` analyzes the response. It uses another, highly-focused LLM call to evaluate the clarity of the thought and the certainty of the action. This call will output a **confidence score** (0.0 to 1.0).
      2.  **`ask_user` Tool:** A new, first-class tool is added to the `Toolbelt`. When invoked, this tool will display a modal GUI dialog to the user, presenting the AI's question and providing a text box for the user's response. The user's typed response becomes the "Observation" for the next ReAct loop.
      3.  **Decision Logic:** The `AgentCore`'s main loop is modified. If the Executive Function's confidence score for a proposed action is above a certain threshold (e.g., 0.85), it executes the action normally. If the score is *below* the threshold, it **discards the proposed action** and instead invokes the `ask_user` tool with a question derived from its uncertain "Thought."
    - **Pros:**
        -   **Creates a Truly Interactive Dialogue:** Transforms the agent from a silent executor into a collaborative partner that can ask for help.
        -   **Dramatically Improves Robustness:** Prevents the agent from making low-confidence guesses that would lead to task failure.
        -   **Builds User Trust:** The agent demonstrates self-awareness of its own limitations, which is a key component of intelligence and makes it more trustworthy.
    - **Cons:** Introduces another LLM call per step for confidence scoring, further increasing latency. Requires a new GUI component for the user interaction dialog.

3.  **Always Confirm Every Action:**
    - **Description:** Before every single action (`click`, `type`, etc.), show a confirmation dialog to the user.
    - **Pros:** Maximally safe.
    - **Cons:** Unbearably tedious for the user. It destroys the efficiency and autonomy that the agent is supposed to provide, turning it into a "Mother, may I?" system.

## Decision Outcomemark_i\ui\gui\app_controller.py

**Chosen Option:** **Option 2: Implement an Executive Function and an `ask_user` Tool.**
mark_i\ui\gui\app_controller.py
**Justification:**

This is the only option that grants the agent the critical missing piece of intelligence: the ability to know what it doesn't know. The combination of self-assessed confidence and a direct line of communication to the user is the cornerstone of a truly sentient and useful assistant.

-   **Solves the Ambiguity Problem:** It provides a concrete mechanism for resolving uncertainty, making the agent far more likely to succeed at complex tasks in unpredictable environments.
-   **Balances Autonomy and Collaboration:** The confidence threshold allows the agent to act autonomously on high-certainty steps while intelligently pausing to collaborate with the user when faced with ambiguity. This is the optimal workflow.
-   **Completes the Cognitive Model:** This adds the final layer to the Sentience Core, equipping it with Perception (Entity-Graph), Planning (Intentional Core), and now Metacognition/Communication (Executive Function).

## High-Level Implementation Plan (v12.0.0)

1.  **Create the `ask_user` Tool:**
    -   Implement a new `AskUserTool` class in the `agent.tools` package.
    -   Its `execute` method will trigger a callback to the `AppController` to display a new `UserInputDialog`.
    -   It will use a `threading.Event` to block and wait for the user's text input from the dialog. The returned text will be its "Observation."
2.  **Design the `UserInputDialog` GUI:** Create a new, simple modal Toplevel window that displays the AI's question and has a text entry field and an "OK" button.
3.  **Implement the Executive Function:**
    -   Design a new "confidence scoring" prompt that takes the agent's "Thought" and proposed "Action" and asks the LLM to rate its confidence.
    -   In the `AgentCore`'s main loop, after the ReAct prompt returns a thought/action, make a second call using this new prompt to get the confidence score.
4.  **Update the `AgentCore` Loop:** Add the decision logic: `if confidence > threshold: execute_tool() else: execute_ask_user_tool()`.

## Consequences

-   The agent's autonomy will be greatly enhanced, as it can now navigate situations that would have previously caused it to fail.
-   The user experience will become truly conversational for complex tasks.
-   Overall task latency will increase due to the additional confidence-scoring LLM call per step, which is an accepted trade-off for the massive increase in reliability.