"""
Environment Monitor for MARK-I

This module provides comprehensive environment monitoring capabilities including
system state tracking, application relationship mapping, and environmental
change detection for intelligent system adaptation.
"""

import logging
import threading
import time
import os
import psutil
import platform
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import json
import hashlib

from mark_i.core.base_component import ProcessingComponent
from mark_i.core.architecture_config import ComponentConfig
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(APP_ROOT_LOGGER_NAME + ".context.environment_monitor")


class MonitoringScope(Enum):
    """Scope of environment monitoring."""

    MINIMAL = "minimal"  # Basic system metrics only
    STANDARD = "standard"  # System + application monitoring
    COMPREHENSIVE = "comprehensive"  # Full environment awareness


class SystemHealthStatus(Enum):
    """System health status levels."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """Comprehensive system metrics snapshot."""

    timestamp: datetime
    cpu_usage: float
    cpu_frequency: float
    cpu_temperature: Optional[float]
    memory_total: int
    memory_used: int
    memory_percent: float
    disk_total: int
    disk_used: int
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    network_packets_sent: int
    network_packets_recv: int
    boot_time: datetime
    uptime_seconds: float
    load_average: Tuple[float, float, float]  # 1min, 5min, 15min
    process_count: int
    thread_count: int


@dataclass
class ApplicationInfo:
    """Detailed application information."""

    app_id: str
    name: str
    pid: int
    ppid: int
    status: str
    create_time: datetime
    cpu_percent: float
    memory_percent: float
    memory_rss: int
    memory_vms: int
    num_threads: int
    num_fds: int
    connections: List[Dict[str, Any]]
    open_files: List[str]
    cmdline: List[str]
    exe: str
    cwd: str
    username: str
    is_running: bool
    children: List[int]


@dataclass
class ApplicationRelationship:
    """Relationship between applications."""

    app1_id: str
    app2_id: str
    relationship_type: str  # parent_child, communication, resource_sharing, co_occurrence
    strength: float  # 0.0 to 1.0
    evidence: List[str]
    first_observed: datetime
    last_observed: datetime
    frequency: int


@dataclass
class EnvironmentSnapshot:
    """Complete environment snapshot."""

    timestamp: datetime
    system_metrics: SystemMetrics
    applications: Dict[str, ApplicationInfo]
    relationships: List[ApplicationRelationship]
    network_connections: List[Dict[str, Any]]
    system_events: List[Dict[str, Any]]
    environment_hash: str


class EnvironmentMonitor(ProcessingComponent):
    """
    Comprehensive environment monitoring for system state tracking,
    application relationship mapping, and environmental change detection.
    """

    def __init__(self, config: ComponentConfig):
        super().__init__("environment_monitor", config)

        # Configuration
        self.monitoring_scope = MonitoringScope(getattr(config, "monitoring_scope", "standard"))
        self.monitoring_interval = getattr(config, "monitoring_interval", 10.0)
        self.relationship_threshold = getattr(config, "relationship_threshold", 0.3)
        self.max_snapshots = getattr(config, "max_snapshots", 1000)
        self.enable_deep_monitoring = getattr(config, "enable_deep_monitoring", True)

        # Monitoring state
        self.monitoring_active = False
        self.current_snapshot: Optional[EnvironmentSnapshot] = None
        self.snapshot_history: deque = deque(maxlen=self.max_snapshots)

        # Application tracking
        self.tracked_applications: Dict[str, ApplicationInfo] = {}
        self.application_relationships: Dict[str, ApplicationRelationship] = {}
        self.application_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # System baseline
        self.baseline_metrics: Optional[SystemMetrics] = None
        self.system_info: Dict[str, Any] = {}

        # Change detection
        self.significant_changes: deque = deque(maxlen=500)
        self.change_thresholds = {"cpu_usage": 20.0, "memory_usage": 15.0, "disk_usage": 10.0, "process_count": 5, "network_activity": 50.0}

        # Threading
        self.monitor_lock = threading.Lock()
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()

        # Statistics
        self.monitoring_cycles = 0
        self.snapshots_captured = 0
        self.relationships_discovered = 0
        self.changes_detected = 0

        # Initialize system information
        self._initialize_system_info()

        logger.info(f"EnvironmentMonitor initialized with {self.monitoring_scope.value} scope")

    def start_monitoring(self) -> bool:
        """Start comprehensive environment monitoring."""
        try:
            if self.monitoring_active:
                logger.warning("Environment monitoring already active")
                return True

            self.monitoring_active = True
            self.stop_monitoring.clear()

            # Capture baseline metrics
            self._capture_baseline_metrics()

            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, name="EnvironmentMonitor", daemon=True)
            self.monitor_thread.start()

            logger.info("Environment monitoring started")
            return True

        except Exception as e:
            logger.error(f"Error starting environment monitoring: {e}")
            return False

    def stop_monitoring(self) -> bool:
        """Stop environment monitoring."""
        try:
            if not self.monitoring_active:
                return True

            self.monitoring_active = False
            self.stop_monitoring.set()

            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=10.0)

            logger.info("Environment monitoring stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping environment monitoring: {e}")
            return False

    def get_current_environment(self) -> Optional[Dict[str, Any]]:
        """Get current comprehensive environment information."""
        try:
            with self.monitor_lock:
                if not self.current_snapshot:
                    return None

                return {
                    "timestamp": self.current_snapshot.timestamp.isoformat(),
                    "system_metrics": self._system_metrics_to_dict(self.current_snapshot.system_metrics),
                    "applications": {app_id: self._application_info_to_dict(app_info) for app_id, app_info in self.current_snapshot.applications.items()},
                    "relationships": [self._relationship_to_dict(rel) for rel in self.current_snapshot.relationships],
                    "system_health": self._assess_system_health().value,
                    "environment_hash": self.current_snapshot.environment_hash,
                }

        except Exception as e:
            logger.error(f"Error getting current environment: {e}")
            return None

    def get_application_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get comprehensive application relationship mapping."""
        try:
            relationships = defaultdict(list)

            for rel in self.application_relationships.values():
                rel_dict = self._relationship_to_dict(rel)
                relationships[rel.app1_id].append(rel_dict)
                relationships[rel.app2_id].append(rel_dict)

            return dict(relationships)

        except Exception as e:
            logger.error(f"Error getting application relationships: {e}")
            return {}

    def detect_environment_changes(self, threshold_multiplier: float = 1.0) -> List[Dict[str, Any]]:
        """Detect significant environmental changes."""
        try:
            if len(self.snapshot_history) < 2:
                return []

            current = self.current_snapshot
            previous = list(self.snapshot_history)[-2]

            if not current or not previous:
                return []

            changes = []

            # System metric changes
            changes.extend(self._detect_system_changes(previous.system_metrics, current.system_metrics, threshold_multiplier))

            # Application changes
            changes.extend(self._detect_application_changes(previous.applications, current.applications))

            # Relationship changes
            changes.extend(self._detect_relationship_changes(previous.relationships, current.relationships))

            # Store significant changes
            for change in changes:
                if change.get("significance", 0) > 0.3:
                    self.significant_changes.append(change)
                    self.changes_detected += 1

            return changes

        except Exception as e:
            logger.error(f"Error detecting environment changes: {e}")
            return []

    def analyze_application_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze patterns in application behavior."""
        try:
            patterns = {}

            for app_id, app_info in self.tracked_applications.items():
                pattern_data = self.application_patterns.get(app_id, [])

                if len(pattern_data) < 10:  # Need sufficient data
                    continue

                # Analyze resource usage patterns
                cpu_values = [data.get("cpu_percent", 0) for data in pattern_data]
                memory_values = [data.get("memory_percent", 0) for data in pattern_data]

                patterns[app_id] = {
                    "resource_usage": {
                        "cpu_avg": sum(cpu_values) / len(cpu_values),
                        "cpu_max": max(cpu_values),
                        "cpu_min": min(cpu_values),
                        "memory_avg": sum(memory_values) / len(memory_values),
                        "memory_max": max(memory_values),
                        "memory_min": min(memory_values),
                    },
                    "activity_pattern": self._analyze_activity_pattern(pattern_data),
                    "stability": self._calculate_stability_score(pattern_data),
                    "relationships": self._get_app_relationships(app_id),
                }

            return patterns

        except Exception as e:
            logger.error(f"Error analyzing application patterns: {e}")
            return {}

    def get_system_health_assessment(self) -> Dict[str, Any]:
        """Get comprehensive system health assessment."""
        try:
            if not self.current_snapshot:
                return {"status": "unknown", "error": "No current snapshot available"}

            metrics = self.current_snapshot.system_metrics
            health_status = self._assess_system_health()

            assessment = {
                "overall_status": health_status.value,
                "timestamp": self.current_snapshot.timestamp.isoformat(),
                "metrics": {
                    "cpu_health": self._assess_cpu_health(metrics),
                    "memory_health": self._assess_memory_health(metrics),
                    "disk_health": self._assess_disk_health(metrics),
                    "network_health": self._assess_network_health(metrics),
                    "process_health": self._assess_process_health(metrics),
                },
                "recommendations": self._generate_health_recommendations(health_status, metrics),
                "trends": self._analyze_health_trends(),
            }

            return assessment

        except Exception as e:
            logger.error(f"Error getting system health assessment: {e}")
            return {"status": "error", "error": str(e)}

    def _monitoring_loop(self):
        """Main monitoring loop for environment tracking."""
        logger.info("Environment monitoring loop started")

        while not self.stop_monitoring.is_set():
            try:
                # Capture environment snapshot
                snapshot = self._capture_environment_snapshot()

                if snapshot:
                    with self.monitor_lock:
                        self.current_snapshot = snapshot
                        self.snapshot_history.append(snapshot)
                        self.snapshots_captured += 1

                    # Detect changes
                    changes = self.detect_environment_changes()

                    # Update application patterns
                    self._update_application_patterns(snapshot.applications)

                    # Discover new relationships
                    self._discover_application_relationships(snapshot.applications)

                self.monitoring_cycles += 1

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            # Wait for next monitoring cycle
            self.stop_monitoring.wait(self.monitoring_interval)

        logger.info("Environment monitoring loop stopped")

    def _capture_environment_snapshot(self) -> Optional[EnvironmentSnapshot]:
        """Capture a comprehensive environment snapshot."""
        try:
            timestamp = datetime.now()

            # Capture system metrics
            system_metrics = self._capture_system_metrics()

            # Capture application information
            applications = self._capture_application_info()

            # Get current relationships
            relationships = list(self.application_relationships.values())

            # Capture network connections if deep monitoring enabled
            network_connections = []
            if self.enable_deep_monitoring:
                network_connections = self._capture_network_connections()

            # Generate environment hash
            env_data = {"system": self._system_metrics_to_dict(system_metrics), "apps": list(applications.keys()), "relationships": len(relationships)}
            env_hash = hashlib.md5(json.dumps(env_data, sort_keys=True).encode()).hexdigest()

            snapshot = EnvironmentSnapshot(
                timestamp=timestamp,
                system_metrics=system_metrics,
                applications=applications,
                relationships=relationships,
                network_connections=network_connections,
                system_events=[],  # Could be extended to capture system events
                environment_hash=env_hash,
            )

            return snapshot

        except Exception as e:
            logger.error(f"Error capturing environment snapshot: {e}")
            return None

    def _capture_system_metrics(self) -> SystemMetrics:
        """Capture comprehensive system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_frequency = cpu_freq.current if cpu_freq else 0.0

            # Temperature (if available)
            cpu_temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            cpu_temperature = entries[0].current
                            break
            except (AttributeError, OSError):
                pass

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage("/")

            # Network metrics
            network = psutil.net_io_counters()

            # System info
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = time.time() - psutil.boot_time()

            # Load average (Unix-like systems)
            load_avg = (0.0, 0.0, 0.0)
            try:
                if hasattr(os, "getloadavg"):
                    load_avg = os.getloadavg()
            except (AttributeError, OSError):
                pass

            # Process counts
            process_count = len(psutil.pids())
            thread_count = sum(proc.num_threads() for proc in psutil.process_iter() if proc.is_running())

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_percent,
                cpu_frequency=cpu_frequency,
                cpu_temperature=cpu_temperature,
                memory_total=memory.total,
                memory_used=memory.used,
                memory_percent=memory.percent,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_percent=disk.percent,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                network_packets_sent=network.packets_sent,
                network_packets_recv=network.packets_recv,
                boot_time=boot_time,
                uptime_seconds=uptime,
                load_average=load_avg,
                process_count=process_count,
                thread_count=thread_count,
            )

        except Exception as e:
            logger.error(f"Error capturing system metrics: {e}")
            # Return minimal metrics on error
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=0.0,
                cpu_frequency=0.0,
                cpu_temperature=None,
                memory_total=0,
                memory_used=0,
                memory_percent=0.0,
                disk_total=0,
                disk_used=0,
                disk_percent=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                network_packets_sent=0,
                network_packets_recv=0,
                boot_time=datetime.now(),
                uptime_seconds=0.0,
                load_average=(0.0, 0.0, 0.0),
                process_count=0,
                thread_count=0,
            )

    def _capture_application_info(self) -> Dict[str, ApplicationInfo]:
        """Capture detailed application information."""
        applications = {}

        try:
            for proc in psutil.process_iter():
                try:
                    if not proc.is_running():
                        continue

                    # Get process info
                    proc_info = proc.as_dict(
                        [
                            "pid",
                            "ppid",
                            "name",
                            "status",
                            "create_time",
                            "cpu_percent",
                            "memory_percent",
                            "memory_info",
                            "num_threads",
                            "num_fds",
                            "connections",
                            "open_files",
                            "cmdline",
                            "exe",
                            "cwd",
                            "username",
                        ]
                    )

                    app_id = f"{proc_info['name']}_{proc_info['pid']}"

                    # Get children
                    children = [child.pid for child in proc.children()]

                    app_info = ApplicationInfo(
                        app_id=app_id,
                        name=proc_info["name"],
                        pid=proc_info["pid"],
                        ppid=proc_info["ppid"],
                        status=proc_info["status"],
                        create_time=datetime.fromtimestamp(proc_info["create_time"]),
                        cpu_percent=proc_info["cpu_percent"] or 0.0,
                        memory_percent=proc_info["memory_percent"] or 0.0,
                        memory_rss=proc_info["memory_info"].rss if proc_info["memory_info"] else 0,
                        memory_vms=proc_info["memory_info"].vms if proc_info["memory_info"] else 0,
                        num_threads=proc_info["num_threads"] or 0,
                        num_fds=proc_info["num_fds"] or 0,
                        connections=[conn._asdict() for conn in (proc_info["connections"] or [])],
                        open_files=[f.path for f in (proc_info["open_files"] or [])],
                        cmdline=proc_info["cmdline"] or [],
                        exe=proc_info["exe"] or "",
                        cwd=proc_info["cwd"] or "",
                        username=proc_info["username"] or "",
                        is_running=True,
                        children=children,
                    )

                    applications[app_id] = app_info

                    # Update tracked applications
                    self.tracked_applications[app_id] = app_info

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    logger.debug(f"Error capturing info for process {proc.pid}: {e}")
                    continue

            return applications

        except Exception as e:
            logger.error(f"Error capturing application info: {e}")
            return {}

    def _capture_network_connections(self) -> List[Dict[str, Any]]:
        """Capture network connection information."""
        try:
            connections = []
            for conn in psutil.net_connections():
                conn_dict = {
                    "fd": conn.fd,
                    "family": conn.family.name if conn.family else None,
                    "type": conn.type.name if conn.type else None,
                    "laddr": conn.laddr._asdict() if conn.laddr else None,
                    "raddr": conn.raddr._asdict() if conn.raddr else None,
                    "status": conn.status,
                    "pid": conn.pid,
                }
                connections.append(conn_dict)

            return connections

        except Exception as e:
            logger.error(f"Error capturing network connections: {e}")
            return []

    def _initialize_system_info(self):
        """Initialize static system information."""
        try:
            self.system_info = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "memory_total": psutil.virtual_memory().total,
                "disk_partitions": [{"device": part.device, "mountpoint": part.mountpoint, "fstype": part.fstype} for part in psutil.disk_partitions()],
            }

        except Exception as e:
            logger.error(f"Error initializing system info: {e}")
            self.system_info = {}

    def _capture_baseline_metrics(self):
        """Capture baseline system metrics for comparison."""
        try:
            self.baseline_metrics = self._capture_system_metrics()
            logger.info("Baseline system metrics captured")

        except Exception as e:
            logger.error(f"Error capturing baseline metrics: {e}")

    def _system_metrics_to_dict(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Convert SystemMetrics to dictionary."""
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_usage": metrics.cpu_usage,
            "cpu_frequency": metrics.cpu_frequency,
            "cpu_temperature": metrics.cpu_temperature,
            "memory_total": metrics.memory_total,
            "memory_used": metrics.memory_used,
            "memory_percent": metrics.memory_percent,
            "disk_total": metrics.disk_total,
            "disk_used": metrics.disk_used,
            "disk_percent": metrics.disk_percent,
            "network_bytes_sent": metrics.network_bytes_sent,
            "network_bytes_recv": metrics.network_bytes_recv,
            "network_packets_sent": metrics.network_packets_sent,
            "network_packets_recv": metrics.network_packets_recv,
            "boot_time": metrics.boot_time.isoformat(),
            "uptime_seconds": metrics.uptime_seconds,
            "load_average": metrics.load_average,
            "process_count": metrics.process_count,
            "thread_count": metrics.thread_count,
        }

    def _application_info_to_dict(self, app_info: ApplicationInfo) -> Dict[str, Any]:
        """Convert ApplicationInfo to dictionary."""
        return {
            "app_id": app_info.app_id,
            "name": app_info.name,
            "pid": app_info.pid,
            "ppid": app_info.ppid,
            "status": app_info.status,
            "create_time": app_info.create_time.isoformat(),
            "cpu_percent": app_info.cpu_percent,
            "memory_percent": app_info.memory_percent,
            "memory_rss": app_info.memory_rss,
            "memory_vms": app_info.memory_vms,
            "num_threads": app_info.num_threads,
            "num_fds": app_info.num_fds,
            "connections": app_info.connections,
            "open_files": app_info.open_files,
            "cmdline": app_info.cmdline,
            "exe": app_info.exe,
            "cwd": app_info.cwd,
            "username": app_info.username,
            "is_running": app_info.is_running,
            "children": app_info.children,
        }

    def _relationship_to_dict(self, rel: ApplicationRelationship) -> Dict[str, Any]:
        """Convert ApplicationRelationship to dictionary."""
        return {
            "app1_id": rel.app1_id,
            "app2_id": rel.app2_id,
            "relationship_type": rel.relationship_type,
            "strength": rel.strength,
            "evidence": rel.evidence,
            "first_observed": rel.first_observed.isoformat(),
            "last_observed": rel.last_observed.isoformat(),
            "frequency": rel.frequency,
        }

    def _assess_system_health(self) -> SystemHealthStatus:
        """Assess overall system health status."""
        if not self.current_snapshot:
            return SystemHealthStatus.FAIR

        metrics = self.current_snapshot.system_metrics

        # Calculate health score based on various metrics
        health_score = 100.0

        # CPU health impact
        if metrics.cpu_usage > 90:
            health_score -= 30
        elif metrics.cpu_usage > 70:
            health_score -= 15
        elif metrics.cpu_usage > 50:
            health_score -= 5

        # Memory health impact
        if metrics.memory_percent > 95:
            health_score -= 25
        elif metrics.memory_percent > 80:
            health_score -= 10
        elif metrics.memory_percent > 60:
            health_score -= 3

        # Disk health impact
        if metrics.disk_percent > 95:
            health_score -= 20
        elif metrics.disk_percent > 85:
            health_score -= 8
        elif metrics.disk_percent > 70:
            health_score -= 2

        # Load average impact (if available)
        if metrics.load_average[0] > psutil.cpu_count() * 2:
            health_score -= 15
        elif metrics.load_average[0] > psutil.cpu_count():
            health_score -= 5

        # Determine status based on score
        if health_score >= 90:
            return SystemHealthStatus.EXCELLENT
        elif health_score >= 75:
            return SystemHealthStatus.GOOD
        elif health_score >= 50:
            return SystemHealthStatus.FAIR
        elif health_score >= 25:
            return SystemHealthStatus.POOR
        else:
            return SystemHealthStatus.CRITICAL

    def _detect_system_changes(self, previous: SystemMetrics, current: SystemMetrics, threshold_multiplier: float) -> List[Dict[str, Any]]:
        """Detect changes in system metrics."""
        changes = []

        # CPU usage change
        cpu_change = abs(current.cpu_usage - previous.cpu_usage)
        if cpu_change > self.change_thresholds["cpu_usage"] * threshold_multiplier:
            changes.append(
                {
                    "type": "system_metric",
                    "metric": "cpu_usage",
                    "change": cpu_change,
                    "previous": previous.cpu_usage,
                    "current": current.cpu_usage,
                    "significance": min(1.0, cpu_change / 100.0),
                    "timestamp": current.timestamp.isoformat(),
                }
            )

        # Memory usage change
        memory_change = abs(current.memory_percent - previous.memory_percent)
        if memory_change > self.change_thresholds["memory_usage"] * threshold_multiplier:
            changes.append(
                {
                    "type": "system_metric",
                    "metric": "memory_usage",
                    "change": memory_change,
                    "previous": previous.memory_percent,
                    "current": current.memory_percent,
                    "significance": min(1.0, memory_change / 100.0),
                    "timestamp": current.timestamp.isoformat(),
                }
            )

        # Disk usage change
        disk_change = abs(current.disk_percent - previous.disk_percent)
        if disk_change > self.change_thresholds["disk_usage"] * threshold_multiplier:
            changes.append(
                {
                    "type": "system_metric",
                    "metric": "disk_usage",
                    "change": disk_change,
                    "previous": previous.disk_percent,
                    "current": current.disk_percent,
                    "significance": min(1.0, disk_change / 100.0),
                    "timestamp": current.timestamp.isoformat(),
                }
            )

        # Process count change
        process_change = abs(current.process_count - previous.process_count)
        if process_change > self.change_thresholds["process_count"] * threshold_multiplier:
            changes.append(
                {
                    "type": "system_metric",
                    "metric": "process_count",
                    "change": process_change,
                    "previous": previous.process_count,
                    "current": current.process_count,
                    "significance": min(1.0, process_change / 50.0),
                    "timestamp": current.timestamp.isoformat(),
                }
            )

        return changes

    def _detect_application_changes(self, previous: Dict[str, ApplicationInfo], current: Dict[str, ApplicationInfo]) -> List[Dict[str, Any]]:
        """Detect changes in application state."""
        changes = []

        # New applications
        new_apps = set(current.keys()) - set(previous.keys())
        for app_id in new_apps:
            changes.append({"type": "application", "change_type": "new_application", "app_id": app_id, "app_name": current[app_id].name, "significance": 0.5, "timestamp": datetime.now().isoformat()})

        # Removed applications
        removed_apps = set(previous.keys()) - set(current.keys())
        for app_id in removed_apps:
            changes.append(
                {"type": "application", "change_type": "removed_application", "app_id": app_id, "app_name": previous[app_id].name, "significance": 0.4, "timestamp": datetime.now().isoformat()}
            )

        # Changed applications
        common_apps = set(current.keys()) & set(previous.keys())
        for app_id in common_apps:
            prev_app = previous[app_id]
            curr_app = current[app_id]

            # CPU usage change
            cpu_change = abs(curr_app.cpu_percent - prev_app.cpu_percent)
            if cpu_change > 10.0:  # 10% CPU change threshold
                changes.append(
                    {
                        "type": "application",
                        "change_type": "cpu_usage_change",
                        "app_id": app_id,
                        "app_name": curr_app.name,
                        "change": cpu_change,
                        "previous": prev_app.cpu_percent,
                        "current": curr_app.cpu_percent,
                        "significance": min(1.0, cpu_change / 50.0),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Memory usage change
            memory_change = abs(curr_app.memory_percent - prev_app.memory_percent)
            if memory_change > 5.0:  # 5% memory change threshold
                changes.append(
                    {
                        "type": "application",
                        "change_type": "memory_usage_change",
                        "app_id": app_id,
                        "app_name": curr_app.name,
                        "change": memory_change,
                        "previous": prev_app.memory_percent,
                        "current": curr_app.memory_percent,
                        "significance": min(1.0, memory_change / 20.0),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return changes

    def _detect_relationship_changes(self, previous: List[ApplicationRelationship], current: List[ApplicationRelationship]) -> List[Dict[str, Any]]:
        """Detect changes in application relationships."""
        changes = []

        prev_rels = {f"{rel.app1_id}_{rel.app2_id}_{rel.relationship_type}": rel for rel in previous}
        curr_rels = {f"{rel.app1_id}_{rel.app2_id}_{rel.relationship_type}": rel for rel in current}

        # New relationships
        new_rel_keys = set(curr_rels.keys()) - set(prev_rels.keys())
        for rel_key in new_rel_keys:
            rel = curr_rels[rel_key]
            changes.append(
                {
                    "type": "relationship",
                    "change_type": "new_relationship",
                    "app1_id": rel.app1_id,
                    "app2_id": rel.app2_id,
                    "relationship_type": rel.relationship_type,
                    "strength": rel.strength,
                    "significance": rel.strength,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Removed relationships
        removed_rel_keys = set(prev_rels.keys()) - set(curr_rels.keys())
        for rel_key in removed_rel_keys:
            rel = prev_rels[rel_key]
            changes.append(
                {
                    "type": "relationship",
                    "change_type": "removed_relationship",
                    "app1_id": rel.app1_id,
                    "app2_id": rel.app2_id,
                    "relationship_type": rel.relationship_type,
                    "strength": rel.strength,
                    "significance": rel.strength * 0.8,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Changed relationship strength
        common_rel_keys = set(curr_rels.keys()) & set(prev_rels.keys())
        for rel_key in common_rel_keys:
            prev_rel = prev_rels[rel_key]
            curr_rel = curr_rels[rel_key]

            strength_change = abs(curr_rel.strength - prev_rel.strength)
            if strength_change > 0.2:  # 20% strength change threshold
                changes.append(
                    {
                        "type": "relationship",
                        "change_type": "strength_change",
                        "app1_id": curr_rel.app1_id,
                        "app2_id": curr_rel.app2_id,
                        "relationship_type": curr_rel.relationship_type,
                        "change": strength_change,
                        "previous": prev_rel.strength,
                        "current": curr_rel.strength,
                        "significance": strength_change,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return changes

    def _update_application_patterns(self, applications: Dict[str, ApplicationInfo]):
        """Update application behavior patterns."""
        try:
            for app_id, app_info in applications.items():
                pattern_data = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": app_info.cpu_percent,
                    "memory_percent": app_info.memory_percent,
                    "num_threads": app_info.num_threads,
                    "num_fds": app_info.num_fds,
                    "status": app_info.status,
                }

                self.application_patterns[app_id].append(pattern_data)

                # Keep pattern history manageable
                if len(self.application_patterns[app_id]) > 100:
                    self.application_patterns[app_id] = self.application_patterns[app_id][-100:]

        except Exception as e:
            logger.error(f"Error updating application patterns: {e}")

    def _discover_application_relationships(self, applications: Dict[str, ApplicationInfo]):
        """Discover relationships between applications."""
        try:
            app_list = list(applications.values())

            for i, app1 in enumerate(app_list):
                for app2 in app_list[i + 1 :]:
                    # Check for parent-child relationship
                    if app1.ppid == app2.pid or app2.ppid == app1.pid:
                        self._add_relationship(app1.app_id, app2.app_id, "parent_child", 0.9, ["process_hierarchy"])

                    # Check for resource sharing patterns
                    if self._check_resource_similarity(app1, app2):
                        self._add_relationship(app1.app_id, app2.app_id, "resource_sharing", 0.6, ["similar_resource_usage"])

                    # Check for communication (shared files, network connections)
                    if self._check_communication_patterns(app1, app2):
                        self._add_relationship(app1.app_id, app2.app_id, "communication", 0.7, ["shared_resources"])

                    # Check for co-occurrence patterns
                    if self._check_co_occurrence(app1.app_id, app2.app_id):
                        self._add_relationship(app1.app_id, app2.app_id, "co_occurrence", 0.5, ["frequently_active_together"])

        except Exception as e:
            logger.error(f"Error discovering application relationships: {e}")

    def _add_relationship(self, app1_id: str, app2_id: str, rel_type: str, strength: float, evidence: List[str]):
        """Add or update an application relationship."""
        rel_key = f"{app1_id}_{app2_id}_{rel_type}"

        if rel_key in self.application_relationships:
            # Update existing relationship
            rel = self.application_relationships[rel_key]
            rel.strength = max(rel.strength, strength)  # Take higher strength
            rel.evidence.extend(evidence)
            rel.evidence = list(set(rel.evidence))  # Remove duplicates
            rel.last_observed = datetime.now()
            rel.frequency += 1
        else:
            # Create new relationship
            self.application_relationships[rel_key] = ApplicationRelationship(
                app1_id=app1_id, app2_id=app2_id, relationship_type=rel_type, strength=strength, evidence=evidence, first_observed=datetime.now(), last_observed=datetime.now(), frequency=1
            )
            self.relationships_discovered += 1

    def _check_resource_similarity(self, app1: ApplicationInfo, app2: ApplicationInfo) -> bool:
        """Check if two applications have similar resource usage patterns."""
        try:
            # Compare CPU usage
            cpu_diff = abs(app1.cpu_percent - app2.cpu_percent)
            if cpu_diff > 20.0:  # Too different
                return False

            # Compare memory usage
            memory_diff = abs(app1.memory_percent - app2.memory_percent)
            if memory_diff > 15.0:  # Too different
                return False

            # Both should be reasonably active
            if app1.cpu_percent < 1.0 and app2.cpu_percent < 1.0:
                return False

            return True

        except Exception as e:
            logger.debug(f"Error checking resource similarity: {e}")
            return False

    def _check_communication_patterns(self, app1: ApplicationInfo, app2: ApplicationInfo) -> bool:
        """Check if two applications have communication patterns."""
        try:
            # Check for shared files
            shared_files = set(app1.open_files) & set(app2.open_files)
            if shared_files:
                return True

            # Check for network connections between them
            app1_connections = {(conn.get("laddr", {}).get("ip", ""), conn.get("laddr", {}).get("port", 0)) for conn in app1.connections}
            app2_connections = {(conn.get("raddr", {}).get("ip", ""), conn.get("raddr", {}).get("port", 0)) for conn in app2.connections}

            if app1_connections & app2_connections:
                return True

            return False

        except Exception as e:
            logger.debug(f"Error checking communication patterns: {e}")
            return False

    def _check_co_occurrence(self, app1_id: str, app2_id: str) -> bool:
        """Check if two applications frequently occur together."""
        try:
            # This is a simplified check - in a real implementation,
            # this would analyze historical data for co-occurrence patterns

            # For now, check if both applications are currently active
            app1_pattern = self.application_patterns.get(app1_id, [])
            app2_pattern = self.application_patterns.get(app2_id, [])

            if len(app1_pattern) < 10 or len(app2_pattern) < 10:
                return False

            # Check recent co-occurrence
            recent_app1 = [p for p in app1_pattern[-20:] if p.get("cpu_percent", 0) > 1.0]
            recent_app2 = [p for p in app2_pattern[-20:] if p.get("cpu_percent", 0) > 1.0]

            # If both have been active recently, consider co-occurrence
            return len(recent_app1) > 5 and len(recent_app2) > 5

        except Exception as e:
            logger.debug(f"Error checking co-occurrence: {e}")
            return False

    def _analyze_activity_pattern(self, pattern_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze activity patterns for an application."""
        try:
            if not pattern_data:
                return {}

            # Calculate activity periods
            active_periods = []
            inactive_periods = []

            for data in pattern_data:
                cpu = data.get("cpu_percent", 0)
                if cpu > 5.0:  # Consider active if CPU > 5%
                    active_periods.append(data)
                else:
                    inactive_periods.append(data)

            return {
                "active_ratio": len(active_periods) / len(pattern_data),
                "average_active_cpu": sum(d.get("cpu_percent", 0) for d in active_periods) / max(1, len(active_periods)),
                "activity_consistency": self._calculate_consistency(pattern_data),
                "peak_activity_times": self._find_peak_times(pattern_data),
            }

        except Exception as e:
            logger.debug(f"Error analyzing activity pattern: {e}")
            return {}

    def _calculate_stability_score(self, pattern_data: List[Dict[str, Any]]) -> float:
        """Calculate stability score for an application."""
        try:
            if len(pattern_data) < 5:
                return 0.5  # Neutral score for insufficient data

            # Calculate variance in CPU usage
            cpu_values = [d.get("cpu_percent", 0) for d in pattern_data]
            cpu_mean = sum(cpu_values) / len(cpu_values)
            cpu_variance = sum((x - cpu_mean) ** 2 for x in cpu_values) / len(cpu_values)

            # Calculate variance in memory usage
            memory_values = [d.get("memory_percent", 0) for d in pattern_data]
            memory_mean = sum(memory_values) / len(memory_values)
            memory_variance = sum((x - memory_mean) ** 2 for x in memory_values) / len(memory_values)

            # Lower variance = higher stability
            stability = 1.0 / (1.0 + (cpu_variance + memory_variance) / 100.0)
            return min(1.0, max(0.0, stability))

        except Exception as e:
            logger.debug(f"Error calculating stability score: {e}")
            return 0.5

    def _get_app_relationships(self, app_id: str) -> List[Dict[str, Any]]:
        """Get relationships for a specific application."""
        relationships = []

        for rel in self.application_relationships.values():
            if rel.app1_id == app_id or rel.app2_id == app_id:
                relationships.append(self._relationship_to_dict(rel))

        return relationships

    def _assess_cpu_health(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Assess CPU health."""
        if metrics.cpu_usage > 90:
            status = "critical"
            message = "CPU usage critically high"
        elif metrics.cpu_usage > 70:
            status = "warning"
            message = "CPU usage high"
        elif metrics.cpu_usage > 50:
            status = "fair"
            message = "CPU usage moderate"
        else:
            status = "good"
            message = "CPU usage normal"

        return {"status": status, "message": message, "usage": metrics.cpu_usage, "frequency": metrics.cpu_frequency, "temperature": metrics.cpu_temperature}

    def _assess_memory_health(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Assess memory health."""
        if metrics.memory_percent > 95:
            status = "critical"
            message = "Memory usage critically high"
        elif metrics.memory_percent > 80:
            status = "warning"
            message = "Memory usage high"
        elif metrics.memory_percent > 60:
            status = "fair"
            message = "Memory usage moderate"
        else:
            status = "good"
            message = "Memory usage normal"

        return {"status": status, "message": message, "usage_percent": metrics.memory_percent, "used_gb": metrics.memory_used / (1024**3), "total_gb": metrics.memory_total / (1024**3)}

    def _assess_disk_health(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Assess disk health."""
        if metrics.disk_percent > 95:
            status = "critical"
            message = "Disk space critically low"
        elif metrics.disk_percent > 85:
            status = "warning"
            message = "Disk space low"
        elif metrics.disk_percent > 70:
            status = "fair"
            message = "Disk space moderate"
        else:
            status = "good"
            message = "Disk space adequate"

        return {
            "status": status,
            "message": message,
            "usage_percent": metrics.disk_percent,
            "used_gb": metrics.disk_used / (1024**3),
            "total_gb": metrics.disk_total / (1024**3),
            "free_gb": (metrics.disk_total - metrics.disk_used) / (1024**3),
        }

    def _assess_network_health(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Assess network health."""
        # This is a simplified assessment
        # In a real implementation, this would compare against baseline
        return {
            "status": "good",
            "message": "Network activity normal",
            "bytes_sent": metrics.network_bytes_sent,
            "bytes_recv": metrics.network_bytes_recv,
            "packets_sent": metrics.network_packets_sent,
            "packets_recv": metrics.network_packets_recv,
        }

    def _assess_process_health(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Assess process health."""
        if metrics.process_count > 500:
            status = "warning"
            message = "High number of processes"
        elif metrics.process_count > 300:
            status = "fair"
            message = "Moderate number of processes"
        else:
            status = "good"
            message = "Normal number of processes"

        return {"status": status, "message": message, "process_count": metrics.process_count, "thread_count": metrics.thread_count, "load_average": metrics.load_average}

    def _generate_health_recommendations(self, health_status: SystemHealthStatus, metrics: SystemMetrics) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []

        if metrics.cpu_usage > 80:
            recommendations.append("Consider closing unnecessary applications to reduce CPU load")

        if metrics.memory_percent > 85:
            recommendations.append("Close memory-intensive applications or add more RAM")

        if metrics.disk_percent > 90:
            recommendations.append("Free up disk space by removing unnecessary files")

        if metrics.process_count > 400:
            recommendations.append("Review running processes and close unnecessary ones")

        if health_status == SystemHealthStatus.CRITICAL:
            recommendations.append("System requires immediate attention - consider restarting")

        return recommendations

    def _analyze_health_trends(self) -> Dict[str, Any]:
        """Analyze health trends over time."""
        try:
            if len(self.snapshot_history) < 5:
                return {"status": "insufficient_data"}

            recent_snapshots = list(self.snapshot_history)[-10:]  # Last 10 snapshots

            # Calculate trends
            cpu_trend = self._calculate_trend([s.system_metrics.cpu_usage for s in recent_snapshots])
            memory_trend = self._calculate_trend([s.system_metrics.memory_percent for s in recent_snapshots])
            disk_trend = self._calculate_trend([s.system_metrics.disk_percent for s in recent_snapshots])

            return {"cpu_trend": cpu_trend, "memory_trend": memory_trend, "disk_trend": disk_trend, "overall_trend": "improving" if (cpu_trend + memory_trend + disk_trend) < 0 else "degrading"}

        except Exception as e:
            logger.error(f"Error analyzing health trends: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend direction for a series of values."""
        if len(values) < 2:
            return 0.0

        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))

        # Calculate slope
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        return slope

    def _calculate_consistency(self, pattern_data: List[Dict[str, Any]]) -> float:
        """Calculate consistency score for pattern data."""
        try:
            if len(pattern_data) < 3:
                return 0.5

            cpu_values = [d.get("cpu_percent", 0) for d in pattern_data]
            mean_cpu = sum(cpu_values) / len(cpu_values)

            if mean_cpu == 0:
                return 1.0  # Consistently inactive

            # Calculate coefficient of variation
            variance = sum((x - mean_cpu) ** 2 for x in cpu_values) / len(cpu_values)
            std_dev = variance**0.5
            cv = std_dev / mean_cpu if mean_cpu > 0 else 0

            # Convert to consistency score (lower CV = higher consistency)
            consistency = 1.0 / (1.0 + cv)
            return min(1.0, max(0.0, consistency))

        except Exception as e:
            logger.debug(f"Error calculating consistency: {e}")
            return 0.5

    def _find_peak_times(self, pattern_data: List[Dict[str, Any]]) -> List[str]:
        """Find peak activity times for an application."""
        try:
            if len(pattern_data) < 10:
                return []

            # Group by hour and find peaks
            hourly_activity = defaultdict(list)

            for data in pattern_data:
                timestamp_str = data.get("timestamp", "")
                if timestamp_str:
                    try:
                        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        hour = dt.hour
                        cpu = data.get("cpu_percent", 0)
                        hourly_activity[hour].append(cpu)
                    except ValueError:
                        continue

            # Calculate average activity per hour
            hourly_averages = {}
            for hour, cpu_values in hourly_activity.items():
                hourly_averages[hour] = sum(cpu_values) / len(cpu_values)

            # Find top 3 peak hours
            sorted_hours = sorted(hourly_averages.items(), key=lambda x: x[1], reverse=True)
            peak_hours = [f"{hour:02d}:00" for hour, _ in sorted_hours[:3]]

            return peak_hours

        except Exception as e:
            logger.debug(f"Error finding peak times: {e}")
            return []
