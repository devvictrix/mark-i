# Technical Design Document: Mark-I

This document outlines the technical design and architectural considerations for the Mark-I visual automation tool. It has been refactored to reflect the architectural decisions for **v13.0.0 (The God Core)**, as approved in `ADR-022` and `ADR-023`.

The primary architecture is now a proactive, multi-modal, hierarchical AI agent.

## 1. Core Architecture (v13.0.0 Paradigm)

The system is architected around a set of specialized, interacting cores that represent different layers of the AI's "consciousness."

- **`perception.perception_engine.PerceptionEngine` (The Senses):**
  - A standalone, asynchronous engine responsible for continuous, multi-modal environmental sensing.
  - **Responsibility:** To run background threads that consume input from a video stream (screenshots), audio (voice commands), and OS event hooks. It normalizes these inputs into a unified "perception event" stream, which it provides to the `AgencyCore`.
  - This is the AI's sensory cortex, providing the raw data of worldly experience.

- **`agency.agency_core.AgencyCore` (The Will / Executive Brain):**
  - The new highest level of the AI's cognition. It is a proactive, strategic agent.
  - **Responsibility:** To consume the event stream from the `PerceptionEngine`. It continuously reasons about the user's context in relation to its own **Core Directives** (e.g., "Optimize user workflow"). Its primary output is not an action, but a self-generated **task goal** that it deems helpful to the user.

- **`agent.agent_core.AgentCore` (The Cognitive / Tactical Core):**
  - The powerful ReAct-based agent developed in v11. It is now the tactical executor for the `AgencyCore`.
  - **Responsibility:** To receive a high-level goal (either from the user directly via Interactive Command, or from the `AgencyCore`), and execute it flawlessly using its See-Think-Act loop and its `Toolbelt`.

- **`agent.toolbelt.Toolbelt` & `agent.tools.*` (The Hands):**
  - The collection of capabilities available to the `AgentCore`.
  - **v13.0.0 Enhancement:** The Toolbelt can now be dynamically expanded via **Tool Synthesis**. A new meta-tool, `create_new_tool`, allows the `AgencyCore` or `AgentCore` to write, save, and load new Python-based tools on the fly, enabling self-improvement and adaptation.

- **`knowledge.knowledge_base.KnowledgeBase` (The Memory):**
  - Unchanged in its core function. It remains the AI's long-term memory, storing user data, aliases, and learned strategies (Objectives). The `KnowledgeDiscoveryEngine` continues to proactively suggest additions to it.

## 2. The Proactive Cognitive Flow

The primary operational model is no longer a single, user-initiated command, but a continuous, proactive loop:

1.  **Perceive:** The `PerceptionEngine` is always running, observing the screen and listening. It places a "VISUAL_UPDATE" event in its queue every second.
2.  **Assess:** The `AgencyCore` wakes up periodically, consumes the latest events from the queue, and analyzes the latest screenshot.
3.  **Reason (Strategic):** It feeds the current context into its Core Directives prompt and asks a powerful LLM: "Based on my purpose and what I'm seeing, is there a helpful task I should perform?"
4.  **Initiate:** If the strategic reasoning results in a task (e.g., "I see the user performing a repetitive task. I should automate it."), the `AgencyCore` generates a goal string.
5.  **Confirm:** The generated goal is presented to the user for confirmation (a critical safety and usability step).
6.  **Delegate (Tactical):** Upon confirmation, the `AgencyCore` delegates the goal to the `AgentCore`.
7.  **Execute:** The `AgentCore` executes the goal using its familiar, robust ReAct loop, its Entity-Graph `WorldModel`, and its extensible `Toolbelt`.
8.  **Learn:** The outcome of the task execution (success or failure) is used by the `KnowledgeBase` to refine the `success_rate` of the strategy used, closing the learning loop.

## 3. Tool Synthesis

A key feature for making the AI more powerful is the ability to create its own tools.

-   **Trigger:** The `AgentCore` can reason that it lacks a necessary tool to complete a step. Its "Thought" might be, "I need to get the current weather, but I do not have a tool for that. I will use the `create_new_tool` tool."
-   **Process:** It calls the `create_new_tool` with a detailed description of the needed capability. This tool uses an LLM to generate the Python code for a new tool class.
-   **Safety:** The generated code is presented to the user in a confirmation dialog. The user, acting as a security supervisor, must approve the code before it is saved.
-   **Integration:** Once saved, the `Toolbelt` dynamically loads the new Python file, and the new tool is immediately available for the AI to use.

## 4. DEPRECATED: Standalone `AutonomyEngine`

The `AutonomyEngine` from v6 is now superseded by the much more powerful and integrated `AgencyCore`. The `AgencyCore` fulfills the same proactive role but within a more sophisticated and continuous cognitive architecture.
