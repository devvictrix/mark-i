# ADR-014: Strategic Executor and Knowledge Base Architecture

- **Status:** Proposed
- **Date Decision Made:** 2025-08-30
- **Deciders:** DevLead

## Context and Problem Statement

Mark-I v7.0.0's Interactive Command Mode is powerful but fundamentally tactical. It executes a single, user-provided command against the current screen state. It lacks the ability to perform multi-stage tasks or to understand personalized context (e.g., knowing that "my wife" refers to a specific contact named "Big Boss"). If a command requires an application to be opened first, the current system will fail.

To achieve a higher level of intelligence and handle more complex, multi-step user commands, we need a new architecture that introduces:
1.  **Strategic Planning:** A higher-level "brain" that can decompose a complex user goal into a sequence of distinct, tactical sub-goals.
2.  **Persistent Knowledge:** A mechanism for the AI to store and retrieve user-specific information, such as aliases for people, applications, and files.

## Considered Options for Knowledge Storage

1.  **Dedicated Database (e.g., SQLite, PostgreSQL):**
    - **Description:** Store user knowledge in a structured database.
    - **Pros:** Scalable to very large datasets, supports complex queries and relations.
    - **Cons:** Massive increase in complexity for both the user (setup, maintenance) and the developer (dependencies, schema management, ORMs/SQL). It is significant over-engineering for the project's current and medium-term needs.

2.  **Simple JSON File (`knowledge_base.json`) (Chosen):**
    - **Description:** Store all user-specific knowledge in a single, user-editable JSON file.
    - **Pros:**
        -   **User-Friendly:** Easily understood, edited, and backed up with any text editor. Zero setup for the user.
        -   **Developer Simplicity:** Utilizes Python's built-in `json` library with no new dependencies.
        -   **Portability:** The entire knowledge base is a single file that can be version-controlled and shared.
        -   **Sufficient Performance:** The file will be small enough to be loaded into memory instantly at the start of a command, making read performance excellent.
    - **Cons:** Not suitable for gigabyte-scale data or high-transaction scenarios (which are not requirements for this feature).

## Decision Outcome

**Chosen Option:** The architecture for v8.0.0 will consist of two new core components: a **`StrategicExecutor`** and a **`KnowledgeBase`** class that manages a simple, user-maintained **`knowledge_base.json`** file.

**Justification:**

This hierarchical AI architecture (a strategic planner orchestrating a tactical executor) combined with a simple, file-based knowledge store is the optimal solution.

-   **Separation of Concerns:** The `StrategicExecutor` is responsible for *what* needs to be done (the high-level plan), while the existing `GeminiDecisionModule` is responsible for *how* to do each specific step on the screen. This is a clean and powerful separation.
-   **Right Tool for the Job:** Using a JSON file for the knowledge base prioritizes user simplicity and developer efficiency, which are core tenets of the project. It avoids the unnecessary complexity of a database for a configuration-like task.
-   **Extensibility:** This architecture is highly extensible. The `knowledge_base.json` schema can be expanded in the future (e.g., with visual aliases, workflow recipes) without changing the core engine logic. The `StrategicExecutor` itself is the foundation upon which more advanced capabilities, like the v9.0.0 Proactive Knowledge Discovery, can be built.

## High-Level Implementation Plan

1.  **Create `mark_i/knowledge/knowledge_base.py`:**
    -   Define a `KnowledgeBase` class.
    -   It will be responsible for loading, accessing, and parsing the `knowledge_base.json` file from the project root.
    -   It will provide methods to resolve aliases and retrieve specific knowledge categories (e.g., `get_alias("my wife")`, `get_user_data("my_email")`).

2.  **Create `mark_i/execution/strategic_executor.py`:**
    -   Define a `StrategicExecutor` class.
    -   It will be initialized with the `KnowledgeBase` and all relevant engines (`GeminiAnalyzer`, `GeminiDecisionModule`).
    -   It will have a primary public method, `execute_command(command: str, screenshot: np.ndarray)`.

3.  **Implement the Strategic Execution Flow:**
    -   `execute_command` will first use the `KnowledgeBase` to pre-process the user's command string, substituting known aliases.
    -   It will then construct a detailed prompt for a powerful AI model (e.g., Gemini 1.5 Pro), injecting the *entire knowledge base* as context along with the processed command. The prompt will ask the AI to generate a high-level, multi-step plan.
    -   It will parse the AI's response to get this list of sub-goals.
    -   It will loop through the sub-goals, passing each one as a new, tactical command to the existing `GeminiDecisionModule.execute_nlu_task()`. It will take fresh screenshots betwee