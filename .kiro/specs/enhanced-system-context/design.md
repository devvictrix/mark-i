# Enhanced System Context Design Document

## Overview

This design extends MARK-I's current OS detection capabilities into a comprehensive system context awareness system. The enhanced system will collect, cache, and provide rich environmental data including hardware specifications, installed applications, running processes, network status, user behavior patterns, and UI context. This contextual intelligence will enable the AI to make more informed decisions, optimize performance, and provide proactive assistance.

## Architecture

### System Context Collection Framework

```
mark_i/
├── context/                     # New context collection system
│   ├── __init__.py
│   ├── context_manager.py       # Main orchestrator
│   ├── collectors/              # Individual data collectors
│   │   ├── __init__.py
│   │   ├── hardware_collector.py
│   │   ├── application_collector.py
│   │   ├── network_collector.py
│   │   ├── ui_collector.py
│   │   └── user_collector.py
│   ├── cache/                   # Context caching system
│   │   ├── __init__.py
│   │   ├── cache_manager.py
│   │   └── refresh_scheduler.py
│   └── analyzers/               # Context analysis and patterns
│       ├── __init__.py
│       ├── usage_analyzer.py
│       └── pattern_detector.py
```

### Enhanced Storage Structure

```
storage/
├── context/                     # Enhanced context storage
│   ├── current/                 # Current system state
│   │   ├── hardware.json
│   │   ├── applications.json
│   │   ├── network.json
│   │   ├── ui_context.json
│   │   └── user_environment.json
│   ├── history/                 # Historical context data
│   │   ├── 2025-10-13/
│   │   └── usage_patterns.json
│   └── cache/                   # Cached expensive operations
│       ├── app_discovery.json
│       └── performance_baseline.json
├── os/                          # Existing OS detection (enhanced)
└── profiles/                    # Existing profiles
```

## Components and Interfaces

### 1. Hardware Context Collector

**Purpose:** Gather comprehensive hardware and performance information

**Data Structure:**
```json
{
  "hardware": {
    "cpu": {
      "model": "Intel Core i7-12700K",
      "cores_physical": 12,
      "cores_logical": 20,
      "frequency_current": 3600,
      "frequency_max": 5000,
      "usage_percent": 15.2,
      "temperature": 45
    },
    "memory": {
      "total_gb": 32.0,
      "available_gb": 24.1,
      "used_gb": 7.9,
      "usage_percent": 24.7,
      "swap_total_gb": 8.0,
      "swap_used_gb": 0.0
    },
    "gpu": [
      {
        "name": "NVIDIA GeForce RTX 4080",
        "memory_gb": 16,
        "driver_version": "535.183.01",
        "usage_percent": 5
      },
      {
        "name": "Intel UHD Graphics 770",
        "type": "integrated",
        "usage_percent": 0
      }
    ],
    "storage": [
      {
        "device": "/dev/nvme0n1",
        "mount_point": "/",
        "total_gb": 1000,
        "used_gb": 450,
        "free_gb": 550,
        "filesystem": "ext4"
      }
    ],
    "displays": [
      {
        "name": "DP-1",
        "resolution": "3440x1440",
        "refresh_rate": 144,
        "scaling_factor": 1.25,
        "primary": true,
        "position": {"x": 0, "y": 0}
      }
    ]
  }
}
```

### 2. Application Context Collector

**Purpose:** Discover installed applications and track running processes

**Data Structure:**
```json
{
  "applications": {
    "installed": {
      "browsers": [
        {"name": "firefox", "version": "119.0", "path": "/usr/bin/firefox"},
        {"name": "google-chrome", "version": "119.0.6045.105", "path": "/usr/bin/google-chrome"}
      ],
      "editors": [
        {"name": "code", "version": "1.84.2", "path": "/usr/bin/code"},
        {"name": "vim", "version": "9.0", "path": "/usr/bin/vim"}
      ],
      "terminals": [
        {"name": "gnome-terminal", "version": "3.48.2", "path": "/usr/bin/gnome-terminal"}
      ],
      "communication": [
        {"name": "discord", "version": "0.0.32", "path": "/opt/discord/Discord"}
      ],
      "development": [
        {"name": "docker", "version": "24.0.7", "path": "/usr/bin/docker"},
        {"name": "git", "version": "2.42.0", "path": "/usr/bin/git"}
      ]
    },
    "running": [
      {
        "pid": 12345,
        "name": "firefox",
        "command": "firefox --new-instance",
        "cpu_percent": 2.1,
        "memory_mb": 512,
        "start_time": "2025-10-13T10:30:00Z"
      }
    ],
    "usage_stats": {
      "firefox": {"total_time_hours": 45.2, "launches_today": 3, "last_used": "2025-10-13T11:00:00Z"},
      "code": {"total_time_hours": 120.5, "launches_today": 1, "last_used": "2025-10-13T09:15:00Z"}
    }
  }
}
```

### 3. UI Context Collector

**Purpose:** Gather window manager and desktop environment information

