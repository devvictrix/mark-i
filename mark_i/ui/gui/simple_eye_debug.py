"""
Simple Eye Debug Window for MARK-I
A more robust, simplified version of the Eye Debug window.
"""

import logging
import threading
import time
from typing import Dict, List, Any, Optional
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import numpy as np

from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.cv_analyzer import CVAnalyzer
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.simple_eye_debug")

class SimpleEyeDebugWindow:
    """Simple, robust Eye Debug window."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.window = None
        self.is_running = False
        self.update_thread = None
        
        # Initialize engines
        self.capture_engine = CaptureEngine()
        self.cv_analyzer = CVAnalyzer()
        
        # UI elements
        self.canvas = None
        self.info_label = None
        self.status_label = None
        
        # Current data
        self.current_stats = {}
        
        logger.info("SimpleEyeDebugWindow initialized")
    
    def create_window(self):
        """Create the simple Eye Debug window."""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("👁️ MARK-I Eye Debug - What I See")
        self.window.geometry("800x600")
        
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Top panel - controls and info
        self._create_top_panel()
        
        # Main content
        self._create_main_content()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start monitoring
        self.start_monitoring()
        
        logger.info("Simple Eye Debug window created")
    
    def _create_top_panel(self):
        """Create the top control panel."""
        top_frame = ctk.CTkFrame(self.window)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        top_frame.grid_columnconfigure(1, weight=1)
        
        # Title and update button
        title_label = ctk.CTkLabel(top_frame, text="👁️ MARK-I Eye Debug", 
                                  font=ctk.CTkFont(size=18, weight="bold"))
        title_label.grid(row=0, column=0, padx=10, pady=5)
        
        update_btn = ctk.CTkButton(top_frame, text="Update Now", 
                                  command=self.force_update, width=100)
        update_btn.grid(row=0, column=2, padx=10, pady=5)
        
        # Status
        self.status_label = ctk.CTkLabel(top_frame, text="Status: Initializing...")
        self.status_label.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="w")
    
    def _create_main_content(self):
        """Create the main content area."""
        main_frame = ctk.CTkFrame(self.window)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left - Image preview
        image_frame = ctk.CTkFrame(main_frame)
        image_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.canvas = tk.Canvas(image_frame, bg="black")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Right - Information
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        info_title = ctk.CTkLabel(info_frame, text="🔍 Detection Stats", 
                                 font=ctk.CTkFont(size=14, weight="bold"))
        info_title.pack(pady=10)
        
        self.info_label = ctk.CTkLabel(info_frame, text="No data yet...", 
                                      justify="left", anchor="nw")
        self.info_label.pack(fill="both", expand=True, padx=10, pady=10)
    
    def start_monitoring(self):
        """Start the monitoring thread."""
        if not self.is_running:
            self.is_running = True
            self.update_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.update_thread.start()
            logger.info("Eye monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=2.0)
        logger.info("Eye monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                self._capture_and_analyze()
                time.sleep(3.0)  # Update every 3 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self._safe_update_status(f"Error: {str(e)}")
                time.sleep(1.0)
    
    def _capture_and_analyze(self):
        """Capture screen and analyze."""
        try:
            self._safe_update_status("📸 Capturing screen...")
            
            # Capture screen
            screen_region = {
                "name": "simple_eye_debug",
                "x": 0,
                "y": 0,
                "width": self.capture_engine.get_primary_screen_width(),
                "height": self.capture_engine.get_primary_screen_height()
            }
            
            start_time = time.time()
            captured_image = self.capture_engine.capture_region(screen_region)
            capture_time = time.time() - start_time
            
            if captured_image is None:
                self._safe_update_status("❌ Screen capture failed")
                return
            
            self._safe_update_status("👁️ Analyzing with CV...")
            
            # Analyze with CV
            start_time = time.time()
            cv_results = self.cv_analyzer.analyze_image_comprehensive(captured_image)
            cv_time = time.time() - start_time
            
            # Update stats
            self.current_stats = {
                "capture_time": capture_time,
                "cv_time": cv_time,
                "cv_results": cv_results,
                "image_shape": captured_image.shape
            }
            
            # Update display in main thread
            if self.window:
                self.window.after_idle(self._update_display)
            
            self._safe_update_status("✅ Analysis complete")
            
        except Exception as e:
            logger.error(f"Error in capture and analyze: {e}")
            self._safe_update_status(f"❌ Error: {str(e)}")
    
    def _update_display(self):
        """Update the display with current stats."""
        try:
            if not self.current_stats:
                return
            
            cv_results = self.current_stats.get("cv_results", {})
            summary = cv_results.get("summary", {})
            complexity = cv_results.get("visual_complexity", {})
            
            # Update info text
            info_text = f"""📊 SCREEN ANALYSIS
            
