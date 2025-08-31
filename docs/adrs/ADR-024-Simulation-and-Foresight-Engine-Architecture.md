# ADR-024: Simulation and Foresight Engine Architecture

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The v13 `AgencyCore` is powerfully proactive, but its planning is still based on its training data and past experiences. When faced with a novel or high-stakes task, it executes the plan it believes is best, but it cannot anticipate second-order effects or complex failure modes without actually attempting the task. This is a significant limitation for an agent intended to perform complex operations.

To achieve a higher level of intelligence and safety, the AI needs the ability to perform a "dry run" of a proposed plan. It needs foresight—the ability to simulate the likely consequences of its actions before committing to them.

## Considered Options

1.  **Build a True Digital Twin Environment:**

    - **Description:** Create a complete, sandboxed virtual desktop environment where the AI can execute its actions against virtualized applications.
    - **Pros:** Offers the highest possible fidelity for simulation.
    - **Cons:** Astronomically complex and far beyond the scope of this project. Requires virtualizing the entire OS and its applications, which is a massive engineering effort in itself.

2.  **Implement an LLM-Based Foresight Engine (Chosen):**
    - **Description:** Create a new `SimulationEngine`. This engine does not execute code. Instead, it uses a powerful, large-context LLM (e.g., Gemini 1.5 Pro) to perform a "cognitive simulation."
      - The `AgencyCore`, after generating a strategic plan, passes the plan and the current screen context to the `SimulationEngine`.
      - The engine uses a specialized prompt to ask the LLM to act as a "Red Team" expert. The prompt asks: "Given this plan and this screen, predict the step-by-step outcome. What could go wrong? What are the potential failure points or unintended consequences?"
      - The LLM's response—a textual simulation and risk analysis—is returned to the `AgencyCore`.
    - **Pros:**
      - **Feasible and Powerful:** Leverages the world knowledge and reasoning capabilities of modern LLMs to provide a surprisingly effective simulation without a physical sandbox.
      - **Architecturally Clean:** Creates a dedicated engine for "foresight," which the `AgencyCore` can consult as part of its decision-making process.
      - **Identifies Novel Risks:** An LLM can identify risks that a purely programmatic check might miss (e.g., "Executing this action might close the unsaved document in the background").
    - **Cons:** The simulation is only as good as the LLM's reasoning. It is a cognitive check, not a deterministic one.

## Decision Outcome

**Chosen Option:** **Option 2: Implement an LLM-Based Foresight Engine.**

**Justification:**

This approach is the most pragmatic and intelligent way to grant the AI foresight. It correctly identifies that for a visual desktop agent, the "simulation" is less about bits and bytes and more about understanding context, causality, and human-computer interaction patterns. Using an LLM as the simulation's "physics engine" is a perfect application of its capabilities and aligns with MARK-I's AI-first design philosophy. The `SimulationEngine` will become a critical tool for the `AgencyCore`, allowing it to refine plans, add safety checks, and avoid errors _before_ they happen.

## High-Level Implementation Plan

1.  **Create `mark_i/foresight/simulation_engine.py`:** This will house the `SimulationEngine` class.
2.  **Design the Foresight Prompt:** A new, sophisticated prompt will be engineered that instructs the LLM to act as a simulation and risk analysis expert.
3.  **Implement `simulate_plan` Method:** The engine's core method will take a strategic plan and a visual context, call the `GeminiAnalyzer` with the foresight prompt, and parse the resulting analysis.
4.  **Integrate with `AgencyCore`:** The `AgencyCore`'s main loop will be updated. After generating a task but _before_ executing it, it will call the `SimulationEngine`. If the simulation reveals significant risks, the `AgencyCore` can choose to refine the plan, ask the user for clarification, or abort the task.
