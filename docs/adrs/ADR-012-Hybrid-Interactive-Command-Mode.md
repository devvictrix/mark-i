# ADR-012: Hybrid Interactive Command Mode Architecture

- **Status:** Approved
- **Date Decision Made:** 2025-08-30
- **Deciders:** DevLead

## Context and Problem Statement

With the completion of v6.0.0, Mark-I has two primary AI-driven operational modes:

1.  **AI Profile Creator (v5):** An offline, design-time assistant that helps users build structured, reusable automation profiles from high-level goals.
2.  **Autonomous Assistant (v6):** A proactive, online agent that passively observes the screen and attempts to infer and suggest tasks without any direct user input.

A key gap has been identified: there is no mode for a user to give a **direct, on-the-fly command** for immediate execution on the current, arbitrary screen state. The Autonomous Assistant relies purely on inference, which can be limiting. The Profile Creator is not designed for real-time tasks.

We need an architecture for a "Hybrid Mode" that allows a user to type a natural language command and have Mark-I immediately attempt to execute it using its visual understanding and action capabilities, without needing a pre-existing profile.

## Considered Options

1.  **Directly Integrate `GeminiDecisionModule` with a GUI Command Bar (Chosen):**

    - **Description:** This approach leverages the powerful `GeminiDecisionModule` (GDM) developed for v4.0.0's `gemini_perform_task` action. A new UI component, a "Command Bar," will be added to the `MainAppWindow`. When the user types a command and hits "Execute":
      1.  The `AppController` captures the current full screen.
      2.  It passes the user's text command and the screenshot directly to an instance of the `GeminiDecisionModule`.
      3.  The GDM performs its existing Observe-Assess-Plan-Execute loop for that single command.
      4.  This entire operation runs in a background thread to keep the GUI responsive, with status updates provided back to the UI.
    - **Pros:**
      - Maximally reuses the robust, existing `GeminiDecisionModule`, which is purpose-built for this exact task.
      - Provides the most direct and powerful user experience for on-the-fly tasks.
      - Keeps the logic cleanly separated within the `AppController` and the GDM.
    - **Cons:**
      - Requires new GUI components (Command Bar).
      - The latency of the GDM's multiple AI calls will be directly experienced by the user, requiring clear UI feedback (e.g., "Executing...").

2.  **Dynamically Generate and Run a Temporary Profile:**
    - **Description:** When a user enters a command, use `StrategyPlanner` and `ProfileGenerator` in the background to create a temporary, single-rule profile in memory, and then use `MainController` to execute it once.
    - **Pros:** Reuses the v5.0.0 profile generation pipeline.
    - **Cons:** Extremely convoluted and slow. It's an inappropriate use of the profile generation tools, which are designed for interactive user guidance, not fast, headless execution. This adds unnecessary overhead and complexity.

## Decision Outcome

**Chosen Option:** **Option 1: Directly Integrate `GeminiDecisionModule` with a GUI Command Bar.**

**Justification:**

This is the most direct, efficient, and logical architecture. The `GeminiDecisionModule` was engineered to solve exactly this problem: turning a natural language command into a series of actions based on visual context. By connecting it directly to a user-facing command bar, we unlock its full potential as a real-time interactive tool. This approach perfectly embodies the "Hybrid" concept by combining explicit user intent with the AI's autonomous execution capabilities on a live UI. It delivers the "tell it what to do, and it does it" experience that represents the next major leap in Mark-I's capabilities.

## High-Level Implementation Plan

1.  **GUI Enhancement:** Add a new frame to the bottom of the `MainAppWindow`'s center panel containing a `CTkEntry` for command input and an "Execute Command" button.
2.  **`AppController` Logic:** Create a new method, e.g., `execute_interactive_command(command: str)`.
3.  **Threading:** The `execute_interactive_command` method will spawn a new background thread to run the task, preventing the GUI from freezing.
4.  **Execution Flow in Thread:**
    - The thread will call `CaptureEngine` to get a full screenshot.
    - It will then call `self.gemini_decision_module.execute_nlu_task()`, passing the user's command and the screenshot as context.
    - The `AppController` will provide feedback to the GUI via `after()` calls (e.g., updating a status label to "Executing...", "Task Complete", or "Error").
5.  **State Management:** The "Execute Command" button will be disabled while a command is in progress.

## Consequences

- A new, third primary mode of operation will be introduced: "Interactive Command".
- The `MainAppWindow` UI will be updated.
- The `AppController` will be expanded to manage this new interactive workflow.
- This feature will make Mark-I significantly more versatile and powerful for ad-hoc automation tasks.

```

```
