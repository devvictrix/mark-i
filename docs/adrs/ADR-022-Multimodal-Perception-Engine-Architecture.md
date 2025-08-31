# ADR-022: Multimodal Perception Engine Architecture

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The MARK-I agent's perception is currently limited and reactive. It only captures a screenshot ("sees") at the beginning of a task or a ReAct loop step. It is "blind" at all other times and is unaware of other potential inputs, such as system events or audio commands.

To evolve into a proactive assistant, the AI needs a continuous and multi-modal understanding of its environment. It needs to be able to see, hear, and feel the state of the operating system persistently.

## Considered Options

1.  **Integrate Perception into the Agent Core:**
    - **Description:** Modify the main `AgentCore` loop to include checks for audio, video changes, and OS events within its reasoning cycle.
    - **Pros:** Keeps logic centralized.
    - **Cons:** Massively violates the Single Responsibility Principle. The `AgentCore`'s job is to reason and act, not to manage low-level hardware and OS event loops. This would make the core loop incredibly complex, slow, and hard to maintain.

2.  **Create a Dedicated, Asynchronous `PerceptionEngine` (Chosen):**
    - **Description:** Implement a new, standalone `PerceptionEngine` that runs in its own set of background threads. This engine's sole responsibility is to consume multiple input streams (video, audio, OS events) and consolidate them into a unified, high-level "context stream" or state object that other parts of the system can subscribe to.
    - **Pros:**
        -   **Clean Separation of Concerns:** Perfectly separates the low-level, asynchronous task of "sensing" from the high-level task of "thinking."
        -   **Scalability & Modularity:** New senses (e.g., network monitoring, webcam input) can be added as new modules within the `PerceptionEngine` without affecting the `AgencyCore` at all.
        -   **Efficiency:** Allows for different polling rates and event-driven logic for each sense, making it much more efficient than a single monolithic loop.
    - **Cons:** Introduces a new major component and requires an inter-thread communication mechanism (e.g., queues, callbacks) for the `AgencyCore` to receive perception data.

## Decision Outcome

**Chosen Option:** **Option 2: Create a Dedicated, Asynchronous `PerceptionEngine`.**

**Justification:**

This is the only architecturally sound solution for building a truly aware agent. It is modular, scalable, and correctly separates the high-speed, low-level world of event handling from the slower, more deliberate world of AI reasoning. The `PerceptionEngine` becomes the AI's "sensory cortex," processing raw stimuli into a coherent picture of the world that the `AgencyCore` (the "frontal lobe") can then act upon.

## High-Level Implementation Plan

1.  **Create `mark_i/perception/perception_engine.py`:** This will house the `PerceptionEngine` class.
2.  **Implement Threaded Lifecycle:** The engine will manage its own `start()` and `stop()` methods, which will in turn manage separate threads for each sensory input (e.g., a `_video_loop`, a `_audio_loop`).
3.  **Develop Input Modules (Placeholders):**
    -   **Video:** A thread that provides a continuous, low-FPS stream of screenshots.
    -   **Audio:** A thread that listens for a wake word and captures voice commands.
    -   **OS Events:** A placeholder for a future module that hooks into OS events.
4.  **Context Aggregation:** The engine will manage a thread-safe queue or state object where it places significant "perception events" (e.g., "User said: 'open notepad'", "New window 'Error' appeared").
5.  **Integration:** The new `AgencyCore` will be initialized with the `PerceptionEngine` and will consume events from its output queue as the trigger for its own reasoning cycle.
