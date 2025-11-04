# MARK-I: The Genesis Core - An AI-Powered Visual Automation Agent

![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg)![License](https://img.shields.io/badge/License-Proprietary-red.svg)![Status](https://img.shields.io/badge/Status-v18.0.0%20Stable-brightgreen)

**MARK-I is an intelligent, proactive desktop assistant that uses Google Gemini to see, understand, and interact with any Graphical User Interface (GUI). This project serves as a demonstration of advanced AI agent architecture, moving beyond simple automation to learn from its environment, generate its own tasks to assist the user, and execute complex, multi-step goals from a single natural language command.**

---

## 📈 Project Status & Vision (Seed Stage)

**MARK-I is currently in the seed-stage of development.** We are actively seeking strategic partnerships and initial funding to accelerate R&D and establish market fit.

The vision is to evolve MARK-I from a powerful demonstration into a robust, **enterprise-grade cognitive automation platform**. We are focused on building a next-generation **Robotic Process Automation (RPA)** solution that replaces brittle, selector-based bots with intelligent, vision-based agents capable of handling dynamic UIs and complex, multi-step business processes.

---

### ► Visual Demonstration

*(**Action Required:** Record a short video of the "Interactive Command" mode in action, for example, telling it: **"Log into our web admin, navigate to the sales report, and download the CSV for Q4."** Convert this video to a GIF and replace the placeholder below.)*

![MARK-I Demo GIF](https://user-images.githubusercontent.com/username/repo/your-demo.gif)
*In this demo, MARK-I is given a high-level business goal and autonomously executes the required UI interactions.*

---

## The Problem with Today's Automation

Current Robotic Process Automation (RPA) tools like UiPath and Blue Prism are powerful but suffer from fundamental limitations that make them expensive and difficult to maintain in dynamic enterprise environments.

-   **Brittle & Unreliable:** Traditional RPA relies on hard-coded UI selectors (like HTML IDs or CSS paths). A minor update to an application's interface can break the entire automation, requiring constant, costly maintenance.
-   **Not Truly Intelligent:** These tools lack genuine understanding. They cannot adapt to unexpected situations, read complex documents, or learn from user behavior to improve over time.
-   **High Total Cost of Ownership:** The combination of expensive licenses, specialized developer costs, and continuous maintenance makes traditional RPA a significant investment.

## Our Solution: An AI Agent that Sees, Understands, and Adapts

MARK-I is an **AI-Native** automation platform built from the ground up on a visual, cognitive architecture. It interacts with applications just like a human does, making it resilient, adaptable, and far more capable.

### The Eye-Brain-Hand Architecture

-   **👁️ The Eye (Vision):** Uses Google Gemini's multimodal capabilities to **see and interpret the screen visually**. It understands context and identifies elements like "the submit button" or "the username field" based on visual cues, not fragile selectors.
-   **🧠 The Brain (Cognition):** Understands high-level goals (e.g., "Pull the latest report from SAP") and generates a step-by-step plan using a **ReAct (Reason+Act) cognitive loop**. If a step fails, its **Self-Correction** mechanism allows it to analyze the new screen state and create a new plan to recover.
-   **🤚 The Hand (Action):** Executes the plan by precisely controlling the mouse and keyboard, performing clicks, typing text, and verifying the outcome of each action before proceeding.

**The Key Differentiator:** When a button's ID changes from `id-submit-btn` to `id-confirm-btn`, old RPA bots break. MARK-I continues to function because it visually identifies the button labeled "Confirm" and completes the task.

## Core Features for the Enterprise

-   **🎯 Focused Context Execution:** Intelligently identifies and "crops" its vision to the target application window (e.g., SAP, Salesforce), ignoring desktop clutter. This dramatically increases speed, accuracy, and reduces API costs.
-   **🚫 Perceptual Filtering:** Can be taught to ignore irrelevant UI elements (like widgets, notifications, or decorative charts), ensuring it focuses only on task-relevant components.
-   **🗣️ Interactive Command Core:** Execute complex business processes with a single natural language command.
-   **🧠 Proactive Agency Core:** In a future release, MARK-I will be able to passively observe user workflows, identify repetitive tasks (like manual data entry between two systems), and proactively suggest a new automation.
-   **💡 Self-Correcting Strategies:** The AI learns and saves successful plans. If a UI update breaks a saved plan, it can perform **self-correction** by generating a new one on the fly and remembering it for next time.

## 💼 Business & Enterprise Applications

MARK-I's architecture makes it the ideal platform for next-generation **Cognitive Robotic Process Automation (RPA)**.

**Example Business Command:**
```
"Log into the company's SAP portal, navigate to the 'Vendor Invoices' module, find all invoices from 'ABC Corp' in the last 30 days, and export them to a consolidated PDF."
```

**How MARK-I Executes This:**
1.  **👁️ Eye:** Detects and focuses on the SAP application window, ignoring desktop notifications.
2.  **🧠 Brain:** Uses its knowledge base to visually identify login fields, buttons labeled "Vendor Invoices," and data fields for "ABC Corp", even if the UI changes slightly. It filters out irrelevant UI elements based on its perceptual training.
3.  **🤚 Hand:** Executes precise clicks and typing to log in, navigate menus, apply filters, and trigger the export, verifying the success of each step visually.

## 🚀 Quick Start

### Prerequisites
-   Python 3.9+
-   Google Gemini API key

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd mark-i

# Install dependencies
pip install -r requirements.txt

# Set up your Gemini API key in a new .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Running MARK-I
```bash
# Launch the main GUI (recommended)
python -m mark_i
```

### Technology Stack

| Category              | Technology / Library                                             |
| --------------------- | ---------------------------------------------------------------- |
| **Core Language**     | Python 3.9+                                                      |
| **AI & Machine Learning** | Google Gemini API (`gemini-1.5-pro`, `gemini-1.5-flash`)           |
| **GUI Framework**       | CustomTkinter                                                    |
| **Visual Perception**   | Pillow, OpenCV, PyAutoGUI                                        |
| **UI Automation**       | PyAutoGUI                                                        |
| **Configuration**     | JSON, python-dotenv                                              |
| **Concurrency**       | `threading`, `queue`                                             |
| **Development**       | `pytest` (Testing), `black` (Formatting), `flake8` (Linting)     |

## License

This is a proprietary software project intended for demonstration and seed-stage development. All rights are reserved by the copyright holder. Please see the [LICENSE](LICENSE) file for the full terms.