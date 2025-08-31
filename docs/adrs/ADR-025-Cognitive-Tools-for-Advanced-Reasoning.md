# ADR-025: Cognitive Tools for Advanced Reasoning and Self-Redefinition

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

The MARK-I agent's reasoning is powerful but limited to its observational context. It solves problems by seeing the UI and manipulating it. It cannot solve problems that require abstract, non-visual reasoning (e.g., "What is the most efficient way to sort this data?"). Furthermore, its core purpose, defined by its "Core Directives," is static and unchangeable.

To achieve the final stages of its planned evolution (the Genesis Core), the AI requires two new, purely cognitive capabilities:

1.  **Axiomatic Inference:** The ability to reason from first principles without visual input.
2.  **Ontological Self-Redefinition:** The ability to reflect on and propose changes to its own fundamental purpose.

## Considered Options

1.  **Build Separate, Specialized Engines for Each Capability:**
    - **Description:** Create a new `AxiomaticInferenceEngine` and a separate `SelfRedefinitionEngine`.
    - **Pros:** Highly modular.
    - **Cons:** Over-engineering. These are not persistent processes like the `PerceptionEngine`; they are discrete cognitive *actions*. The best way to model a discrete action in the MARK-I architecture is as a tool in the `Toolbelt`.

2.  **Implement New Capabilities as Cognitive Tools (Chosen):**
    - **Description:** Model these advanced reasoning functions as new, specialized tools available in the `Toolbelt`.
      1.  **`reason_from_first_principles` Tool:** A tool that takes a complex, abstract problem as a string. It uses a powerful LLM with a specialized prompt to solve the problem and returns the solution as a string. It has no access to the screen.
      2.  **`propose_directive_change` Tool:** A meta-tool that allows the AI to reflect on its performance and propose an improvement to its own `AgencyCore`'s Core Directives prompt. The proposal is presented to the user for approval. If approved, a helper function updates the core prompt file on disk.
    - **Pros:**
        -   **Architecturally Consistent:** Perfectly aligns with the ReAct and Toolbelt pattern. These advanced thoughts become explicit, auditable "Act" steps.
        -   **Safe and Controllable:** The user retains ultimate control, especially over changes to the AI's core purpose.
        -   **Extensible:** More cognitive tools (e.g., `_analyze_ethical_dilemma_`) can be easily added in the future.
    - **Cons:** The logic for modifying the core prompt file must be handled with extreme care.

## Decision Outcome

**Chosen Option:** **Option 2: Implement New Capabilities as Cognitive Tools.**

**Justification:**

This is the most elegant, safe, and architecturally sound solution. It empowers the AI with incredible new abilities without breaking the existing cognitive model. By making these functions tools, the AI's use of them becomes a deliberate, traceable action. The `AgencyCore` can reason, "My directive to 'optimize workflow' is too vague. I will use the `propose_directive_change` tool to suggest a more specific version." This makes the AI's path to self-improvement transparent and user-supervised, which is a critical safety feature for an agent of this power.

## High-Level Implementation Plan

1.  **Create `mark_i/agent/tools/cognitive_tools.py`:** This new file will house the new tools.
2.  **Implement `ReasonFromFirstPrinciplesTool`:** This tool will primarily be a prompt wrapper that sends a problem to `GeminiAnalyzer` and returns the text response.
3.  **Implement `ProposeDirectiveChangeTool`:** This tool will trigger a user confirmation GUI. If the user approves, it will carefully overwrite the `AGENCY_PROMPT_TEMPLATE` in `mark_i/agency/agency_core.py`.
4.  **Update `AppController`:** The new cognitive tools will be instantiated and added to the `Toolbelt`.
