# ADR-019: Implementing an Intentional Core for Goal Decomposition

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The v12 agent, equipped with an Entity-Graph World Model, has a sophisticated understanding of the *current* screen state. However, the ReAct (Reason+Act) loop, by itself, is purely tactical. For a complex, multi-stage goal (e.g., "Find the latest financial report, summarize it, and email the summary to my manager"), the agent might struggle to maintain focus. It could get bogged down in the low-level details of one step without a clear high-level "map" of the entire task, making it prone to errors or inefficient paths.

We need a mechanism for the agent to perform high-level strategic planning *before* diving into the low-level tactical execution of the ReAct loop. It needs to be able to break down a big problem into smaller, manageable sub-goals.

## Considered Options

1.  **Rely Solely on the ReAct Loop:**
    - **Description:** Do not implement a separate planning step. Hope that the main ReAct prompt, which includes the overall goal, is sufficient for the LLM to manage its own high-level progress internally.
    - **Pros:** Simplest to implement, as it requires no new components.
    - **Cons:** Not reliable for complex tasks. It's difficult to steer the agent's focus within a single, continuous ReAct loop. The agent can easily "forget" the later stages of a goal while working on the initial steps, leading to incomplete tasks.

2.  **Implement a Hierarchical Agent Structure (Intentional Core) (Chosen):**
    - **Description:** Introduce a new, initial "planning" phase that runs *before* the ReAct loop begins.
      1.  **Goal Decomposition:** When a user goal is received, the `AgentCore` first uses a specialized "Goal Decomposer" prompt to ask the LLM to break the complex goal into a sequence of high-level, human-readable **Intentions** (e.g., 1. "Find the financial report", 2. "Summarize the report", 3. "Compose and send the email").
      2.  **Focused Execution:** The `AgentCore` then executes the ReAct loop for *only the first Intention*. The main ReAct prompt is modified to include "Your current sub-goal is: [Intention #1]".
      3.  **Progression:** Once the AI determines that the first Intention is complete (e.g., by using the `finish_task` tool, which will be repurposed as `finish_intention`), the `AgentCore` moves to the next Intention in the list and starts a new ReAct cycle for it.
    - **Pros:**
        -   **Provides Strategic Focus:** Drastically improves the agent's ability to handle long, complex tasks by breaking them down into manageable chunks.
        -   **Improves Reliability:** Reduces the risk of the agent getting sidetracked or forgetting later parts of the original goal.
        -   **Enhanced Transparency:** The GUI can display the overall list of intentions, showing the user the AI's high-level plan and its current progress.
    - **Cons:** Adds an initial planning step, which introduces a small amount of latency at the beginning of a task. Requires more sophisticated state management within the `AgentCore`.

3.  **Recursive Agent Calls:**
    - **Description:** A more advanced approach where the main agent can invoke a subordinate, temporary agent to handle a sub-task.
    - **Pros:** Extremely powerful and flexible for deeply nested tasks.
    - **Cons:** Massively increases complexity in terms of state management, context passing, and cost. It's a full "agent-of-agents" framework, which is beyond the scope of v12 and likely over-engineering. The simpler Intentional Core provides most of the benefits with a fraction of the complexity.

## Decision Outcome

**Chosen Option:** **Option 2: Implement a Hierarchical Agent Structure (Intentional Core).**

**Justification:**

The Intentional Core strikes the perfect balance between strategic planning and tactical execution. It provides the high-level structure needed for complex tasks without the immense overhead of a full recursive agent framework.

-   **Solves the Focus Problem:** By providing the ReAct loop with a clear, immediate sub-goal (the current Intention), we anchor its reasoning process and ensure it makes steady, logical progress toward the overall user goal.
-   **Architectural Soundness:** It creates a clean, hierarchical cognitive model: the user provides a Goal, the Intentional Core creates a Strategy (the list of Intentions), and the ReAct loop performs the Tactics (the Thought->Action steps). This is a robust and scalable model for advanced agentic behavior.
-   **Improves User Experience:** Displaying the list of generated Intentions in the GUI will give the user confidence that the AI has correctly understood their complex request and allows them to track its progress at a high level.

## High-Level Implementation Plan (v12.0.0)

1.  **Design the "Goal Decomposer" Prompt:** Create a new prompt that instructs the LLM to take a user command and output a JSON object containing a list of string "intentions."
2.  **Update `AgentCore`:**
    -   Modify `execute_goal` to first call the LLM with the decomposer prompt.
    -   Store the returned list of intentions in the `WorldModel`.
    -   The main execution will now be a loop that iterates through the list of intentions. Inside this loop, the existing ReAct loop will run, but with its prompt modified to include the *current intention*.
3.  **Repurpose the `finish_task` Tool:** The `finish_task` tool will be renamed to `finish_intention`. When the AI uses this tool, it will signal to the `AgentCore` that the current sub-goal is complete, prompting the `AgentCore` to move to the next intention in the list. If it was the last intention, the entire task is considered successful.
4.  **Update GUI (`VisualLogPanel`):** The panel will be enhanced to display the full list of intentions and highlight the one that is currently active.

## Consequences

-   The `AgentCore` will become significantly more capable of handling complex, multi-stage tasks.
-   The system's reasoning will be more structured and less prone to drift.
-   The main ReAct prompt will be modified to be "intention-aware."
-   The `finish_task` tool will be repurposed, requiring changes in the `Toolbelt` and the main ReAct prompt's instructions.