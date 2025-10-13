#!/usr/bin/env python3
"""
MARK-I Real-Time Eye Viewer
Live video feed showing what MARK-I's Eye sees with real-time object detection.
"""

import os
import sys
import time
import threading
from pathlib import Path
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np

# Load environment variables
load_dotenv()

# Add mark_i to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.cv_analyzer import CVAnalyzer

class RealTimeEyeViewer:
    """Real-time viewer for MARK-I's Eye system."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("👁️ MARK-I Real-Time Eye Viewer")
        self.root.geometry("1400x900")
        
        # Initialize engines
        self.capture_engine = CaptureEngine()
        self.cv_analyzer = CVAnalyzer()
        
        # Control variables
        self.is_running = False
        self.show_detections = tk.BooleanVar(value=True)
        self.show_shapes = tk.BooleanVar(value=True)
        self.show_text_regions = tk.BooleanVar(value=True)
        self.show_ui_elements = tk.BooleanVar(value=True)
        self.fps_target = tk.IntVar(value=2)  # Target FPS
        
        # Stats
        self.frame_count = 0
        self.start_time = time.time()
        self.last_frame_time = 0
        self.current_fps = 0
        self.detection_count = 0
        
        # Threading
        self.capture_thread = None
        self.current_frame = None
        self.current_detections = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface."""
        # Control panel
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Title
        title_label = ttk.Label(control_frame, text="👁️ MARK-I Real-Time Eye Viewer", 
                               font=("Arial", 16, "bold"))
        title_label.pack(side="left")
        
        # Controls
        controls_right = ttk.Frame(control_frame)
        controls_right.pack(side="right")
        
        # Start/Stop button
        self.start_stop_btn = ttk.Button(controls_right, text="▶️ Start", 
                                        command=self.toggle_capture)
        self.start_stop_btn.pack(side="left", padx=5)
        
        # FPS control
        ttk.Label(controls_right, text="FPS:").pack(side="left", padx=5)
        fps_spinbox = ttk.Spinbox(controls_right, from_=1, to=10, width=5, 
                                 textvariable=self.fps_target)
        fps_spinbox.pack(side="left", padx=5)
        
        # Detection toggles
        detection_frame = ttk.LabelFrame(self.root, text="Detection Options")
        detection_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Checkbutton(detection_frame, text="Show Detections", 
                       variable=self.show_detections).pack(side="left", padx=10)
        ttk.Checkbutton(detection_frame, text="Shapes", 
                       variable=self.show_shapes).pack(side="left", padx=10)
        ttk.Checkbutton(detection_frame, text="Text Regions", 
                       variable=self.show_text_regions).pack(side="left", padx=10)
        ttk.Checkbutton(detection_frame, text="UI Elements", 
                       variable=self.show_ui_elements).pack(side="left", padx=10)
        
        # Main content area
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Video display
        video_frame = ttk.LabelFrame(content_frame, text="Live Eye Feed")
        video_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self.video_label = ttk.Label(video_frame, text="Click Start to begin live feed", 
                                    anchor="center")
        self.video_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Stats panel
        stats_frame = ttk.LabelFrame(content_frame, text="Eye Statistics")
        stats_frame.pack(side="right", fill="y", padx=(5, 0))
        stats_frame.configure(width=300)
        
        # Stats display
        self.stats_text = tk.Text(stats_frame, width=35, height=30, wrap="word")
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", 
                                       command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        stats_scrollbar.pack(side="right", fill="y")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready to start Eye viewer")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief="sunken", anchor="w")
        status_bar.pack(fill="x", side="bottom")
        
    def toggle_capture(self):
        """Start or stop the real-time capture."""
        if not self.is_running:
            self.start_capture()
        else:
            self.stop_capture()
    
    def start_capture(self):
        """Start the real-time capture thread."""
        self.is_running = True
        self.start_stop_btn.configure(text="⏹️ Stop")
        self.status_var.set("Starting Eye capture...")
        
        # Reset stats
        self.frame_count = 0
        self.start_time = time.time()
        self.detection_count = 0
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
        
        # Start UI update loop
        self.update_display()
        
    def stop_capture(self):
        """Stop the real-time capture."""
        self.is_running = False
        self.start_stop_btn.configure(text="▶️ Start")
        self.status_var.set("Eye capture stopped")
        
    def capture_loop(self):
        """Main capture loop running in separate thread."""
        while self.is_running:
            try:
                frame_start = time.time()
                
                # Capture screen
                screen_region = {
                    "name": "realtime_eye_capture",
                    "x": 0,
                    "y": 0,
                    "width": self.capture_engine.get_primary_screen_width(),
                    "height": self.capture_engine.get_primary_screen_height()
                }
                
                captured_image = self.capture_engine.capture_region(screen_region)
                if captured_image is None:
                    continue
                
                # Resize for display (to improve performance)
                display_height = 600
                aspect_ratio = captured_image.shape[1] / captured_image.shape[0]
                display_width = int(display_height * aspect_ratio)
                
                display_image = cv2.resize(captured_image, (display_width, display_height))
                
                # Run CV analysis if detections are enabled
                detections = None
                if self.show_detections.get():
                    # Analyze at lower resolution for speed
                    analysis_image = cv2.resize(captured_image, (display_width, display_height))
                    cv_results = self.cv_analyzer.analyze_image_comprehensive(analysis_image)
                    detections = cv_results.get("detections", {})
                    self.detection_count = cv_results.get("summary", {}).get("total_detections", 0)
                
                # Draw detections if enabled
                if detections and self.show_detections.get():
                    display_image = self.draw_realtime_detections(display_image, detections)
                
                # Store current frame and detections
                self.current_frame = display_image
                self.current_detections = detections
                
                # Update stats
                self.frame_count += 1
                frame_time = time.time() - frame_start
                self.current_fps = 1.0 / frame_time if frame_time > 0 else 0
                
                # Control frame rate
                target_interval = 1.0 / self.fps_target.get()
                sleep_time = max(0, target_interval - frame_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"Error in capture loop: {e}")
                time.sleep(0.1)
    
    def draw_realtime_detections(self, image, detections):
        """Draw detection overlays on the image."""
        try:
            # Colors for different types
            colors = {
                "shapes": (0, 255, 0),        # Green
                "text_regions": (255, 0, 0),  # Blue  
                "ui_elements": (0, 0, 255),   # Red
            }
            
            # Draw shapes
            if self.show_shapes.get():
                for shape in detections.get("shapes", []):
                    bbox = shape.get("bbox", {})
                    x, y, w, h = bbox.get("x", 0), bbox.get("y", 0), bbox.get("width", 0), bbox.get("height", 0)
                    cv2.rectangle(image, (x, y), (x + w, y + h), colors["shapes"], 2)
                    
                    # Label
                    label = f"{shape.get('shape_type', 'shape')}"
                    cv2.putText(image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors["shapes"], 1)
            
            # Draw text regions
            if self.show_text_regions.get():
                for region in detections.get("text_regions", []):
                    bbox = region.get("bbox", {})
                    x, y, w, h = bbox.get("x", 0), bbox.get("y", 0), bbox.get("width", 0), bbox.get("height", 0)
                    cv2.rectangle(image, (x, y), (x + w, y + h), colors["text_regions"], 2)
                    
                    # Label
                    label = "text"
                    cv2.putText(image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors["text_regions"], 1)
            
            # Draw UI elements
            if self.show_ui_elements.get():
                for element in detections.get("ui_elements", []):
                    bbox = element.get("bbox", {})
                    x, y, w, h = bbox.get("x", 0), bbox.get("y", 0), bbox.get("width", 0), bbox.get("height", 0)
                    cv2.rectangle(image, (x, y), (x + w, y + h), colors["ui_elements"], 2)
                    
                    # Label
                    label = element.get("ui_type", "ui")
                    cv2.putText(image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors["ui_elements"], 1)
            
            return image
            
        except Exception as e:
            print(f"Error drawing detections: {e}")
            return image
    
    def update_display(self):
        """Update the display with current frame and stats."""
        if not self.is_running:
            return
        
        try:
            # Update video display
            if self.current_frame is not None:
                # Convert BGR to RGB for display
                display_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(display_frame)
                photo = ImageTk.PhotoImage(pil_image)
                
                self.video_label.configure(image=photo, text="")
                self.video_label.image = photo  # Keep a reference
            
            # Update stats
            self.update_stats()
            
            # Update status
            self.status_var.set(f"Eye active - FPS: {self.current_fps:.1f} - Objects: {self.detection_count}")
            
        except Exception as e:
            print(f"Error updating display: {e}")
        
        # Schedule next update
        if self.is_running:
            self.root.after(100, self.update_display)  # Update UI every 100ms
    
    def update_stats(self):
        """Update the statistics display."""
        try:
            elapsed_time = time.time() - self.start_time
            avg_fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0
            
            stats_text = f"""👁️ MARK-I EYE STATISTICS

🎥 PERFORMANCE:
   Current FPS: {self.current_fps:.1f}
   Average FPS: {avg_fps:.1f}
   Target FPS: {self.fps_target.get()}
   Frames Captured: {self.frame_count}
   Runtime: {elapsed_time:.1f}s

🔍 DETECTIONS:
   Total Objects: {self.detection_count}
   
📊 SCREEN INFO:
   Resolution: {self.capture_engine.get_primary_screen_width()}x{self.capture_engine.get_primary_screen_height()}
   Capture Method: {getattr(self.capture_engine, 'capture_tool', 'ImageGrab')}

🎛️ DETECTION FILTERS:
   Show Detections: {'✅' if self.show_detections.get() else '❌'}
   Show Shapes: {'✅' if self.show_shapes.get() else '❌'}
   Show Text Regions: {'✅' if self.show_text_regions.get() else '❌'}
   Show UI Elements: {'✅' if self.show_ui_elements.get() else '❌'}

🎯 WHAT I SEE:
"""
            
            # Add detection details if available
            if self.current_detections:
                shapes = self.current_detections.get("shapes", [])
                text_regions = self.current_detections.get("text_regions", [])
                ui_elements = self.current_detections.get("ui_elements", [])
                
                stats_text += f"   Shapes: {len(shapes)}\n"
                stats_text += f"   Text Regions: {len(text_regions)}\n"
                stats_text += f"   UI Elements: {len(ui_elements)}\n\n"
                
                # Show some examples
                if shapes:
                    stats_text += "🔺 RECENT SHAPES:\n"
                    for i, shape in enumerate(shapes[:3], 1):
                        stats_text += f"   {i}. {shape.get('shape_type', 'unknown').title()}\n"
                    stats_text += "\n"
                
                if ui_elements:
                    stats_text += "🖱️ RECENT UI ELEMENTS:\n"
                    for i, element in enumerate(ui_elements[:3], 1):
                        stats_text += f"   {i}. {element.get('ui_type', 'unknown').title()}\n"
                    stats_text += "\n"
            
            # Performance assessment
            if avg_fps >= 2:
                stats_text += "✅ PERFORMANCE: Excellent\n"
            elif avg_fps >= 1:
                stats_text += "✅ PERFORMANCE: Good\n"
            else:
                stats_text += "⚠️ PERFORMANCE: Needs optimization\n"
            
            # Update the text widget
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text)
            
        except Exception as e:
            print(f"Error updating stats: {e}")
    
    def run(self):
        """Start the real-time eye viewer."""
        print("👁️ Starting MARK-I Real-Time Eye Viewer...")
        print("🎮 Use the GUI controls to start/stop and configure detection options")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n⏹️ Stopping Eye viewer...")
        finally:
            self.is_running = False

def main():
    """Run the real-time eye viewer."""
    viewer = RealTimeEyeViewer()
    viewer.run()

if __name__ == "__main__":
    main()