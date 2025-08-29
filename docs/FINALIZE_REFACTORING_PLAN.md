# Finalized Refactoring Plan for Mark-I

## 1. Analysis and Recap

This document finalizes the comprehensive refactoring strategy for the `mark-i` project. The primary goal is to evolve the codebase into a more modular, maintainable, and professional structure, directly addressing the initial request for a NestJS-inspired categorization.

Through our analysis, we have established several key principles:

1.  **Clarity Through Naming:** The core of the refactor is to rename all Python source files to a `name_type.py` convention (e.g., `config_service.py`) to make each module's role immediately obvious.
2.  **Python Compatibility:** We will use underscores (`_`) instead of dots (`.`) in filenames to ensure compatibility with Python's import system.
3.  **Codebase Health:** To prevent monolithic files, we are introducing soft Lines of Code (LOC) limits for both files and functions, encouraging a more modular design.
4.  **Scope Limitation:** The refactoring will focus exclusively on the application's source code (`mark_i/`), tests (`tests/`), and example profiles (`profiles/`). The `docs/` directory will remain unchanged.
5.  **Professional Enhancements:** To elevate the project's quality, we are integrating several best practices, including automated code quality tooling, clearer dependency management, custom exceptions, better developer onboarding, and centralized constants.

This plan serves as the definitive blueprint for the implementation phase.

---

## 2. Guiding Principles

### Naming Convention
-   **Pattern:** `name_type.py` (e.g., `capture_engine.py`, `main_app_window.py`).
-   **Purpose:** To make the primary responsibility of each module clear from its filename.

### Lines of Code (LOC) Guidelines
-   **File Size Limit (Soft):** 400-600 LoC. Files exceeding this should be reviewed for potential refactoring into smaller modules.
-   **Function/Method Size Limit (Soft):** 50-70 LoC. Functions exceeding this should be broken down into smaller, single-purpose helper methods.

### Bonus Enhancements for Professional Quality
1.  **Automated Code Quality:** Integrate `isort` (import sorting) and `mypy` (static type checking) to enforce consistency and catch bugs early.
2.  **Improved Dependency Management:** Split `requirements.txt` into `requirements.txt` (for production) and `requirements-dev.txt` (for development tools).
3.  **Custom Exceptions:** Create `mark_i/core/exceptions_custom.py` for more descriptive and precise error handling.
4.  **Developer Onboarding:** Add a `.env.example` file to guide new developers in setting up the required environment variables.
5.  **Centralized Constants:** Create `mark_i/core/constants_app.py` to hold widely used application constants, reducing "magic strings".

---

## 3. Finalized File Structure & Categorization

### Core Application & Services
*The application's entry point, main controller, and foundational services.*

| Original File Path                   | Proposed File Path                     | Reasoning/Notes                                                         |
| :----------------------------------- | :------------------------------------- | :---------------------------------------------------------------------- |
| `mark_i/__main__.py`                 | `mark_i/__main__.py`                   | **No Change.** Python standard entry point.                             |
| `mark_i/main_controller.py`          | `mark_i/main_controller.py`            | The main application orchestrator.                                      |
| `mark_i/core/config_manager.py`      | `mark_i/core/config_service.py`        | Provides configuration as a service.                                    |
| `mark_i/core/logging_setup.py`       | `mark_i/core/logging_config.py`        | Configures the logging system.                                          |
| *(New File)*                         | `mark_i/core/exceptions_custom.py`     | **(Bonus)** Defines application-specific exceptions.                    |
| *(New File)*                         | `mark_i/core/constants_app.py`         | **(Bonus)** Centralizes application-wide constants.                     |

### Bot Runtime Engines
*Modules performing the primary runtime tasks of the bot.*

| Original File Path                             | Proposed File Path                               | Reasoning/Notes                                                                   |
| :--------------------------------------------- | :----------------------------------------------- | :-------------------------------------------------------------------------------- |
| `mark_i/engines/capture_engine.py`             | `mark_i/engines/capture_engine.py`               | `.engine` is a fitting type for this high-level task performer.                 |
| `mark_i/engines/analysis_engine.py`            | `mark_i/engines/analysis_engine.py`              | `.engine` is a fitting type.                                                    |
| `mark_i/engines/rules_engine.py`               | `mark_i/engines/rules_engine.py`                 | `.engine` is a fitting type.                                                    |
| `mark_i/engines/action_executor.py`            | `mark_i/engines/action_executor.py`              | `.executor` is a highly descriptive type for executing UI actions.              |
| `mark_i/engines/gemini_analyzer.py`            | `mark_i/engines/gemini_analyzer.py`              | `.analyzer` is more specific than `.service` for its role.                    |
| `mark_i/engines/gemini_decision_module.py`     | `mark_i/engines/gemini_decision_module.py`       | `.module` aligns with a self-contained feature unit.                              |
| `mark_i/engines/condition_evaluators.py`       | `mark_i/engines/condition_evaluator.py`          | Contains Strategy Pattern implementations; `.evaluator` is the perfect type.    |
| `mark_i/engines/primitive_executors.py`        | `mark_i/engines/primitive_executor.py`           | Contains Strategy Pattern implementations; `.executor` is the perfect type.     |

