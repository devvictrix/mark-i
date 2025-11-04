# MARK-I: The Symbiotic AI Desktop Assistant

**_An AI-powered visual automation agent that sees, understands, and interacts with any GUI, learning from its environment to proactively assist you._**

---

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Version](https://img.shields.io/badge/version-18.0.0-blue)
![Python Version](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

MARK-I is an intelligent desktop assistant powered by AI that transcends traditional automation. By leveraging Google Gemini, it can **see, understand, and interact** with any Graphical User Interface (GUI). MARK-I is not merely a tool that follows commands; it's a cognitive partner that learns from its user's environment, anticipates needs, and executes complex, multi-step tasks from a single natural language command.

## The Problem

As our work on computers becomes increasingly complex, automation tools have remained rudimentary. They cannot adapt to UI changes, understand the context of complex tasks, or learn from their mistakes. This creates a "capability gap" that leaves users performing tedious, repetitive, and time-consuming work.

## Our Vision: Your J.A.R.V.I.S. for the Desktop

We built MARK-I to be an exceptionally intelligent and adaptive assistant—a J.A.R.V.I.S. for the desktop. It works seamlessly with you, learns from your behavior, and continuously grows its own capabilities. Our ultimate vision is a perfect partnership between human and AI, unlocking a new level of productivity and creativity.

*[ Placeholder for a GIF demonstrating MARK-I in action ]*

## ✨ Core Capabilities

MARK-I is built on a Hierarchical AI architecture, enabling advanced capabilities that set it apart from conventional tools:

*   **🧠 Proactive Assistance (Agency Core):** MARK-I doesn't just wait for commands. It **proactively observes** the user's screen in the background. When it detects an opportunity to help (like a finished download or a repetitive task), it offers to automate it for you (with your confirmation).
*   **🗣️ Natural Language Command (Agent Core):** It can take commands in plain English (e.g., "search for information about Mr. A from Google and Facebook") and uses a **ReAct (Reason+Act)** cognitive loop to plan and execute the task step-by-step until the goal is achieved.
*   **💡 Self-Correction & Learning:** When a previously successful plan fails (e.g., due to a UI change), MARK-I can **analyze the situation and create a new plan** to complete the task. It learns and remembers the better, new plan for the future.
*   **🔧 Self-Improvement via Tool Synthesis:** When faced with a problem it can't solve with its existing tools, the AI can **write its own new code** to create new tools, endlessly expanding its own capabilities.
*   **🎯 Intelligent Focus & Efficiency (The Optimization Core):**
    *   **Focused Context Execution:** The AI automatically "focuses" its vision on the relevant application window for a given task. This reduces the data it needs to process, making it **faster, more accurate, and more cost-effective**.
    *   **Perceptual Filtering:** Users can teach the AI to "ignore" visual noise on the screen (like clock widgets or notifications), allowing it to concentrate only on what matters for the task.
*   **💻 Deep System Awareness:** MARK-I possesses a deep understanding of the user's environment—from hardware specs and installed applications to the user's typical workflow patterns—enabling smarter decision-making.

## 🏛️ Architecture Overview

MARK-I uses an **Eye-Brain-Hand** paradigm, which clearly separates the AI's functions into distinct components, allowing for complex and flexible cognitive processing.

*   **Eye (Perception):** A multi-modal system for sensing the environment.
*   **Brain (Cognition):** A hierarchical AI brain composed of an `Agency Core` (the strategist) and an `Agent Core` (the tactician).
*   **Hand (Action):** A precise system for command execution and interaction with any GUI.

```mermaid
graph TB
    subgraph "MARK-I Core Architecture"
        subgraph "Cognitive Layer"
            AC[Agency Core<br/>Strategic/Proactive]
            AGC[Agent Core<br/>Tactical/Reactive]
            SE[Strategic Executor<br/>Planning]
        end
        
        subgraph "Processing Engines"
            GE[Gemini Engine<br/>AI Analysis]
            DE[Decision Engine<br/>Rule Processing]
            PE[Primitive Executors<br/>Basic Actions]
            TSE[Tool Synthesis Engine<br/>Self-Improvement]
        end
        
        subgraph "Perception Layer"
            CE[Capture Engine<br/>Visual Input]
            PF[Perceptual Filter<br/>Focus & Attention]
            VR[Visual Recognition<br/>Pattern Matching]
        end
        
        subgraph "Action Layer"
            AE[Action Executor<br/>GUI Interaction]
            TB[Toolbelt<br/>Tool Management]
            WM[World Model<br/>State Tracking]
        end
        
        subgraph "Knowledge & Memory"
            KB[Knowledge Base<br/>Learning & Memory]
            ESC[Enhanced System Context<br/>Environment Awareness]
            PM[Profile Manager<br/>Automation Profiles]
        end
        
        subgraph "Interface Layer"
            SI[Symbiosis Interface<br/>Human-AI Collaboration]
            GUI[GUI Components<br/>Visual Interface]
            CLI[CLI Interface<br/>Command Line]
        end
    
    AC --> SE
    AC --> AGC
    SE --> AGC
    AGC --> GE
    AGC --> DE
    AGC --> TB
    GE --> TSE
    CE --> PF
    PF --> VR
    VR --> AGC
    AGC --> AE
    AE --> WM
    TB --> PE
    KB --> AC
    KB --> AGC
    ESC --> AC
    PM --> AGC
    SI --> AC
    SI --> AGC
```

## 🛠️ Technology Stack

*   **Language:** Python 3.9+
*   **AI/ML:** Google Gemini API (`gemini-1.5-pro`, `gemini-1.5-flash`)
*   **GUI Framework:** CustomTkinter
*   **Visual Perception:** Pillow, OpenCV, PyAutoGUI
*   **UI Automation:** PyAutoGUI
*   **Configuration:** JSON, python-dotenv

## 🚀 Getting Started

### Prerequisites

*   Python 3.9+
*   Google Gemini API Key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/mark-i.git
    cd mark-i
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configure your environment:**
    *   Create a file named `.env` in the project root.
    *   Add your Google Gemini API key to the file:
        ```env
        GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```

### Running the Application

Launch the main Command & Control interface:
```bash
python -m mark_i
```

## 📈 Roadmap

MARK-I has achieved its core architectural and performance goals. Our `vFuture` plans are focused on expanding its capabilities even further:

*   **Multi-Application Workflows:** Orchestrate complex processes that span multiple different applications.
*   **Voice Command Integration:** Enable more natural interaction through voice commands.
*   **Task Scheduling:** Execute automations based on a predefined schedule.
*   **Extensible Platform:** Create a Plugin and API system for third-party developers to build new tools and integrations.

## 🤝 Contributing

We welcome developers and visionaries who are passionate about building the future of desktop automation. If you are interested in contributing, please read `CONTRIBUTING.md` (to be added) or open an Issue to share your ideas.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 📞 Contact

Interested in our vision? Want to discuss investment or partnership opportunities?
*   **Project Lead:** Panupong Jaengaksorn
*   **Email:** dev.victrix@gmail.com
