# Development Configuration & Choices

This document outlines key development choices, current phase settings, and environment setup for the **Mark-I** project.
**Version 18.0.0 (The Optimization Core) is now considered complete and stable.**
Focus will shift to planning for future enhancements (`vFuture`).

## 1. Core Project Setup

- **Project Name (Informal):** Mark-I
- **Python Package Name:** `mark_i`
- **Language:** Python
- **Python Version (Target):** 3.9+ (or as specified by dependencies like CustomTkinter or OpenCV)
- **Package Manager:** pip
- **Virtual Environment:** venv (standard, recommended)
  - Example setup: `python -m venv .venv` then `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows).

## 1.1. Environment Configuration (per ADR-007, ADR-008)

- **Method:** `.env` file at the project root, loaded using the `python-dotenv` library.
- **Key Variables:**
  - `APP_ENV`: Controls logging, etc.
    - **Possible Values:** `development`, `uat`, `production`.
    - **Default for local development:** Create a `.env` file in the project root with `APP_ENV=development`.
  - **`GEMINI_API_KEY` (Required):** Your API key for accessing Google Gemini API.
    - Obtain from Google AI Studio or Google Cloud Console.
    - Add `GEMINI_API_KEY=your_api_key_here` to your `.env` file.
  - **`GEMINI_MODELS_PRO` (Optional):** Comma-separated list of models for complex reasoning (e.g., `StrategicExecutor`).
    - **Default:** `gemini-1.5-pro-latest`
  - **`GEMINI_MODELS_FLASH` (Optional):** Comma-separated list for fast, tactical execution (e.g., `AgentCore`).
    - **Default:** `gemini-1.5-flash-latest`
  - **`GEMINI_MODELS_NANO` (Optional):** Comma-separated list for lightweight parsing tasks.
    - **Default:** `gemini-2.0-flash-lite`
- **Purpose:** Controls environment-specific behavior (logging, API keys, AI model selection, etc.).
- **`.gitignore`:** The `.env` file **MUST** be added to `.gitignore` to prevent committing environment-specific or sensitive settings (like API keys). The `logs/` directory should also be ignored.

## 2. Current Development Phase Focus

- **Overall Goal for Eighteenth Major Deliverable:** `v18.0.0 (The Optimization Core)` - **COMPLETED.**

  - This version introduces significant performance and efficiency upgrades to the AI's core, including Focused Context Execution and Perceptual Filtering.

- **Active Version (Current State):** `v18.0.0 (The Optimization Core) - STABLE`
  - **Primary Goal for Active Version:** This version is feature-complete and stable.
- **Next Development Cycle Focus:** `vFuture - Planning Phase`
  - Evaluate features listed under "vFuture" in `FEATURE_ROADMAP.MD`.
- **Linting/Formatting Setup:**
  - **Flake8 (Linter):** Enabled (Configured for Black compatibility via `.flake8`).
  - **Black (Formatter):** Enabled (Configured via `pyproject.toml`).
  - Manual adherence to PEP 8 encouraged.

## 3. Architectural & Design Approach

- **Overall Architectural Style:** Proactive, hierarchical agent architecture with new optimizations for efficiency.
  - _Details in `TECHNICAL_DESIGN.MD` and `ADR-029`, `ADR-030`._
- **Logging Strategy:** Comprehensive logging implemented.
- **Code Design Principles:** Readability, Simplicity, Modularity, Testability, Diagnosability.

## 4. Tooling Choices (Key Tools - per ADRs)

- **Environment Management:** `python-dotenv`
- **Logging:** Python `logging` module.
- **Screen Capture:** `Pillow` (`ImageGrab`), `OpenCV-Python`.
- **Image Processing:** `OpenCV-Python`, `NumPy`, `Pillow`.
- **OCR:** `pytesseract`.
- **Input Simulation:** `pyautogui`.
- **Configuration Format:** JSON.
- **CLI:** `argparse`.
- **GUI:** `CustomTkinter`.
- **AI Vision API (v4.0.0+):** `google-generativeai` (Python SDK for Gemini).
- **Unit Testing Framework:** `pytest` (Status: `Implemented` - for v5.0.2)
- **Linter:** `Flake8` (Status: `Enabled`)
- **Formatter:** `Black` (Status: `Enabled`)
- **Import Sorter (Future):** `isort` (Status: `Pending DevLead Enablement`)

## 5. Version Control

- **System:** Git
- **Branching (Simplified Strategy):**
  - `main`: Should now reflect the v18.0.0 stable release.
  - `develop`: Active development branch for any ongoing minor fixes for v18.0.0 or for starting `vFuture` work. Feature branches for new development are created from `develop`.
- **Commit Messages:** Aim for conventional commit style.

## 6. Documentation

- **Docstring Style:** Google Python Style.
- **Project Documentation Status:** Updated for v18.0.0.
- **README.md (Project Root):** Updated for v18.0.0.

## 7. Development Environment

- **Target OS for Bot Runtime:** **Windows** (Primary initial focus).
- **Development OS:** **Windows** (Assumed for DevLead).
- **Key Dependencies Installation (Windows Focus):**
  - Ensure Python 3.9+ is installed and in PATH.
  - Create virtual environment: `python -m venv .venv` & activate.
  - Install packages: `pip install -r requirements.txt`. (Ensure `requirements.txt` is created and maintained).
  - **Tesseract OCR Engine:** Must be installed system-wide and in PATH for OCR features.
  - **(v4.0.0+) Gemini API Key:** Requires a `.env` file with `GEMINI_API_KEY=your_key`.
