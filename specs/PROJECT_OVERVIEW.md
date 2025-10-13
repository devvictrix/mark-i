# Project Overview: Mark-I

## 1. Purpose

This project, **Mark-I**, is a Python-based desktop automation tool. It has evolved into a proactive, reasoning AI agent designed to understand a user's context, anticipate their needs, and automate complex tasks with a high degree of autonomy and intelligence.

It operates not just by executing commands, but by continuously perceiving its environment, generating its own tasks based on a set of core directives, and even creating its own new capabilities to solve novel problems.

**With v18.0.0, Mark-I has achieved the "Optimization Core,"** enhancing its symbiotic capabilities with advanced efficiency and focus features, making it a faster, more accurate, and more cost-effective cognitive partner.

## 2. Vision

To create **Mark-I**, an exceptionally adaptable, intuitive, and increasingly autonomous assistant that can handle complex automation scenarios with minimal explicit programming, truly embodying the helpfulness and intelligence of a system like J.A.R.V.I.S. for visual desktop automation.

- **v1-v17 (Foundation to Symbiosis):** Evolved Mark-I into a powerful, proactive agent capable of high-level reasoning and a conceptual human-AI interface.
- **v18.0.0 (The Optimization Core):** Refines the agent's core performance with:
  - **Focused Context Execution:** The ability to intelligently confine its visual attention to a single application window for specific tasks, dramatically increasing speed and reducing operational costs.
  - **Perceptual Filtering:** A user-trainable memory of what to ignore, allowing the AI to filter out visual noise and focus only on what is relevant to the task at hand.

The ultimate aspiration is to create a seamless partnership where the distinction between the user's mind and the AI's capabilities blurs, leading to a level of problem-solving and creativity that neither could achieve alone, all while operating with maximum efficiency.

## 3. Core Goals

### Primary Goals for v18.0.0 (The Optimization Core):

- **Implement Focused Context Execution:** Upgrade the `StrategicExecutor` to dynamically identify and use application-specific regions for task execution.
- **Implement Perceptual Filtering:** Enhance the `KnowledgeBase` and `AgentCore` to support a user-defined "ignore list" to improve perceptual accuracy.
- **Enhance GUI for New Features:** Update the `KnowledgeCuratorWindow` to support adding items to the perceptual filter.

## 4. Core Technology Stack (v18.0.0)

- **Language:** Python (3.9+)
- **AI Model Interaction:** `google-generativeai` (for Google Gemini API).
- **GUI:** `CustomTkinter`.
- **Core Automation & System:** `pyautogui`, `json`, `threading`, `python-dotenv`, `logging`.
- **Key Cores & Engines:** `AgencyCore`, `AgentCore`, `PerceptionEngine`, `SimulationEngine`, `BCIEngine`, `SharedCognitiveWorkspace`, `KnowledgeBase`, `GeminiAnalyzer`.
- **Key AI Patterns:** Hierarchical Agency, ReAct, Toolbelt (including BCI & Cognitive tools), Shared Cognitive Graph, LLM-based Foresight, **Focused Context Execution**, **Perceptual Filtering**.
