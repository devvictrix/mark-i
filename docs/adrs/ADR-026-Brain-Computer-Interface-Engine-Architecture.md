# ADR-026: Brain-Computer-Interface (BCI) Engine Architecture

- **Status:** Approved
- **Date Decision Made:** 2025-08-31
- **Deciders:** DevLead

## Context and Problem Statement

All interaction with the MARK-I agent is currently bottlenecked by physical I/O: typing commands, speaking, and viewing a screen. To achieve the "Symbiotic Core" vision, a communication channel with a much higher bandwidth is required, one that approaches the speed of thought.

We need an architecture that allows the AI to both receive commands directly from the user's mind and send information back.

## Decision Outcome

**Chosen Option:** A new, dedicated **`BCIEngine`** will be implemented within a new `symbiosis` package. This engine will act as a hardware abstraction layer for a conceptual Brain-Computer Interface.

**Justification:**

This is a foundational requirement for cognitive fusion. By encapsulating all BCI interaction within a dedicated engine, we cleanly separate the highly specialized logic of neural signal processing from the AI's core reasoning. The `AgencyCore` and `AgentCore` will interact with this engine via a new set of BCI-specific tools in the `Toolbelt`, maintaining perfect architectural consistency. This modular approach allows the underlying BCI hardware/SDK to be swapped out in the future without altering the AI's cognitive code.
