# MARK-I: The Genesis Core - An AI-Powered Visual Automation Agent

![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)![License](https://img.shields.io/badge/License-Proprietary-red.svg)![Status](https://img.shields.io/badge/Status-v18.0.0%20Stable-brightgreen)

**MARK-I is an intelligent, proactive desktop assistant that uses Google Gemini to see, understand, and interact with any Graphical User Interface (GUI). This project serves as a demonstration of advanced AI agent architecture, moving beyond simple automation to learn from its environment, generate its own tasks to assist the user, and execute complex, multi-step goals from a single natural language command.**

---

### **► Visual Demonstration**

*(**Action Required:** Record a short video of the "Interactive Command" mode in action, for example, telling it "Open Notepad and type 'Hello World'". Convert this video to a GIF and replace the placeholder below.)*

![MARK-I Demo GIF](https://user-images.githubusercontent.com/username/repo/your-demo.gif)
*In this demo, MARK-I is given a high-level goal and autonomously executes the required UI interactions.*

---

## Vision & Core Features

The vision for MARK-I is to create a true cognitive partner—a "J.A.R.V.I.S. for your desktop"—that can anticipate needs and optimize workflows. Its advanced architecture enables a powerful set of features:

-   **🤖 Interactive Command Core:** Give MARK-I a direct command in plain English (e.g., "Find the latest report in my downloads and move it to the 'Reports' folder"), and its `AgentCore` will use a **ReAct (Reason+Act) cognitive loop** to execute the task step-by-step.
-   **🧠 Proactive Agency Core:** When enabled, MARK-I passively observes the user's screen, identifies repetitive or inefficient actions based on its **Core Directives**, and proactively suggests automations for the user to approve.
-   **🔍 Knowledge Discovery & Memory:** MARK-I can learn about a specific user's environment, identifying key UI elements and data fields. This knowledge is curated by the user and stored in a persistent `knowledge_base.json`, making the AI more personalized and effective over time.
-   **💡 Self-Correcting Strategies:** The AI uses an **Objective-Strategy-Tactic (OST)** pattern. It learns and saves successful plans for goals. If a saved strategy fails due to a UI change, it can perform **self-correction** by generating a new plan on the fly.
-   **⚡️ Optimized & Focused:** For application-specific tasks, MARK-I intelligently identifies the app window and focuses its vision and actions only on that area, dramatically increasing speed, accuracy, and cost-efficiency.
-   **🧙 AI-Driven Profile Creator:** For complex, recurring tasks, an interactive wizard uses AI to help translate a high-level goal into a complete, reusable automation profile.

## For Developers & Hirers: Technical Deep Dive

MARK-I is a demonstration of advanced software architecture, AI agent design, and a deep understanding of system integration.

### Architectural Overview

The system is built on a **hierarchical, multi-core AI architecture** where different agents handle distinct levels of cognition:

-   **Agency Core (The Strategist):** The highest level of thought. It operates proactively, observing the user and its environment via the `PerceptionEngine` to generate its own goals based on a set of core directives.
-   **Strategic Executor (The Planner):** When a goal is set (by the user or the Agency Core), this executor creates a high-level, multi-step plan. It leverages a `KnowledgeBase` to use learned strategies (Objectives) or generate new ones, performing self-correction if a plan fails.
-   **Agent Core (The Tactician):** This is the workhorse that executes plans. It operates on a **ReAct (Reason+Act)** loop, using its `Toolbelt` of capabilities (clicking, typing, etc.) to carry out one step at a time based on its real-time visual understanding of the screen.

This separation of concerns allows for highly complex, robust, and adaptive behavior.

### Technology Stack

| Category              | Technology / Library                                                              |
| --------------------- | --------------------------------------------------------------------------------- |
| **Core Language**     | Python 3.9+                                                                       |
| **AI & Machine Learning** | Google Gemini API (`gemini-1.5-pro`, `gemini-1.5-flash`)                            |
| **GUI Framework**     | CustomTkinter                                                                     |
| **Visual Perception** | Pillow, OpenCV, PyAutoGUI                                                         |
| **UI Automation**     | PyAutoGUI                                                                         |
| **Configuration**     | JSON, python-dotenv                                                               |
| **Concurrency**       | `threading`, `queue`                                                              |
| **Development**       | `pytest` (Testing), `black` (Formatting), `flake8` (Linting)                      |

## License

This is a proprietary software project. All rights are reserved by the copyright holder. Please see the [LICENSE](LICENSE) file for the full terms.