🖼️ Resolution: {self.capture_engine.get_primary_screen_width()}x{self.capture_engine.get_primary_screen_height()}
📐 Image Shape: {self.current_stats.get('image_shape', 'Unknown')}

⏱️ PERFORMANCE
📸 Capture: {self.current_stats.get('capture_time', 0)*1000:.1f}ms
👁️ CV Analysis: {self.current_stats.get('cv_time', 0)*1000:.1f}ms

🧠 VISUAL COMPLEXITY
Level: {complexity.get('complexity_level', 'unknown').upper()}
Edge Density: {complexity.get('edge_density', 0):.4f}

🎯 DETECTIONS
Total Objects: {summary.get('total_detections', 0):,}
🔺 Shapes: {summary.get('shape_count', 0):,}
📝 Text Regions: {summary.get('text_region_count', 0):,}
🖱️ UI Elements: {summary.get('ui_element_count', 0):,}

🎨 CAPTURE METHOD
{getattr(self.capture_engine, 'capture_tool', 'ImageGrab')}
"""
            
            self.info_label.configure(text=info_text)
            
            # Simple performance indicator on canvas
            if self.canvas:
                self.canvas.delete("all")
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                if canvas_width > 1 and canvas_height > 1:
                    # Draw performance indicator
                    total_time = self.current_stats.get('capture_time', 0) + self.current_stats.get('cv_time', 0)
                    total_objects = summary.get('total_detections', 0)
                    
                    # Performance color
                    if total_time < 1.0:
                        color = "green"
                        status = "EXCELLENT"
                    elif total_time < 3.0:
                        color = "orange"
                        status = "GOOD"
                    else:
                        color = "red"
                        status = "SLOW"
                    
                    # Draw status
                    self.canvas.create_text(canvas_width//2, canvas_height//2 - 50, 
                                          text=f"👁️ MARK-I EYE STATUS", 
                                          fill="white", font=("Arial", 16, "bold"))
                    
                    self.canvas.create_text(canvas_width//2, canvas_height//2, 
                                          text=f"{status}", 
                                          fill=color, font=("Arial", 24, "bold"))
                    
                    self.canvas.create_text(canvas_width//2, canvas_height//2 + 30, 
                                          text=f"{total_objects:,} objects detected", 
                                          fill="white", font=("Arial", 12))
                    
                    self.canvas.create_text(canvas_width//2, canvas_height//2 + 50, 
                                          text=f"in {total_time*1000:.1f}ms", 
                                          fill="white", font=("Arial", 12))
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
    
    def _safe_update_status(self, status: str):
        """Safely update status from any thread."""
        try:
            if self.window and self.status_label:
                self.window.after_idle(lambda: self._update_status_label(status))
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def _update_status_label(self, status: str):
        """Update status label in main thread."""
        try:
            if self.status_label:
                self.status_label.configure(text=f"Status: {status}")
        except Exception as e:
            logger.error(f"Error updating status label: {e}")
    
    def force_update(self):
        """Force an immediate update."""
        if self.is_running:
            threading.Thread(target=self._capture_and_analyze, daemon=True).start()
    
    def on_closing(self):
        """Handle window closing."""
        try:
            self.stop_monitoring()
            if self.window:
                self.window.destroy()
                self.window = None
            logger.info("Simple Eye Debug window closed")
        except Exception as e:
            logger.error(f"Error closing window: {e}")
    
    def show(self):
        """Show the window."""
        if not self.window:
            self.create_window()
        else:
            self.window.deiconify()
            self.window.lift()