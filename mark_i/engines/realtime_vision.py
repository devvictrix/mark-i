"""
MARK-I Real-Time Vision Engine
High-performance, focused vision system for real-time screen analysis.
"""

import logging
import time
import threading
from typing import Dict, List, Any, Optional, Tuple, Callable
import queue
import cv2
import numpy as np
from PIL import Image
from dataclasses import dataclass

from mark_i.engines.optimized_capture import OptimizedCaptureEngine
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.engines.realtime_vision")

@dataclass
class FocusRegion:
    """Defines a focused region for analysis."""
    name: str
    x: int
    y: int
    width: int
    height: int
    priority: str  # "critical", "important", "monitor", "ignore"
    color: str     # "red", "yellow", "green", "gray"
    update_rate: float  # Hz (updates per second)
    last_update: float = 0.0
    
class RealtimeVisionEngine:
    """Real-time vision engine with intelligent focus regions."""
    
    def __init__(self):
        self.capture_engine = OptimizedCaptureEngine()
        self.is_running = False
        self.vision_thread = None
        self.frame_queue = queue.Queue(maxsize=5)  # Small buffer for real-time
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        self.frame_times = []
        
        # Focus regions
        self.focus_regions: List[FocusRegion] = []
        self.region_callbacks: Dict[str, Callable] = {}
        
        # Current frame data
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Performance settings
        self.target_fps = 10  # Target 10 FPS for real-time feel
        self.max_frame_time = 1.0 / self.target_fps  # 100ms max per frame
        
        logger.info("RealtimeVisionEngine initialized")
    
    def add_focus_region(self, region: FocusRegion, callback: Optional[Callable] = None):
        """Add a focus region for monitoring."""
        self.focus_regions.append(region)
        if callback:
            self.region_callbacks[region.name] = callback
        logger.info(f"Added focus region: {region.name} ({region.color} - {region.priority})")
    
    def remove_focus_region(self, name: str):
        """Remove a focus region."""
        self.focus_regions = [r for r in self.focus_regions if r.name != name]
        if name in self.region_callbacks:
            del self.region_callbacks[name]
        logger.info(f"Removed focus region: {name}")
    
    def start_realtime_vision(self):
        """Start real-time vision processing."""
        if self.is_running:
            return
        
        self.is_running = True
        self.vision_thread = threading.Thread(target=self._vision_loop, daemon=True)
        self.vision_thread.start()
        logger.info("Real-time vision started")
    
    def stop_realtime_vision(self):
        """Stop real-time vision processing."""
        self.is_running = False
        if self.vision_thread:
            self.vision_thread.join(timeout=2.0)
        logger.info("Real-time vision stopped")
    
    def _vision_loop(self):
        """Main real-time vision processing loop."""
        frame_start_time = time.time()
        
        while self.is_running:
            loop_start = time.time()
            
            try:
                # Fast screen capture
                frame = self._fast_capture()
                if frame is None:
                    time.sleep(0.01)  # Brief pause on failure
                    continue
                
                # Update current frame
                with self.frame_lock:
                    self.current_frame = frame
                
                # Process focus regions
                self._process_focus_regions(frame)
                
                # Update FPS
                self._update_fps()
                
                # Maintain target FPS
                elapsed = time.time() - loop_start
                if elapsed < self.max_frame_time:
                    time.sleep(self.max_frame_time - elapsed)
                
                # Track frame time
                total_frame_time = time.time() - loop_start
                self.frame_times.append(total_frame_time)
                if len(self.frame_times) > 100:
                    self.frame_times.pop(0)
                
            except Exception as e:
                logger.error(f"Error in vision loop: {e}")
                time.sleep(0.1)
    
    def _fast_capture(self) -> Optional[np.ndarray]:
        """Ultra-fast screen capture optimized for real-time."""
        try:
            # Use optimized capture with caching
            if not self.focus_regions:
                # Capture center region for speed
                return self.capture_engine.capture_center_region(640)
            else:
                # Full screen capture when we have focus regions
                return self.capture_engine.capture_screen_optimized()
            
        except Exception as e:
            logger.error(f"Fast capture error: {e}")
            return None
    
    def _process_focus_regions(self, frame: np.ndarray):
        """Process all focus regions based on their priority and update rate."""
        current_time = time.time()
        
        for region in self.focus_regions:
            # Check if region needs update based on its rate
            time_since_update = current_time - region.last_update
            required_interval = 1.0 / region.update_rate
            
            if time_since_update < required_interval:
                continue  # Skip this region for now
            
            # Extract region from frame
            try:
                region_frame = self._extract_region(frame, region)
                if region_frame is None:
                    continue
                
                # Process based on priority
                if region.priority == "critical":
                    self._process_critical_region(region, region_frame)
                elif region.priority == "important":
                    self._process_important_region(region, region_frame)
                elif region.priority == "monitor":
                    self._process_monitor_region(region, region_frame)
                # Skip "ignore" regions
                
                region.last_update = current_time
                
            except Exception as e:
                logger.error(f"Error processing region {region.name}: {e}")
    
    def _extract_region(self, frame: np.ndarray, region: FocusRegion) -> Optional[np.ndarray]:
        """Extract a specific region from the frame."""
        try:
            h, w = frame.shape[:2]
            
            # Ensure coordinates are within bounds
            x1 = max(0, min(region.x, w))
            y1 = max(0, min(region.y, h))
            x2 = max(0, min(region.x + region.width, w))
            y2 = max(0, min(region.y + region.height, h))
            
            if x2 <= x1 or y2 <= y1:
                return None
            
            return frame[y1:y2, x1:x2]
            
        except Exception as e:
            logger.error(f"Error extracting region: {e}")
            return None
    
    def _process_critical_region(self, region: FocusRegion, region_frame: np.ndarray):
        """Process critical (red) regions - highest priority, fastest analysis."""
        try:
            # Fast change detection
            changes = self._detect_fast_changes(region_frame, region.name)
            
            if changes > 0.1:  # 10% change threshold
                # Call callback if registered
                if region.name in self.region_callbacks:
                    self.region_callbacks[region.name]({
                        "region": region,
                        "frame": region_frame,
                        "changes": changes,
                        "priority": "CRITICAL"
                    })
                
                logger.debug(f"Critical region {region.name}: {changes:.2f} change detected")
                
        except Exception as e:
            logger.error(f"Error processing critical region: {e}")
    
    def _process_important_region(self, region: FocusRegion, region_frame: np.ndarray):
        """Process important (yellow) regions - medium priority."""
        try:
            # Medium-speed analysis
            features = self._extract_fast_features(region_frame)
            
            if region.name in self.region_callbacks:
                self.region_callbacks[region.name]({
                    "region": region,
                    "frame": region_frame,
                    "features": features,
                    "priority": "IMPORTANT"
                })
                
        except Exception as e:
            logger.error(f"Error processing important region: {e}")
    
    def _process_monitor_region(self, region: FocusRegion, region_frame: np.ndarray):
        """Process monitor (green) regions - low priority, periodic checks."""
        try:
            # Basic monitoring
            stats = self._get_basic_stats(region_frame)
            
            if region.name in self.region_callbacks:
                self.region_callbacks[region.name]({
                    "region": region,
                    "stats": stats,
                    "priority": "MONITOR"
                })
                
        except Exception as e:
            logger.error(f"Error processing monitor region: {e}")
    
    def _detect_fast_changes(self, frame: np.ndarray, region_name: str) -> float:
        """Fast change detection using frame differencing."""
        try:
            # Convert to grayscale for speed
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Store previous frame for comparison
            cache_key = f"prev_frame_{region_name}"
            if not hasattr(self, '_frame_cache'):
                self._frame_cache = {}
            
            if cache_key in self._frame_cache:
                prev_gray = self._frame_cache[cache_key]
                
                # Calculate difference
                diff = cv2.absdiff(gray, prev_gray)
                
                # Calculate change percentage
                total_pixels = diff.shape[0] * diff.shape[1]
                changed_pixels = np.count_nonzero(diff > 30)  # Threshold for significant change
                change_ratio = changed_pixels / total_pixels
                
                self._frame_cache[cache_key] = gray
                return change_ratio
            else:
                self._frame_cache[cache_key] = gray
                return 0.0
                
        except Exception as e:
            logger.error(f"Error in fast change detection: {e}")
            return 0.0
    
    def _extract_fast_features(self, frame: np.ndarray) -> Dict[str, Any]:
        """Extract basic features quickly."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Basic statistics
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            
            # Edge density (simplified)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.count_nonzero(edges) / (edges.shape[0] * edges.shape[1])
            
            return {
                "brightness": float(mean_brightness),
                "contrast": float(std_brightness),
                "edge_density": float(edge_density),
                "size": frame.shape[:2]
            }
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {}
    
    def _get_basic_stats(self, frame: np.ndarray) -> Dict[str, Any]:
        """Get basic frame statistics."""
        try:
            return {
                "shape": frame.shape,
                "mean_color": [float(np.mean(frame[:,:,i])) for i in range(3)],
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Error getting basic stats: {e}")
            return {}
    
    def _update_fps(self):
        """Update FPS counter."""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        avg_frame_time = np.mean(self.frame_times) if self.frame_times else 0.0
        
        return {
            "fps": self.current_fps,
            "avg_frame_time_ms": avg_frame_time * 1000,
            "target_fps": self.target_fps,
            "is_realtime": self.current_fps >= (self.target_fps * 0.8),  # 80% of target
            "focus_regions": len(self.focus_regions),
            "frame_buffer_size": self.frame_queue.qsize()
        }
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current frame safely."""
        with self.frame_lock:
            return self.current_frame.copy() if self.current_frame is not None else None
    
    def create_focus_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Create an overlay showing focus regions."""
        try:
            overlay = frame.copy()
            
            # Color mapping
            color_map = {
                "red": (0, 0, 255),      # Critical - Red
                "yellow": (0, 255, 255), # Important - Yellow  
                "green": (0, 255, 0),    # Monitor - Green
                "gray": (128, 128, 128)  # Ignore - Gray
            }
            
            for region in self.focus_regions:
                color = color_map.get(region.color, (255, 255, 255))
                
                # Draw rectangle
                cv2.rectangle(overlay, 
                            (region.x, region.y), 
                            (region.x + region.width, region.y + region.height),
                            color, 2)
                
                # Draw label
                label = f"{region.name} ({region.priority})"
                cv2.putText(overlay, label, 
                          (region.x, region.y - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            return overlay
            
        except Exception as e:
            logger.error(f"Error creating focus overlay: {e}")
            return frame