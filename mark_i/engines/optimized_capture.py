"""
MARK-I Optimized Screen Capture
Optimized screen capture for real-time performance on Linux.
"""

import logging
import time
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any
import numpy as np
import cv2
from concurrent.futures import ThreadPoolExecutor
import threading

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.engines.optimized_capture")

class OptimizedCaptureEngine:
    """Optimized screen capture engine for maximum real-time performance."""
    
    def __init__(self):
        self.screen_width = 1920
        self.screen_height = 1080
        self.capture_cache = {}
        self.cache_lock = threading.Lock()
        self.last_capture_time = 0
        self.cache_duration = 0.033  # 30 FPS cache (33ms)
        
        # Thread pool for async captures
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Get screen dimensions
        self._get_screen_dimensions()
        
        logger.info("OptimizedCaptureEngine initialized")
    
    def _get_screen_dimensions(self):
        """Get screen dimensions quickly."""
        try:
            # Try xrandr first (fastest)
            result = subprocess.run(["xrandr"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=1.0)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if ' connected primary ' in line or (' connected ' in line and 'primary' not in line):
                        parts = line.split()
                        for part in parts:
                            if 'x' in part and '+' in part:
                                resolution = part.split('+')[0]
                                if 'x' in resolution:
                                    w, h = resolution.split('x')
                                    self.screen_width = int(w)
                                    self.screen_height = int(h)
                                    logger.info(f"Screen: {self.screen_width}x{self.screen_height}")
                                    return
        except:
            pass
        
        # Fallback
        logger.warning("Using default screen size 1920x1080")
    
    def get_screen_width(self) -> int:
        return self.screen_width
    
    def get_screen_height(self) -> int:
        return self.screen_height
    
    def capture_screen_optimized(self, x: int = 0, y: int = 0, 
                               width: Optional[int] = None, 
                               height: Optional[int] = None,
                               use_cache: bool = True) -> Optional[np.ndarray]:
        """
        Optimized screen capture with caching for real-time performance.
        
        Args:
            x, y: Top-left coordinates
            width, height: Capture dimensions
            use_cache: Whether to use cached results for performance
        
        Returns:
            BGR numpy array or None if failed
        """
        if width is None:
            width = self.screen_width
        if height is None:
            height = self.screen_height
        
        # Check cache for recent capture
        if use_cache:
            current_time = time.time()
            cache_key = f"{x},{y},{width},{height}"
            
            with self.cache_lock:
                if (cache_key in self.capture_cache and 
                    current_time - self.last_capture_time < self.cache_duration):
                    return self.capture_cache[cache_key].copy()
        
        # Perform actual capture
        result = self._fast_capture_gnome(x, y, width, height)
        
        # Update cache
        if result is not None and use_cache:
            with self.cache_lock:
                self.capture_cache[cache_key] = result.copy()
                self.last_capture_time = time.time()
                
                # Limit cache size
                if len(self.capture_cache) > 5:
                    # Remove oldest entry
                    oldest_key = next(iter(self.capture_cache))
                    del self.capture_cache[oldest_key]
        
        return result
    
    def _fast_capture_gnome(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """Fast capture using gnome-screenshot with optimizations."""
        tmp_path = None
        try:
            # Create temporary file
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".png")
            os.close(tmp_fd)
            
            # Use gnome-screenshot (most compatible)
            cmd = ["gnome-screenshot", "-f", tmp_path]
            
            # Run with timeout
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  timeout=1.5,  # Reduced timeout
                                  env=os.environ.copy())
            
            if result.returncode == 0 and os.path.exists(tmp_path):
                # Load image
                img = cv2.imread(tmp_path)
                if img is not None:
                    # Crop if needed
                    if x != 0 or y != 0 or width != self.screen_width or height != self.screen_height:
                        h, w = img.shape[:2]
                        x1 = max(0, min(x, w))
                        y1 = max(0, min(y, h))
                        x2 = max(0, min(x + width, w))
                        y2 = max(0, min(y + height, h))
                        
                        if x2 > x1 and y2 > y1:
                            img = img[y1:y2, x1:x2]
                    
                    return img
            
            return None
            
        except Exception as e:
            logger.error(f"Fast gnome capture error: {e}")
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    
    def capture_small_region(self, x: int, y: int, size: int = 320) -> Optional[np.ndarray]:
        """Capture a small region for maximum speed."""
        return self.capture_screen_optimized(x, y, size, size)
    
    def capture_center_region(self, size: int = 640) -> Optional[np.ndarray]:
        """Capture center region for speed."""
        x = (self.screen_width - size) // 2
        y = (self.screen_height - size) // 2
        return self.capture_screen_optimized(x, y, size, size)
    
    def benchmark_optimized_capture(self, iterations: int = 20) -> Dict[str, Any]:
        """Benchmark optimized capture performance."""
        logger.info(f"Benchmarking optimized capture ({iterations} iterations)...")
        
        # Test different scenarios
        scenarios = [
            ("small_region", lambda: self.capture_small_region(0, 0, 320)),
            ("medium_region", lambda: self.capture_center_region(640)),
            ("large_region", lambda: self.capture_screen_optimized(0, 0, 1280, 720)),
            ("cached_capture", lambda: self.capture_screen_optimized(0, 0, 320, 240, use_cache=True))
        ]
        
        results = {}
        
        for scenario_name, capture_func in scenarios:
            times = []
            successful = 0
            
            print(f"   Testing {scenario_name}...")
            
            for i in range(iterations):
                start_time = time.time()
                result = capture_func()
                end_time = time.time()
                
                if result is not None:
                    times.append(end_time - start_time)
                    successful += 1
                
                # Show progress
                if (i + 1) % 5 == 0:
                    print(f"     Progress: {i+1}/{iterations}")
            
            if times:
                avg_time = np.mean(times)
                fps = 1.0 / avg_time if avg_time > 0 else 0.0
                
                results[scenario_name] = {
                    "success_rate": successful / iterations,
                    "avg_time_ms": avg_time * 1000,
                    "fps": fps,
                    "successful_captures": successful
                }
            else:
                results[scenario_name] = {
                    "success_rate": 0.0,
                    "avg_time_ms": 0.0,
                    "fps": 0.0,
                    "successful_captures": 0
                }
        
        return results
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        with self.cache_lock:
            cache_size = len(self.capture_cache)
            cache_age = time.time() - self.last_capture_time if self.last_capture_time > 0 else 0
        
        return {
            "cache_size": cache_size,
            "cache_age_ms": cache_age * 1000,
            "cache_duration_ms": self.cache_duration * 1000,
            "screen_resolution": f"{self.screen_width}x{self.screen_height}"
        }
    
    def clear_cache(self):
        """Clear the capture cache."""
        with self.cache_lock:
            self.capture_cache.clear()
            self.last_capture_time = 0
        logger.info("Capture cache cleared")