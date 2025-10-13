"""
MARK-I Native Screen Capture
Ultra-fast native screen capture for real-time performance.
"""

import logging
import time
import platform
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any
import numpy as np
import cv2
from PIL import Image

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.engines.native_capture")


class NativeCaptureEngine:
    """Native screen capture engine optimized for maximum speed."""

    def __init__(self):
        self.system = platform.system()
        self.capture_method = None
        self.screen_width = 1920
        self.screen_height = 1080

        # Initialize the fastest native method
        self._initialize_native_capture()
        self._get_screen_dimensions()

        logger.info(f"NativeCaptureEngine initialized: {self.capture_method}")

        # Set debug level for testing
        logger.setLevel(logging.DEBUG)

    def _initialize_native_capture(self):
        """Initialize the fastest native capture method."""

        if self.system == "Linux":
            # Check for available tools in order of speed
            # On Wayland, scrot works better than ImageMagick import
            tools = [("scrot", "scrot (fast and compatible)"), ("import", "ImageMagick import (fastest but X11 only)"), ("gnome-screenshot", "gnome-screenshot (slow but compatible)")]

            for tool, description in tools:
                if self._check_tool_available(tool):
                    self.capture_method = tool
                    logger.info(f"Using {description}")
                    return

            # Fallback
            self.capture_method = "fallback"
            logger.warning("No fast capture tools found, using fallback")

        else:
            self.capture_method = "fallback"
            logger.info("Non-Linux system, using fallback method")

    def _check_tool_available(self, tool: str) -> bool:
        """Check if a command-line tool is available."""
        try:
            result = subprocess.run(["which", tool], capture_output=True, timeout=1.0)
            return result.returncode == 0
        except:
            return False

    def _get_screen_dimensions(self):
        """Get screen dimensions using the fastest method."""
        try:
            if self.system == "Linux":
                # Try xrandr first (fastest)
                try:
                    result = subprocess.run(["xrandr"], capture_output=True, text=True, timeout=2.0)
                    if result.returncode == 0:
                        lines = result.stdout.split("\n")
                        for line in lines:
                            if " connected primary " in line or " connected " in line:
                                # Parse resolution like "1920x1080+0+0"
                                parts = line.split()
                                for part in parts:
                                    if "x" in part and "+" in part:
                                        resolution = part.split("+")[0]
                                        if "x" in resolution:
                                            w, h = resolution.split("x")
                                            self.screen_width = int(w)
                                            self.screen_height = int(h)
                                            logger.info(f"Screen: {self.screen_width}x{self.screen_height}")
                                            return
                except Exception as e:
                    logger.debug(f"xrandr failed: {e}")

                # Fallback to xdpyinfo
                try:
                    result = subprocess.run(["xdpyinfo"], capture_output=True, text=True, timeout=2.0)
                    if result.returncode == 0:
                        for line in result.stdout.split("\n"):
                            if "dimensions:" in line:
                                # Parse "dimensions:    1920x1080 pixels"
                                parts = line.split()
                                for part in parts:
                                    if "x" in part and "pixels" not in part:
                                        w, h = part.split("x")
                                        self.screen_width = int(w)
                                        self.screen_height = int(h)
                                        logger.info(f"Screen: {self.screen_width}x{self.screen_height}")
                                        return
                except Exception as e:
                    logger.debug(f"xdpyinfo failed: {e}")

            # Final fallback
            logger.warning("Could not detect screen size, using default 1920x1080")

        except Exception as e:
            logger.error(f"Error getting screen dimensions: {e}")

    def get_screen_width(self) -> int:
        """Get screen width."""
        return self.screen_width

    def get_screen_height(self) -> int:
        """Get screen height."""
        return self.screen_height

    def capture_screen_native(self, x: int = 0, y: int = 0, width: Optional[int] = None, height: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Native screen capture optimized for speed.

        Args:
            x, y: Top-left coordinates
            width, height: Capture dimensions (None = full screen)

        Returns:
            BGR numpy array or None if failed
        """
        if width is None:
            width = self.screen_width
        if height is None:
            height = self.screen_height

        try:
            if self.capture_method == "import":
                return self._capture_with_import(x, y, width, height)
            elif self.capture_method == "scrot":
                return self._capture_with_scrot(x, y, width, height)
            elif self.capture_method == "gnome-screenshot":
                return self._capture_with_gnome_screenshot(x, y, width, height)
            else:
                return self._capture_fallback(x, y, width, height)

        except Exception as e:
            logger.error(f"Native capture error: {e}")
            return None

    def _capture_with_import(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """Capture using ImageMagick import (fastest on Linux)."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # ImageMagick import command for region capture
            cmd = ["import", "-window", "root", "-crop", f"{width}x{height}+{x}+{y}", "+repage", tmp_path]

            # Execute with timeout
            result = subprocess.run(cmd, capture_output=True, timeout=0.5)  # 500ms timeout

            if result.returncode == 0 and os.path.exists(tmp_path):
                # Load image
                img = cv2.imread(tmp_path)
                os.unlink(tmp_path)  # Clean up
                return img
            else:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return None

        except Exception as e:
            logger.error(f"Import capture error: {e}")
            return None

    def _capture_with_scrot(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """Capture using scrot (full screen then crop for reliability)."""
        tmp_path = None
        try:
            # Create temporary file
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".png")
            os.close(tmp_fd)  # Close file descriptor

            # Use full screen capture (more reliable than region)
            cmd = ["scrot", tmp_path]

            # Pass environment variables for display access
            env = os.environ.copy()

            result = subprocess.run(cmd, capture_output=True, timeout=2.0, env=env)

            if result.returncode == 0:
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    # Load full screen image
                    img = cv2.imread(tmp_path)
                    if img is not None:
                        # Crop to desired region
                        h, w = img.shape[:2]
                        x1 = max(0, min(x, w))
                        y1 = max(0, min(y, h))
                        x2 = max(0, min(x + width, w))
                        y2 = max(0, min(y + height, h))

                        if x2 > x1 and y2 > y1:
                            cropped = img[y1:y2, x1:x2]
                            return cropped
                        else:
                            return img  # Return full image if crop fails
                    else:
                        logger.error("OpenCV couldn't read the scrot image")
                else:
                    logger.error(f"Scrot output file missing or empty: {tmp_path}")
            else:
                stderr_msg = result.stderr.decode() if result.stderr else "No error message"
                logger.error(f"Scrot command failed: return code {result.returncode}, stderr: {stderr_msg}")

            return None

        except Exception as e:
            logger.error(f"Scrot capture error: {e}")
            return None
        finally:
            # Clean up temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass

    def _capture_with_gnome_screenshot(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """Capture using gnome-screenshot (slowest but most compatible)."""
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # gnome-screenshot for full screen, then crop
            cmd = ["gnome-screenshot", "-f", tmp_path]

            result = subprocess.run(cmd, capture_output=True, timeout=2.0)

            if result.returncode == 0 and os.path.exists(tmp_path):
                # Load and crop
                img = cv2.imread(tmp_path)
                os.unlink(tmp_path)

                if img is not None:
                    # Crop to desired region
                    h, w = img.shape[:2]
                    x1 = max(0, min(x, w))
                    y1 = max(0, min(y, h))
                    x2 = max(0, min(x + width, w))
                    y2 = max(0, min(y + height, h))

                    if x2 > x1 and y2 > y1:
                        return img[y1:y2, x1:x2]

                return img
            else:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                return None

        except Exception as e:
            logger.error(f"Gnome-screenshot capture error: {e}")
            return None

    def _capture_fallback(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """Fallback capture method."""
        logger.warning("Using fallback capture method")
        # Create a dummy image for testing
        dummy_img = np.zeros((height, width, 3), dtype=np.uint8)
        dummy_img[:] = (64, 64, 64)  # Dark gray

        # Add some pattern to show it's working
        cv2.putText(dummy_img, "FALLBACK MODE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(dummy_img, f"{width}x{height}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        return dummy_img

    def benchmark_native_capture(self, iterations: int = 50) -> Dict[str, Any]:
        """Benchmark native capture performance."""
        logger.info(f"Benchmarking native capture ({iterations} iterations)...")

        # Test with small region for speed
        test_width = 640
        test_height = 480

        times = []
        successful_captures = 0

        for i in range(iterations):
            start_time = time.time()

            result = self.capture_screen_native(0, 0, test_width, test_height)

            end_time = time.time()
            capture_time = end_time - start_time

            if result is not None:
                times.append(capture_time)
                successful_captures += 1

                # Show progress every 10 iterations
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i+1}/{iterations} ({capture_time*1000:.1f}ms)")

        if not times:
            return {"success_rate": 0.0, "avg_time_ms": 0.0, "fps": 0.0, "method": self.capture_method}

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
            "test_resolution": f"{test_width}x{test_height}",
            "total_iterations": iterations,
            "successful_captures": successful_captures,
        }

        logger.info(f"Native benchmark: {fps:.1f} FPS, {avg_time*1000:.1f}ms avg")
        return results
