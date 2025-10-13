# Technology Stack

## Core Technologies

- **Language**: Python 3.9+
- **AI/ML**: Google Gemini API (`gemini-1.5-pro`, `gemini-1.5-flash`)
- **GUI Framework**: CustomTkinter
- **Visual Perception**: Pillow, OpenCV, PyAutoGUI
- **UI Automation**: PyAutoGUI
- **Configuration**: JSON, python-dotenv
- **Concurrency**: threading, queue

## Development Tools

- **Testing**: pytest
- **Code Formatting**: black (line length: 199)
- **Linting**: flake8 (max line length: 199, ignores E203, W503)
- **Type Checking**: mypy (cache present)

## Key Dependencies

```
customtkinter
Pillow
opencv-python
numpy
pytesseract
pyautogui
google-generativeai
python-dotenv
pywinauto  # Windows-specific OS-level event hooks
```

## Common Commands

### Running the Application
```bash
# Run as module (recommended)
python -m mark_i

# Launch GUI (default)
python -m mark_i

# Run specific commands
python -m mark_i [command] [options]
```

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .

# Lint code
flake8

# Type checking
mypy mark_i/
```

## Configuration

- Environment variables loaded via python-dotenv
- JSON-based configuration files for profiles and knowledge base
- Logging configured via core.logging_setup module
- EditorConfig enforces 2-space indentation for most files