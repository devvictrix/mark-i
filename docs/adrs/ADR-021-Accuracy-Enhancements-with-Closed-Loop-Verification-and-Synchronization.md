# ADR-021: Accuracy Enhancements with Closed-Loop Verification and Synchronization

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The v12 "Sentience Core" AI is highly capable of planning and reasoning. However, its execution ("Act") phase has two key weaknesses that impact its accuracy and reliability:

1.  **Open-Loop Actions:** When a tool like `click_element` is executed, it performs the action and assumes success. The verification of the outcome is handled later in the main `AgentCore`'s "Observe" phase. This creates a disconnect; the tool itself doesn't know if it succeeded, making it brittle to UI lag, animations, or missed clicks.
2.  **Brittle Synchronization:** The AI lacks a robust mechanism to wait for an application to finish loading or for a process to complete. It must rely on fixed `time.sleep()` calls or proceed immediately, which often leads to failure when interacting with applications of variable speed.

To enhance the AI's accuracy, we need to make its actions more intelligent, self-aware, and synchronized with the live state of the UI.

## Considered Options

1.  **No Change (Rely on AgentCore's Loop):**
    - **Description:** Continue with the existing architecture where the `AgentCore` is solely responsible for verifying outcomes after an action is complete.
    - **Pros:** No architectural changes needed.
    - **Cons:** Fails to address the core problem. Actions remain "dumb" primitives, and the agent cannot be resilient to common issues like UI lag. It cannot distinguish between a failed action and an action that simply took a long time to produce a result.

2.  **Implement Closed-Loop Verification within Tools and a Dedicated Synchronization Tool (Chosen):**
    - **Description:** This approach enhances the "Act" phase directly.
      1.  **Create a `wait_for_visual_cue` Tool:** Implement a new, first-class tool in the `Toolbelt`. This tool will take a textual description of a visual cue (e.g., "the 'Save Complete' dialog") and a timeout. It will repeatedly observe the screen until the cue appears or the timeout is reached.
      2.  **Upgrade `ClickElementTool` to perform Closed-Loop Verification:** Modify the `click_element` tool to accept an optional `expected_outcome_description` parameter. After performing the click, the tool will internally use the logic of the `wait_for_visual_cue` tool to actively check if the expected outcome has appeared on the screen. The tool's success or failure will now be based on this verification, not just the physical click.
    - **Pros:**
        -   **Dramatically Increases Reliability:** Makes actions resilient to timing issues and provides immediate feedback on success or failure *at the source*.
        -   **Eliminates Brittle Sleeps:** Allows the AI to create intelligent, event-driven plans (e.g., "Click save, then wait for the 'Save Complete' dialog to appear").
        -   **Enhances Agent Reasoning:** The AI can now make more sophisticated plans that explicitly involve waiting for UI state changes.
    - **Cons:** Increases the complexity of the `click_element` tool. May slightly increase latency on actions that now perform verification.

## Decision Outcome

**Chosen Option:** **Option 2: Implement Closed-Loop Verification and a Synchronization Tool.**

**Justification:**

This is the most direct and powerful way to solve the stated accuracy problems. It moves the AI's execution from a simple, open-loop model to a robust, closed-loop, event-driven model.

-   **Accuracy & Robustness:** By making actions self-verifying, we create a much more resilient agent that can handle the unpredictable nature of modern user interfaces.
-   **Intelligent Synchronization:** The `wait_for_visual_cue` tool is a fundamental capability for any advanced UI automation agent, allowing it to move at the speed of the application, not on a fixed timer.
-   **Architectural Soundness:** This enhancement fits perfectly within the existing `Toolbelt` architecture. The new `wait_for_visual_cue` is an excellent example of a modular tool, and the upgrade to `click_element` demonstrates how existing tools can be made more intelligent.

## High-Level Implementation Plan

1.  **Create `mark_i/agent/tools/synchronization_tools.py`:**
    -   Define a `WaitForVisualCueTool` class.
    -   Its `execute` method will contain a loop that calls `GeminiAnalyzer` to check for a visual cue until a timeout is reached.
2.  **Update `mark_i/agent/tools/visual_tools.py`:**
    -   Update the `ClickElementTool`'s `__init__` to accept an instance of the `WaitForVisualCueTool`.
    -   Update its `description` to include the new optional `expected_outcome_description` parameter.
    -   Modify its `execute` method to call the internal `WaitForVisualCueTool` after the click if the new parameter is provided.
3.  **Update `mark_i/ui/gui/app_controller.py`:**
    -   In `_initialize_engines`, instantiate `WaitForVisualCueTool`.
    -   Pass the new tool instance into the `ClickElementTool` constructor.
    -   Add the new `WaitForVisualCueTool` to the list of tools when creating the `Toolbelt`.
