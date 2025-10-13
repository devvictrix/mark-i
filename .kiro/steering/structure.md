# Project Structure

## Package Organization

The project follows a hierarchical module structure under the `mark_i/` package:

```
mark_i/
├── __main__.py          # Entry point - handles CLI parsing and app initialization
├── main_controller.py   # Main application controller
├── agency/              # Proactive strategic reasoning (Agency Core)
├── agent/               # Tactical execution (Agent Core with ReAct loops)
│   ├── agent_core.py
│   ├── toolbelt.py      # Tool management and execution
│   ├── tools/           # Individual tool implementations
│   └── world_model.py   # Entity-graph world representation
├── autonomy/            # Autonomous operation engine
├── core/                # Foundational components
│   ├── app_config.py
│   ├── config_manager.py
│   ├── env_validator.py
│   └── logging_setup.py
├── engines/             # Specialized processing engines
│   ├── gemini_analyzer.py
│   ├── gemini_decision_module.py
│   ├── primitive_executors.py
│   └── [other engines]
├── execution/           # Strategic execution and planning
├── foresight/           # Simulation and prediction
├── generation/          # Profile and strategy generation
├── knowledge/           # Knowledge base and discovery
├── perception/          # Multi-modal environmental sensing
├── symbiosis/           # Human-AI interface components
└── ui/                  # User interface components
    ├── cli.py
    └── gui/             # CustomTkinter GUI components
```

## Key Architectural Patterns

### Hierarchical AI Architecture
- **Agency Core**: Strategic, proactive reasoning
- **Agent Core**: Tactical execution with ReAct patterns
- **Engines**: Specialized processing (Gemini, rules, analysis)

### Module Conventions
- Each major component has its own directory
- `__init__.py` files for proper package structure
- Core utilities in `core/` package
- UI separated into CLI and GUI components

### Configuration & Data
- `profiles/` - JSON automation profiles and templates
- `docs/` - Comprehensive documentation including ADRs
- `tests/` - Test suite organized by module structure

### Import Patterns
- Use relative imports within the package
- Run as module: `python -m mark_i`
- Fallback import handling in `__main__.py`

## File Naming Conventions
- Snake_case for Python files
- Descriptive module names reflecting functionality
- Engine/Core/Manager suffixes for major components
- Tool classes in dedicated `tools/` subdirectory