**Data Structure:**
```json
{
  "ui_context": {
    "desktop_environment": {
      "name": "GNOME",
      "version": "45.0",
      "session_type": "wayland"
    },
    "window_manager": {
      "name": "mutter",
      "version": "45.0",
      "compositor": "wayland"
    },
    "theme": {
      "gtk_theme": "Adwaita-dark",
      "icon_theme": "Adwaita",
      "cursor_theme": "Adwaita"
    },
    "workspaces": {
      "total": 4,
      "current": 1,
      "names": ["Main", "Development", "Communication", "Media"]
    },
    "active_windows": [
      {
        "title": "Terminal - devvictrix@mark-i",
        "class": "gnome-terminal-server",
        "pid": 12345,
        "workspace": 1,
        "geometry": {"x": 100, "y": 100, "width": 1200, "height": 800},
        "focused": true,
        "minimized": false
      }
    ],
    "input_devices": {
      "keyboards": [{"name": "AT Translated Set 2 keyboard", "layout": "us"}],
      "mice": [{"name": "Logitech MX Master 3", "buttons": 7}]
    }
  }
}
```

### 4. Network Context Collector

**Purpose:** Monitor network connectivity and configuration

**Data Structure:**
```json
{
  "network": {
    "interfaces": [
      {
        "name": "wlan0",
        "type": "wireless",
        "status": "up",
        "ip_address": "192.168.1.100",
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "speed_mbps": 1000,
        "ssid": "HomeNetwork-5G"
      }
    ],
    "connectivity": {
      "internet_available": true,
      "dns_servers": ["8.8.8.8", "1.1.1.1"],
      "gateway": "192.168.1.1",
      "public_ip": "203.0.113.1",
      "connection_quality": "excellent",
      "latency_ms": 12
    },
    "vpn": {
      "active": false,
      "provider": null,
      "server_location": null
    },
    "firewall": {
      "enabled": true,
      "type": "ufw",
      "status": "active"
    }
  }
}
```

### 5. User Environment Collector

**Purpose:** Gather user-specific environment and behavior data

**Data Structure:**
```json
{
  "user_environment": {
    "profile": {
      "username": "devvictrix",
      "uid": 1000,
      "gid": 1000,
      "home_directory": "/home/devvictrix",
      "shell": "/bin/bash",
      "groups": ["sudo", "docker", "audio", "video"]
    },
    "locale": {
      "language": "en_US.UTF-8",
      "timezone": "Asia/Bangkok",
      "keyboard_layout": "us",
      "date_format": "YYYY-MM-DD",
      "time_format": "24h"
    },
    "working_context": {
      "current_directory": "/home/devvictrix/projects/mark-i",
      "recent_directories": [
        "/home/devvictrix/projects/mark-i",
        "/home/devvictrix/Documents",
        "/home/devvictrix/Downloads"
      ],
      "active_projects": [
        {"path": "/home/devvictrix/projects/mark-i", "type": "python", "last_accessed": "2025-10-13T11:00:00Z"}
      ]
    },
    "behavior_patterns": {
      "most_active_hours": [9, 10, 11, 14, 15, 16],
      "preferred_applications": ["code", "firefox", "gnome-terminal"],
      "workflow_patterns": {
        "development": ["code", "gnome-terminal", "firefox"],
        "research": ["firefox", "obsidian", "zotero"]
      }
    }
  }
}
```

## Data Models

### Context Manager

**Core Class:** `ContextManager`
- Orchestrates all collectors
- Manages refresh schedules
- Provides unified API for context access
- Handles caching and performance optimization

### Collector Interface

```python
class BaseCollector:
    def collect(self) -> Dict[str, Any]:
        """Collect context data"""
        pass
    
    def get_refresh_interval(self) -> int:
        """Return refresh interval in seconds"""
        pass
    
    def is_expensive(self) -> bool:
        """Return True if collection is resource-intensive"""
        pass
```

### Cache Strategy

- **Static Data** (hardware specs): Refresh every 24 hours
- **Semi-Static Data** (installed apps): Refresh every 6 hours
- **Dynamic Data** (running processes, performance): Refresh every 30 seconds
- **Real-time Data** (active windows, network): Refresh every 5 seconds

## Error Handling

### Graceful Degradation
- If hardware detection fails, use basic system info
- If application discovery fails, maintain cached list
- If network detection fails, assume offline mode
- Always provide partial context rather than complete failure

### Privacy Protection
- Filter sensitive information (passwords, tokens, personal files)
- Anonymize user-specific paths when appropriate
- Provide opt-out mechanisms for sensitive data collection
- Log access to context data for audit purposes

## Testing Strategy

### Unit Tests
- Test each collector independently
- Mock system calls and external dependencies
- Validate data structure compliance
- Test error handling and edge cases

### Integration Tests
- Test context manager orchestration
- Validate caching behavior
- Test refresh scheduling
- Verify performance impact

### Performance Tests
- Measure collection time for each collector
- Test memory usage during context gathering
- Validate cache effectiveness
- Monitor system impact during continuous operation

## Implementation Approach

### Phase 1: Core Infrastructure
1. Create context collection framework
2. Implement base collector interface
3. Set up caching and storage system
4. Create context manager orchestrator

### Phase 2: Basic Collectors
1. Implement hardware collector
2. Implement application collector
3. Implement network collector
4. Basic integration and testing

### Phase 3: Advanced Features
1. Implement UI context collector
2. Implement user environment collector
3. Add usage pattern analysis
4. Performance optimization

### Phase 4: Intelligence Integration
1. Integrate with existing MARK-I components
2. Enhance decision-making with context data
3. Add proactive suggestions based on context
4. Performance monitoring and optimization