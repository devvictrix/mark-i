# Project Overview: Mark-I

## 1. Purpose

This project, **Mark-I** (inspired by Tony Stark's pioneering suit, with the long-term vision of evolving into a "J.A.R.V.I.S."-like assistant), is a Python-based desktop automation tool. It is designed to **capture and analyze specific regions of your screen in real-time**, extract information using both local computer vision techniques and advanced AI (Google Gemini), and then perform actions (mouse clicks, keyboard inputs, logging) based on a configurable rules engine or natural language commands.

Mark-I aims to provide a powerful, flexible, and user-friendly solution for automating tasks on the Windows desktop (with cross-platform considerations for core functionalities). It particularly shines in scenarios involving dynamic or non-standard UI elements where traditional automation selectors might falter.

**With v4.0.0, Mark-I significantly advanced its AI capabilities, enabling it to understand visual context more deeply and execute tasks based on natural language commands.**

**The vision for v5.0.0 was to further empower users by leveraging AI to assist in the _creation_ of automation profiles themselves, transforming high-level goals into executable Mark-I configurations.**

**The vision for v6.0.0 is to evolve Mark-I from a tool into a proactive assistant, capable of observing the user's screen, identifying opportunities to help, and executing tasks autonomously with user permission.**

## 2. Vision

To create **Mark-I**, a precise, efficient, and highly intelligent visual automation tool that empowers users to automate a wide array of desktop tasks with increasing ease and sophistication. Mark-I distinguishes itself by focusing on visual cues and semantic understanding of screen content, augmented by cutting-edge AI.

- **Core v4.0.0 Achievement:** Evolved Mark-I into an intelligent assistant capable of:

  - Answering complex questions about screen regions (`gemini_vision_query`).
  - Identifying and precisely interacting with UI elements based on textual descriptions and visual context (bounding box actions).
  - Executing tasks based on simple goals provided by the user (`gemini_perform_task` - goal-driven).
  - Interpreting and acting upon natural language commands, decomposing them into executable steps (`gemini_perform_task` - NLU-driven).

- **Aspiration for v5.0.0 (AI-Driven Profile Generation):** To further reduce the manual effort in creating automations by enabling Mark-I to:
  - Understand a user's high-level automation goal expressed in natural language.
  - Generate a strategic plan of action using AI.
  - Interactively guide the user, with AI-powered suggestions for regions, conditions, and actions, to build a complete Mark-I profile from this plan.

- **Aspiration for v6.0.0 (Autonomous Assistant):** To transition Mark-I from a purely reactive tool to a proactive partner by enabling it to:
    - **Observe Holistically:** Continuously monitor the user's screen to understand the broader context of their work.
    - **Identify Opportunities:** Proactively recognize situations where it can provide assistance, such as handling routine dialogs, managing files, or completing simple, repetitive steps.
    - **Act Autonomously (with consent):** Generate a plan for an identified task, present it to the user for confirmation, and execute it upon approval.

The ultimate aspiration is to make Mark-I an exceptionally adaptable, intuitive, and increasingly autonomous assistant that can handle complex automation scenarios with minimal explicit programming, truly embodying the helpfulness and intelligence of a system like J.A.R.V.I.S. for visual desktop automation.

## 3. Core Goals

### Achieved in v5.0.0 and Earlier:

- **Targeted Screen Capture:** Reliably capture image data from user-defined screen areas.
- **Advanced Local Visual Information Extraction:** Pixel/average color detection, template matching, OCR, dominant color analysis.
- **AI-Powered Visual Understanding (Gemini - v4.0.0):**
  - Semantic visual querying via `gemini_vision_query`.
  - Precise interaction with AI-identified elements using bounding boxes.
- **Flexible Conditional Action Execution (Runtime):**
  - Trigger actions based on local or AI-driven visual analysis.
  - Sophisticated rules engine with single/compound conditions and variable handling.
- **AI-Informed Decision Making & NLU (Gemini - v4.0.0):**
  - `GeminiDecisionModule` enabling goal-driven single action execution and NLU-driven multi-step task orchestration via the `gemini_perform_task` action.
- **User-Friendly Configuration via GUI (`MainAppWindow`):** Comprehensive GUI for all aspects of manual profile creation and management.
- **Goal-to-Plan Translation & AI-Assisted Profile Generation (v5.0.0):**
  - `StrategyPlanner` and `ProfileGenerator` work in concert with the `ProfileCreationWizardWindow` to build profiles from high-level user goals.

### Primary Goals for v6.0.0 (Autonomous Assistant):

- **Proactive Scene Assessment:** Implement an `AutonomyEngine` that runs a continuous `Observe -> Assess` loop, using `GeminiAnalyzer` to analyze full-screen captures to identify potential tasks without pre-defined rules or regions.
- **Dynamic Task Planning:** Integrate the `AutonomyEngine` with the existing `StrategyPlanner` to dynamically generate a step-by-step plan for any task identified during the assessment phase.
- **Safe, Confirmation-Based Execution:** Before executing any autonomously generated plan, present it to the user in a clear, non-intrusive GUI dialog for explicit approval.
- **Autonomous Execution Orchestration:** Upon user confirmation, enable the `AutonomyEngine` to use the `GeminiDecisionModule` to execute the dynamic plan, managing the entire task lifecycle from identification to completion.
- **Seamless GUI Integration:** Provide simple controls in the `MainAppWindow` for users to start and stop the Autonomous Assistant and monitor its current status.

## 4. Non-Goals (Out of Scope for v6.0.0)

- **Fully Unsupervised Operation:** The Autonomous Assistant will **not** act without explicit, real-time user confirmation for each proposed plan. It is a "co-pilot," not an unsupervised agent.
- **Complex, Long-Term Memory or Learning:** The assistant's knowledge is limited to the current screen context. It does not learn from past interactions or maintain memory between sessions.
- Direct UI element inspection using OS accessibility APIs (focus remains visual and AI-interpreted semantic analysis).

## 5. Target Users (Vision for v6.0.0)

Mark-I v6.0.0 aims to enhance productivity for all its target users by acting as a helpful assistant that reduces the friction of common, repetitive desktop tasks.

- **Power Users & Developers:** Can offload minor, interruptive tasks (like clearing notifications or managing downloads) to the assistant while they focus on deep work.
- **Business & Office Users:** The assistant can help streamline workflows by recognizing common patterns (e.g., "It looks like you just exported a report, would you like me to email it to your team?") and offering to automate the subsequent steps.
- **All Users:** Benefit from a system that can handle simple digital "chores" proactively, making their overall computer usage smoother and more efficient.

## 6. Core Technology Stack (v6.0.0)

- **Language:** Python (3.9+)
- **AI Model Interaction:** `google-generativeai` (for Google Gemini API).
- **Local CV/OCR:** `OpenCV-Python`, `NumPy`, `Pillow`, `pytesseract`.
- **GUI:** `CustomTkinter`.
- **Core Automation & System:** `pyautogui`, `json`, `argparse`, `threading`, `python-dotenv`, `logging`.
- **(v6.0.0 New Modules):** `mark_i.autonomy.engine`, `mark_i.ui.gui.autonomy_confirmation_dialog`.