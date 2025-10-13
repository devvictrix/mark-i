"""
MARK-I Fast Screen Capture Engine
Ultra-fast screen capture using native methods for real-time performance.
"""

import logging
import time
import platform
from typing import Optional, Dict, Any, Tuple
import numpy as np
import cv2

# Try different capture methods based on platform
try:
    import mss  # Multi-platform screenshot library
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.engines.fast_capture")

class FastCaptureEngine:
    """Ultra-fast screen capture engine optimized for real-time performance."""
    
    def __init__(self):
        self.system = platform.system()
        self.capture_method = None
        self.mss_instance = None
        self.screen_info = None
        
        # Initialize the fastest available capture method
        self._initialize_capture_method()
        
        # Get screen dimensions
        self._get_screen_info()
        
        logger.info(f"FastCaptureEngine initialized with method: {self.capture_method}")
    
    def _initialize_capture_method(self):
        """Initialize the fastest available capture method."""
        
        # Priority order for Linux: PyAutoGUI > MSS > PIL ImageGrab
        # MSS has issues with Wayland, so prefer PyAutoGUI on Linux
        if self.system == "Linux" and PYAUTOGUI_AVAILABLE:
            try:
                # Test PyAutoGUI first on Linux
                pyautogui.size()
                self.capture_method = "pyautogui"
                logger.info("Using PyAutoGUI - FAST method (Linux optimized)")
                return
            except Exception as e:
                logger.warning(f"PyAutoGUI initialization failed: {e}")
        
        if MSS_AVAILABLE:
            try:
                self.mss_instance = mss.mss()
                # Test MSS with a small capture
                test_region = {"left": 0, "top": 0, "width": 100, "height": 100}
                test_shot = self.mss_instance.grab(test_region)
                self.capture_method = "mss"
                logger.info("Using MSS (Multi-Screen Shot) - FASTEST method")
                return
            except Exception as e:
                logger.warning(f"MSS initialization failed: {e}")
        
        if PYAUTOGUI_AVAILABLE:
            try:
                # Test PyAutoGUI
                pyautogui.size()
                self.capture_method = "pyautogui"
                logger.info("Using PyAutoGUI - FAST method")
                return
            except Exception as e:
                logger.warning(f"PyAutoGUI initialization failed: {e}")
        
        if PIL_AVAILABLE:
            try:
                # Test PIL ImageGrab
                ImageGrab.grab(bbox=(0, 0, 100, 100))
                self.capture_method = "pil"
                logger.info("Using PIL ImageGrab - MODERATE method")
                return
            except Exception as e:
                logger.warning(f"PIL ImageGrab initialization failed: {e}")
        
        # Fallback - this should not happen
        self.capture_method = "none"
        logger.error("No fast capture method available!")
    
    def _get_screen_info(self):
        """Get screen information."""
        try:
            if self.capture_method == "mss" and self.mss_instance:
                # Get primary monitor info
                monitor = self.mss_instance.monitors[1]  # monitors[0] is all monitors combined
                self.screen_info = {
                    "width": monitor["width"],
                    "height": monitor["height"],
                    "left": monitor["left"],
                    "top": monitor["top"]
                }
            elif self.capture_method == "pyautogui":
                size = pyautogui.size()
                self.screen_info = {
                    "width": size.width,
                    "height": size.height,
                    "left": 0,
                    "top": 0
                }
            else:
                # Default fallback
                self.screen_info = {
                    "width": 1920,
                    "height": 1080,
                    "left": 0,
                    "top": 0
                }
            
            logger.info(f"Screen info: {self.screen_info['width']}x{self.screen_info['height']}")
            
        except Exception as e:
            logger.error(f"Error getting screen info: {e}")
            self.screen_info = {"width": 1920, "height": 1080, "left": 0, "top": 0}
    
    def get_screen_width(self) -> int:
        """Get screen width."""
        return self.screen_info["width"] if self.screen_info else 1920
    
    def get_screen_height(self) -> int:
        """Get screen height."""
        return self.screen_info["height"] if self.screen_info else 1080
    
    def capture_screen_fast(self, x: int = 0, y: int = 0, width: Optional[int] = None, height: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Ultra-fast screen capture.
        
        Args:
            x, y: Top-left coordinates
            width, height: Capture dimensions (None = full screen)
        
        Returns:
            BGR numpy array or None if failed
        """
        if self.capture_method == "none":
            return None
        
        # Use full screen if dimensions not specified
        if width is None:
            width = self.get_screen_width()
        if height is None:
            height = self.get_screen_height()
        
        try:
            if self.capture_method == "mss":
                return self._capture_with_mss(x, y, width, height)
            elif self.capture_method == "pyautogui":
                return self._capture_with_pyautogui(x, y, width, height)
            elif self.capture_method == "pil":
                return self._capture_with_pil(x, y, width, height)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Fast capture error: {e}")
            return None
    
    def _capture_with_mss(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """Capture using MSS (fastest method)."""
        try:
            # Define capture region
            region = {
                "left": x,
                "top": y,
                "width": width,
                "height": height
            }
            
            # Capture screenshot
            screenshot = self.mss_instance.grab(region)
            
            # Convert to numpy array
            img_array = np.array(screenshot)
            
            # MSS returns BGRA, convert to BGR
            if img_array.shape[2] == 4:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
            else:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
            
        except Exception as e:
            logger.error(f"MSS capture error: {e}")
            return None
    
    def _capture_with_pyautogui(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """Capture using PyAutoGUI."""
        try:
            # Capture screenshot
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            # Convert PIL to numpy array
            img_array = np.array(screenshot)
            
            # Convert RGB to BGR
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
            
        except Exception as e:
            logger.error(f"PyAutoGUI capture error: {e}")
            return None
    
    def _capture_with_pil(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """Capture using PIL ImageGrab."""
        try:
            # Capture screenshot
            bbox = (x, y, x + width, y + height)
            screenshot = ImageGrab.grab(bbox=bbox)
            
            # Convert PIL to numpy array
            img_array = np.array(screenshot)
            
            # Convert RGB to BGR
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
            
        except Exception as e:
            logger.error(f"PIL capture error: {e}")
            return None
    
    def benchmark_capture(self, iterations: int = 100) -> Dict[str, float]:
        """Benchmark capture performance."""
        logger.info(f"Benchmarking capture performance ({iterations} iterations)...")
        
        # Small region for speed test
        test_width = 640
        test_height = 480
        
        times = []
        successful_captures = 0
        
        for i in range(iterations):
            start_time = time.time()
            
            result = self.capture_screen_fast(0, 0, test_width, test_height)
            
            end_time = time.time()
            capture_time = end_time - start_time
            
            if result is not None:
                times.append(capture_time)
                successful_captures += 1
        
        if not times:
            return {
                "success_rate": 0.0,
                "avg_time_ms": 0.0,
                "fps": 0.0,
                "method": self.capture_method
            }
        
        avg_time = np.mean(times)
        fps = 1.0 / avg_time if avg_time > 0 else 0.0
        success_rate = successful_captures / iterations
        
        results = {
            "success_rate": success_rate,
            "avg_time_ms": avg_time * 1000,
            "min_time_ms": min(times) * 1000,
            "max_time_ms": max(times) * 1000,
            "fps": fps,
            "method": self.capture_method,
            "test_resolution": f"{test_width}x{test_height}"
        }
        
        logger.info(f"Benchmark results: {fps:.1f} FPS, {avg_time*1000:.1f}ms avg")
        return results
    
    def capture_region_fast(self, region: Dict[str, int]) -> Optional[np.ndarray]:
        """Capture a specific region quickly."""
        return self.capture_screen_fast(
            x=region.get("x", 0),
            y=region.get("y", 0),
            width=region.get("width", self.get_screen_width()),
            height=region.get("height", self.get_screen_height())
        )