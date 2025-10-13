# MARK-I Automation Profiles

This directory contains organized automation profiles for the MARK-I AI assistant. Each profile defines specific automation behaviors, rules, and configurations for different applications and use cases.

## Directory Structure

```
profiles/
├── README.md                    # This documentation file
├── messaging/                   # Communication app profiles
├── productivity/                # Office and productivity app profiles
├── gaming/                      # Game automation profiles
├── examples/                    # Template and example profiles
└── experimental/                # POC and test profiles
```

## Categories

### messaging/
Profiles for communication and messaging applications:
- LINE messenger automation
- Discord bot interactions
- Slack workflow automation
- Email client automation

### productivity/
Profiles for office and productivity tools:
- Text editor automation (Notepad, VS Code, etc.)
- Document processing (Word, Excel, etc.)
- File management automation
- System utility automation

### gaming/
Profiles for game automation and assistance:
- Game helper utilities
- Automated gameplay actions
- Game state monitoring
- Achievement tracking

### examples/
Template profiles and basic examples for learning:
- Basic automation examples
- Template profiles for new users
- Tutorial and demonstration profiles
- Best practice examples

### experimental/
Proof-of-concept and test profiles:
- Development and testing profiles
- Experimental features
- POC implementations
- Debug and diagnostic profiles

## Naming Conventions

All profile files follow a consistent naming pattern:

**Format:** `{application}-{purpose}-{variant}.json`

**Rules:**
- Use kebab-case (lowercase with hyphens)
- Include application name as prefix
- Add descriptive purpose
- Use variant suffixes for similar profiles

**Examples:**
- `line-messenger-basic.json` - Basic LINE messenger automation
- `line-messenger-ai-enhanced.json` - AI-powered LINE automation
- `notepad-automator.json` - Notepad automation profile
- `basic-example-profile.json` - Basic example for learning

**Variant Suffixes:**
- `-basic` - Simple, straightforward automation
- `-advanced` - Complex automation with multiple features
- `-ai-enhanced` - Profiles using AI/ML capabilities
- `-test` - Testing and experimental versions
- `-gemini` - Profiles specifically using Gemini AI

## Profile Structure

Each profile JSON file contains:

```json
{
    "profile_description": "Clear description of the profile's purpose",
    "settings": {
        "monitoring_interval_seconds": 1.0,
        "analysis_dominant_colors_k": 3,
        "gemini_default_model_name": "gemini-1.5-flash-latest"
    },
    "regions": [
        {
            "name": "region_name",
            "x": 0, "y": 0, "width": 100, "height": 100,
            "comment": "Description of what this region monitors"
        }
    ],
    "templates": [
        {
            "name": "template_name",
            "filename": "template_file.png",
            "comment": "Description of the template image"
        }
    ],
    "rules": [
        {
            "name": "rule_name",
            "region": "region_name",
            "condition": { "type": "condition_type" },
            "action": { "type": "action_type" }
        }
    ]
}
```

## Creating New Profiles

When creating new automation profiles:

1. **Choose the appropriate category** based on the target application
2. **Follow the naming convention** for consistency
3. **Include a clear profile_description** explaining the purpose
4. **Document regions and templates** with helpful comments
5. **Test thoroughly** before moving from experimental to production categories

## Best Practices

- **Start with examples/**: Review example profiles before creating new ones
- **Use experimental/ for testing**: Test new profiles in experimental before moving to production categories
- **Keep descriptions current**: Update profile_description when modifying profiles
- **Comment your regions**: Always include helpful comments for regions and templates
- **Version control**: Consider using variant suffixes when creating multiple versions

## Migration Notes

This organized structure was created from the original flat storage directory. Original files were:
- `example_profile.json` → `examples/basic-example-profile.json`
- `line_messenger_abc.json` → `messaging/line-messenger-basic.json`
- `line_wife_message_ai.json` → `messaging/line-messenger-ai-enhanced.json`
- `line_wife_message_ai_gemini_test.json` → `messaging/line-messenger-gemini-test.json`
- `notepad_automator.json` → `productivity/notepad-automator.json`
- `simple_game_helper.json` → `gaming/simple-game-helper.json`
- `poc.json` → `experimental/poc-profile.json`