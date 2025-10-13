# MARK-I Context Storage

This directory contains the enhanced system context data collected by MARK-I's context awareness system.

## Directory Structure

### current/
Contains the most recent context data from all collectors:
- `context.json` - Complete current system context
- Individual collector data files (hardware.json, applications.json, etc.)

### history/
Historical context data organized by date:
- `YYYY-MM-DD/` - Daily context snapshots
- `usage_patterns.json` - Analyzed usage patterns over time

### cache/
Cached expensive operations and computed data:
- `app_discovery.json` - Cached application discovery results
- `performance_baseline.json` - System performance baselines
- Individual collector cache files

## Data Refresh Intervals

Different types of context data are refreshed at different intervals:

- **Static Data** (hardware specs): 24 hours
- **Semi-Static Data** (installed apps): 6 hours  
- **Dynamic Data** (running processes, performance): 30 seconds
- **Real-time Data** (active windows, network): 5 seconds

## Privacy and Security

- Sensitive information is filtered before storage
- Personal file paths are anonymized
- Access to context data is logged for audit purposes
- Historical data is automatically cleaned up after 7 days (configurable)

## File Formats

All context data is stored in JSON format with the following structure:

```json
{
  "collection_timestamp": "2025-10-13T11:00:00Z",
  "collectors_count": 5,
  "context": {
    "context_hardware": { ... },
    "context_applications": { ... },
    "context_network": { ... },
    "context_ui": { ... },
    "context_user_environment": { ... }
  }
}
```

Each collector's data includes metadata:

```json
{
  "_metadata": {
    "collector": "Hardware Collector",
    "collected_at": "2025-10-13T11:00:00Z",
    "refresh_interval": 86400,
    "is_expensive": false
  }
}
```