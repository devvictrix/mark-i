# ADR-029: Focused Context Execution for Efficiency

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The `AgentCore` and `StrategicExecutor` currently operate on full-screen captures for every task. While this provides maximum context for general commands, it is highly inefficient for tasks that are confined to a single application window. This inefficiency manifests in three ways:

1.  **Increased Cost:** Sending full-screen images to the vision model API is more expensive than sending smaller, cropped images.
2.  **Increased Latency:** Larger images take longer for the AI to analyze, slowing down each step of the ReAct loop.
3.  **Reduced Accuracy:** The AI's attention can be distracted by notifications, widgets, or other applications visible on the screen, potentially leading to errors.

We need a mechanism to intelligently focus the AI's visual context to the relevant application for the task at hand.

## Decision Outcome

**Chosen Option:** A new **"pre-flight analysis" step** will be added to the `StrategicExecutor`. Before generating a plan, it will perform a quick analysis of the user's command and the initial screenshot to identify the primary application window. The `StrategicExecutor` will then crop the visual context to this window's bounding box and execute the entire tactical plan within this "focused context."

**Justification:**

This approach is the most architecturally sound solution.

- **Hierarchical Control:** It correctly places the responsibility of defining the "operating area" on the high-level strategist (`StrategicExecutor`), which then provides a focused environment for the tactician (`AgentCore`).
- **Efficiency:** It directly addresses the cost, latency, and accuracy problems by significantly reducing the amount of data processed in the tactical loop.
- **Minimal Disruption:** It leverages the existing hierarchical structure without requiring a fundamental rewrite of the `AgentCore`'s ReAct logic. The `AgentCore` remains agnostic to whether its context is full-screen or cropped; it simply acts on the world it is shown.

## High-Level Implementation Plan

1.  **Create `_determine_and_crop_context` method in `StrategicExecutor`:** This new private method will take the user command and a full screenshot. It will use a fast vision model (e.g., Gemini Flash) with a specialized prompt to get the bounding box of the target application.
2.  **Update `execute_command` in `StrategicExecutor`:**
    - It will call `_determine_and_crop_context` at the start of a task.
    - If a focused context is identified, it will store the cropped image and the `(x, y)` offset of the crop from the screen origin.
    - All subsequent calls to the `AgentCore` within that task will use the cropped image.
3.  **Update `ActionExecutor`:** The context dictionary passed to `execute_action` will be enhanced to include an optional `coordinate_offset: (x, y)`. The `ActionExecutor` will add this offset to all calculated click coordinates, seamlessly translating the `AgentCore`'s relative actions into absolute screen positions.
