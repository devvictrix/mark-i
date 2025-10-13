# Profile Organization Design Document

## Overview

This design outlines the reorganization of MARK-I automation profile JSON files from a flat structure in the storage directory to a well-organized hierarchical structure within storage/profiles/. The design focuses on logical categorization, consistent naming conventions, and clear documentation to improve maintainability and discoverability.

## Architecture

### Directory Structure

```
storage/
├── profiles/
│   ├── README.md                    # Organization guide and conventions
│   ├── messaging/                   # Communication app profiles
│   │   ├── line-messenger-basic.json
│   │   ├── line-messenger-ai-enhanced.json
│   │   └── line-messenger-gemini-test.json
│   ├── productivity/                # Office and productivity app profiles
│   │   └── notepad-automator.json
│   ├── gaming/                      # Game automation profiles
│   │   └── simple-game-helper.json
│   ├── examples/                    # Template and example profiles
│   │   └── basic-example-profile.json
│   └── experimental/                # POC and test profiles
│       └── poc-profile.json
├── cache/
├── images/
├── knowledge/
├── logs/
├── os/
└── templates/
```

## Components and Interfaces

### Profile Categorization System

**Categories:**
- **messaging/**: Profiles for communication applications (LINE, Discord, Slack, etc.)
- **productivity/**: Profiles for office and productivity tools (Notepad, Word, Excel, etc.)
- **gaming/**: Profiles for game automation and assistance
- **examples/**: Template profiles and basic examples for learning
- **experimental/**: Proof-of-concept and test profiles

### Naming Convention System

**Format:** `{application}-{purpose}-{variant}.json`

**Examples:**
- `line-messenger-basic.json` - Basic LINE messenger automation
- `line-messenger-ai-enhanced.json` - AI-powered LINE automation
- `notepad-automator.json` - Notepad automation profile
- `basic-example-profile.json` - Basic example for learning

**Rules:**
- Use kebab-case (lowercase with hyphens)
- Include application name as prefix
- Add descriptive purpose
- Use variant suffixes for similar profiles (-basic, -advanced, -ai-enhanced, -test)

## Data Models

### Profile File Mapping

| Current File | New Location | New Name | Category |
|-------------|--------------|----------|----------|
| `example_profile.json` | `storage/profiles/examples/` | `basic-example-profile.json` | examples |
| `line_messenger_abc.json` | `storage/profiles/messaging/` | `line-messenger-basic.json` | messaging |
| `line_wife_message_ai.json` | `storage/profiles/messaging/` | `line-messenger-ai-enhanced.json` | messaging |
| `line_wife_message_ai_gemini_test.json` | `storage/profiles/messaging/` | `line-messenger-gemini-test.json` | messaging |
| `notepad_automator.json` | `storage/profiles/productivity/` | `notepad-automator.json` | productivity |
| `simple_game_helper.json` | `storage/profiles/gaming/` | `simple-game-helper.json` | gaming |
| `poc.json` | `storage/profiles/experimental/` | `poc-profile.json` | experimental |

### Profile Description Updates

Each moved profile will have its `profile_description` field updated to reflect:
1. The new organized location
2. Clearer purpose description
3. Category context

## Error Handling

### File Operation Safety
- Create backup of original files before moving
- Validate JSON structure after each move operation
- Rollback mechanism if any operation fails
- Verify all files are successfully moved before cleanup

### Validation Checks
- Ensure all JSON files are valid after renaming
- Verify no duplicate filenames in target directories
- Confirm all required directories are created
- Check that no files are lost during the move operation

## Testing Strategy

### Validation Tests
1. **File Integrity**: Verify all JSON files remain valid after move operations
2. **Completeness**: Ensure all original files are accounted for in new structure
3. **Naming Consistency**: Validate all files follow the new naming convention
4. **Directory Structure**: Confirm all required directories and README files are created

### Manual Verification
1. Visual inspection of new directory structure
2. Spot-check profile descriptions for accuracy
3. Verify README documentation is comprehensive
4. Test that profiles can still be loaded by the application

## Implementation Approach

### Phase 1: Directory Setup
1. Create storage/profiles/ directory structure
2. Create category subdirectories
3. Generate README.md with organization guidelines

### Phase 2: File Migration
1. Copy files to new locations with new names
2. Update profile_description fields
3. Validate JSON integrity

### Phase 3: Cleanup and Documentation
1. Remove original files from storage/ root
2. Update any references in code or documentation
3. Final validation of complete structure