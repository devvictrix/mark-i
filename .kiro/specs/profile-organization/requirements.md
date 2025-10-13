# Requirements Document

## Introduction

The MARK-I project currently has profile JSON files scattered in the storage directory without proper organization. These profiles define automation behaviors for different applications and use cases, but they lack a clear categorization system and proper directory structure. This feature will reorganize these profiles into a logical hierarchy with improved naming conventions and better categorization.

## Requirements

### Requirement 1

**User Story:** As a developer, I want profile JSON files organized in a clear directory structure within storage, so that I can easily find and manage automation profiles for different applications and use cases.

#### Acceptance Criteria

1. WHEN the system is reorganized THEN all profile JSON files SHALL be moved from storage/ root to organized subdirectories within storage/profiles/
2. WHEN profiles are categorized THEN they SHALL be organized into subdirectories based on application type (messaging, productivity, gaming, examples)
3. WHEN profiles are renamed THEN they SHALL follow a consistent naming convention using kebab-case format
4. WHEN the directory structure is created THEN it SHALL include appropriate README files explaining the organization

### Requirement 2

**User Story:** As a developer, I want profile files to have descriptive and consistent names, so that I can quickly identify their purpose without opening the files.

#### Acceptance Criteria

1. WHEN profile files are renamed THEN they SHALL use descriptive names that clearly indicate their purpose
2. WHEN naming conventions are applied THEN they SHALL use kebab-case format (e.g., line-messenger-basic.json)
3. WHEN similar profiles exist THEN they SHALL be differentiated with appropriate suffixes (e.g., -basic, -advanced, -ai-enhanced)
4. WHEN profiles are renamed THEN the profile_description field SHALL be updated to match the new naming

### Requirement 3

**User Story:** As a developer, I want profiles categorized by application type, so that I can maintain related automation profiles together.

#### Acceptance Criteria

1. WHEN profiles are categorized THEN messaging app profiles SHALL be placed in storage/profiles/messaging/ directory
2. WHEN profiles are categorized THEN productivity app profiles SHALL be placed in storage/profiles/productivity/ directory  
3. WHEN profiles are categorized THEN gaming profiles SHALL be placed in storage/profiles/gaming/ directory
4. WHEN profiles are categorized THEN example/template profiles SHALL be placed in storage/profiles/examples/ directory
5. WHEN profiles are categorized THEN experimental/POC profiles SHALL be placed in storage/profiles/experimental/ directory

### Requirement 4

**User Story:** As a developer, I want the profile directory structure documented, so that I understand how to organize new profiles in the future.

#### Acceptance Criteria

1. WHEN the reorganization is complete THEN a storage/profiles/README.md file SHALL be created explaining the directory structure
2. WHEN documentation is created THEN it SHALL include naming conventions and categorization guidelines
3. WHEN documentation is created THEN it SHALL provide examples of proper profile organization
4. WHEN documentation is created THEN it SHALL explain the purpose of each category subdirectory