### AI-Powered Generation Logic
*Modules for the AI-driven profile creation feature.*

| Original File Path                            | Proposed File Path                              | Reasoning/Notes                                                                   |
| :-------------------------------------------- | :---------------------------------------------- | :-------------------------------------------------------------------------------- |
| `mark_i/generation/strategy_planner.py`       | `mark_i/generation/strategy_planner.py`         | `.planner` is highly descriptive.                                                 |
| `mark_i/generation/profile_generator.py`      | `mark_i/generation/profile_generator.py`        | `.generator` is the perfect type.                                                 |

### User Interface (UI)
*Modules related to all user-facing interfaces, with a refined sub-package structure.*

| Original File Path                                          | Proposed File Path                                          | Reasoning/Notes                                                                       |
| :---------------------------------------------------------- | :---------------------------------------------------------- | :------------------------------------------------------------------------------------ |
| `mark_i/ui/cli.py`                                          | `mark_i/ui/cli_ui.py`                                       | Defines the Command-Line Interface.                                                   |
| `mark_i/ui/gui/gui_config.py`                               | `mark_i/ui/gui/gui_config.py`                               | GUI-specific configuration.                                                           |
| `mark_i/ui/gui/gui_utils.py`                                | `mark_i/ui/gui/gui_utils.py`                                | GUI utility functions.                                                                |
| `mark_i/ui/gui/main_app_window.py`                          | `mark_i/ui/gui/windows/main_app_window.py`                  | **New `windows` sub-package.** A top-level window.                                    |
| `mark_i/ui/gui/region_selector.py`                          | `mark_i/ui/gui/windows/region_selector_window.py`           | Moved to `windows` sub-package.                                                       |
| `mark_i/ui/gui/generation/sub_image_selector_window.py`     | `mark_i/ui/gui/windows/sub_image_selector_window.py`        | Moved to `windows` for consistency.                                                   |
| `mark_i/ui/gui/generation/profile_creation_wizard.py`       | `mark_i/ui/gui/wizards/profile_creation_wizard.py`          | **New `wizards` sub-package.** A multi-step window.                                   |
| `mark_i/ui/gui/panels/details_panel.py`                     | `mark_i/ui/gui/panels/details_panel.py`                     | A major, reusable panel within the main window.                                       |
| `mark_i/ui/gui/panels/condition_editor_component.py`        | `mark_i/ui/gui/components/condition_editor_component.py`    | **New `components` sub-package.** A smaller, reusable UI piece.                       |

### Testing & Example Data
*Test files and profiles will be renamed to mirror the new conventions.*

| Item Type                                | Example Original Path                           | Example Proposed Path                               |
| :--------------------------------------- | :---------------------------------------------- | :-------------------------------------------------- |
| Test Files                               | `tests/core/test_config_manager.py`             | `tests/core/test_config_service.py`                 |
| Example Profiles                         | `profiles/example_profile.json`                 | `profiles/example.profile.json`                     |

---

## 4. Implementation Plan

The refactoring will be executed in the following order to ensure a smooth transition:
1.  **Prepare Directory Structure:** Create the new sub-packages (`ui/gui/windows`, `ui/gui/wizards`, `ui/gui/components`).
2.  **Rename & Move Files:** All Python source files, tests, and profiles will be renamed and moved according to the plan.
3.  **Update Imports:** Systematically update all `import` statements across the entire codebase to reflect the new file names and locations.
4.  **Implement Enhancements:**
    -   Create `exceptions_custom.py` and `constants_app.py` and refactor the code to use them.
    -   Split `requirements.txt` into `requirements.txt` and `requirements-dev.txt`.
    -   Create `.env.example`.
    -   Configure `pyproject.toml` for `isort`, `black`, and `flake8`.
5.  **Verification:** Run all automated tools (`isort`, `black`, `mypy`, `pytest`) to ensure the refactored codebase is clean, consistent, and fully functional.