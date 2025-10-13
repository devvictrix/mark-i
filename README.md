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

The vision for MARK-I is to create a true cognitive partner—a "J.A.R.V.I.S. for your desktop"—that can anticipate needs and optimize workflows. Its advanced **Eye-Brain-Hand** architecture enables a powerful set of features:

### 👁️ **Enhanced Vision System (The Eye)**
-   **🎯 Focused Context Execution:** MARK-I intelligently identifies target application windows and focuses its vision only on relevant areas, dramatically increasing speed, accuracy, and cost-efficiency.
-   **🖼️ Smart Visual Processing:** Automatically crops screenshots to application boundaries, reducing API costs and processing time while eliminating desktop distractions.
-   **📍 Precise Coordinate Translation:** Seamlessly converts relative coordinates from focused contexts to absolute screen positions for accurate interactions.

### 🧠 **Intelligent Filtering System (The Brain)**
-   **🚫 Perceptual Filtering:** Users can teach MARK-I what visual elements to ignore (chat spam, UI decorations, notifications), allowing it to focus only on relevant screen content.
-   **🎯 Smart Entity Analysis:** AI automatically excludes ignored elements during screen analysis, improving accuracy and reducing visual noise.
-   **🛠️ Easy Management Interface:** Intuitive tools for managing ignore lists through the Knowledge Curator and dedicated management windows.

### 🤚 **Precise Action System (The Hand)**
-   **🤖 Interactive Command Core:** Give MARK-I a direct command in plain English (e.g., "Level my character from 85 to 99 by hunting monsters"), and its `AgentCore` will use a **ReAct (Reason+Act) cognitive loop** to execute the task step-by-step.
-   **🧠 Proactive Agency Core:** When enabled, MARK-I passively observes the user's screen, identifies repetitive or inefficient actions based on its **Core Directives**, and proactively suggests automations for the user to approve.
-   **🔍 Knowledge Discovery & Memory:** MARK-I can learn about a specific user's environment, identifying key UI elements and data fields. This knowledge is curated by the user and stored in a persistent `knowledge_base.json`, making the AI more personalized and effective over time.
-   **💡 Self-Correcting Strategies:** The AI uses an **Objective-Strategy-Tactic (OST)** pattern. It learns and saves successful plans for goals. If a saved strategy fails due to a UI change, it can perform **self-correction** by generating a new plan on the fly.
-   **🧙 AI-Driven Profile Creator:** For complex, recurring tasks, an interactive wizard uses AI to help translate a high-level goal into a complete, reusable automation profile.

## For Developers & Hirers: Technical Deep Dive

MARK-I is a demonstration of advanced software architecture, AI agent design, and a deep understanding of system integration.

### Architectural Overview

The system is built on a **hierarchical Eye-Brain-Hand AI architecture** where different components handle distinct aspects of perception, cognition, and action:

#### 👁️ **The Eye (Vision System)**
-   **Focused Context Execution:** Intelligently detects and crops to target application windows
-   **Perceptual Filtering:** Filters out visual noise and distractions based on user-defined ignore lists
-   **Coordinate Translation:** Seamlessly handles relative-to-absolute coordinate conversion

#### 🧠 **The Brain (Cognitive System)**
-   **Agency Core (The Strategist):** The highest level of thought. It operates proactively, observing the user and its environment via the `PerceptionEngine` to generate its own goals based on a set of core directives.
-   **Strategic Executor (The Planner):** When a goal is set (by the user or the Agency Core), this executor creates a high-level, multi-step plan. It leverages a `KnowledgeBase` to use learned strategies (Objectives) or generate new ones, performing self-correction if a plan fails.
-   **WorldModel:** Maintains structured understanding of UI entities with intelligent filtering capabilities.

#### 🤚 **The Hand (Action System)**
-   **Agent Core (The Tactician):** This is the workhorse that executes plans. It operates on a **ReAct (Reason+Act)** loop, using its `Toolbelt` of capabilities (clicking, typing, etc.) to carry out one step at a time based on its real-time visual understanding of the screen.
-   **Toolbelt & Tools:** Comprehensive action execution system with visual element detection, typing, hotkeys, and synchronization tools.
-   **ActionExecutor:** Handles precise physical actions with coordinate offset support for focused contexts.

This **Eye-Brain-Hand** separation enables highly complex, robust, and adaptive behavior perfect for gaming automation and complex desktop tasks.

## 🎮 Perfect for Gaming Automation

MARK-I's Eye-Brain-Hand architecture makes it ideal for complex gaming automation tasks:

**Example Gaming Command:**
```
"Level my character from 85 to 99 by hunting Anolians in the Magma Dungeon. 
Pick up all Anolian Cards, Immortal Hearts, and zeny. 
When HP drops below 30%, use healing items."
```

**How MARK-I Executes This:**
1. **👁️ Eye:** Detects and focuses on the game window, ignoring desktop distractions
2. **🧠 Brain:** Filters out chat spam, UI decorations, and other visual noise you've taught it to ignore
3. **🤚 Hand:** Executes precise game actions - clicking monsters, using skills, picking up items, healing when needed

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Gemini API key

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd mark-i

# Install dependencies
pip install -r requirements.txt

# Set up your Gemini API key
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Running MARK-I
```bash
# Launch the GUI (recommended)
python -m mark_i

# Or run specific commands
python -m mark_i [command] [options]
```

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
