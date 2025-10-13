#!/usr/bin/env python3
"""
MARK-I Real-Time Rectangles Demo
Shows real-time updating rectangles on screen capture.
"""

import os
import sys
import time
import signal
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

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mark_i.engines.optimized_capture import OptimizedCaptureEngine

class RealtimeRectanglesDemo:
    """Real-time rectangles demo showing MARK-I's Eye in action."""
    
    def __init__(self):
        self.capture_engine = OptimizedCaptureEngine()
        self.running = True
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        
        # Focus rectangles
        self.rectangles = [
            {"name": "Critical", "x": 50, "y": 50, "width": 300, "height": 200, "color": (0, 0, 255), "priority": "CRITICAL"},
            {"name": "Important", "x": 400, "y": 100, "width": 400, "height": 300, "color": (0, 255, 255), "priority": "IMPORTANT"},
            {"name": "Monitor", "x": 100, "y": 400, "width": 500, "height": 150, "color": (0, 255, 0), "priority": "MONITOR"},
        ]
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Create GUI
        self.setup_gui()
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n🛑 Stopping real-time rectangles demo...")
        self.running = False
    
    def setup_gui(self):
        """Setup the GUI window."""
        self.root = tk.Tk()
        self.root.title("👁️ MARK-I Real-Time Eye - Rectangle Demo")
        self.root.geometry("900x700")
        
        # Top frame for controls
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Title
        title_label = tk.Label(control_frame, text="👁️ MARK-I Real-Time Eye Demo", 
                              font=("Arial", 16, "bold"))
        title_label.pack(side="left")
        
        # FPS display
        self.fps_label = tk.Label(control_frame, text="FPS: 0.0", 
                                 font=("Arial", 12), fg="red")
        self.fps_label.pack(side="right")
        
        # Status label
        self.status_label = tk.Label(self.root, text="Status: Initializing...", 
                                    font=("Arial", 10))
        self.status_label.pack(fill="x", padx=10)
        
        # Canvas for image display
        self.canvas = tk.Canvas(self.root, bg="black", width=800, height=600)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Info frame
        info_frame = tk.Frame(self.root)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = """
🔴 RED: Critical regions (30Hz updates)
🟡 YELLOW: Important regions (15Hz updates)  
🟢 GREEN: Monitor regions (5Hz updates)

This demo shows MARK-I's Eye updating rectangles in REAL-TIME!
        """
        
        info_label = tk.Label(info_frame, text=info_text, justify="left", 
                             font=("Arial", 9))
        info_label.pack()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def start_capture_thread(self):
        """Start the real-time capture thread."""
        capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        capture_thread.start()
        
        display_thread = threading.Thread(target=self._display_loop, daemon=True)
        display_thread.start()
    
    def _capture_loop(self):
        """Real-time capture loop."""
        while self.running:
            try:
                start_time = time.time()
                
                # Capture screen (optimized with caching)
                frame = self.capture_engine.capture_center_region(800)
                
                if frame is not None:
                    # Update current frame
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                    
                    # Update FPS
                    self._update_fps()
                
                # Target 30 FPS
                elapsed = time.time() - start_time
                target_time = 1.0 / 30.0  # 33ms
                if elapsed < target_time:
                    time.sleep(target_time - elapsed)
                
            except Exception as e:
                print(f"Capture error: {e}")
                time.sleep(0.1)
    
    def _display_loop(self):
        """Real-time display update loop."""
        while self.running:
            try:
                self._update_display()
                time.sleep(1.0 / 60.0)  # 60 FPS display updates
            except Exception as e:
                print(f"Display error: {e}")
                time.sleep(0.1)
    
    def _update_display(self):
        """Update the display with current frame and rectangles."""
        try:
            with self.frame_lock:
                if self.current_frame is None:
                    return
                frame = self.current_frame.copy()
            
            # Draw rectangles on frame
            for rect in self.rectangles:
                # Draw rectangle
                cv2.rectangle(frame, 
                            (rect["x"], rect["y"]), 
                            (rect["x"] + rect["width"], rect["y"] + rect["height"]),
                            rect["color"], 3)
                
                # Draw label
                label = f"{rect['name']} ({rect['priority']})"
                cv2.putText(frame, label, 
                          (rect["x"], rect["y"] - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, rect["color"], 2)
            
            # Add performance info
            cv2.putText(frame, f"FPS: {self.current_fps:.1f}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            cv2.putText(frame, "MARK-I Real-Time Eye", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # Convert to PIL and display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            # Resize to fit canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Calculate scaling
                img_ratio = pil_image.width / pil_image.height
                canvas_ratio = canvas_width / canvas_height
                
                if img_ratio > canvas_ratio:
                    new_width = canvas_width - 20
                    new_height = int(new_width / img_ratio)
                else:
                    new_height = canvas_height - 20
                    new_width = int(new_height * img_ratio)
                
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Update canvas
            photo = ImageTk.PhotoImage(pil_image)
            self.canvas.delete("all")
            self.canvas.create_image(canvas_width//2, canvas_height//2, 
                                   image=photo, anchor="center")
            self.canvas.image = photo  # Keep reference
            
            # Update status
            self.status_label.config(text=f"Status: Real-time capture active - {self.current_fps:.1f} FPS")
            self.fps_label.config(text=f"FPS: {self.current_fps:.1f}", 
                                 fg="green" if self.current_fps >= 10 else "orange" if self.current_fps >= 5 else "red")
            
        except Exception as e:
            print(f"Display update error: {e}")
    
    def _update_fps(self):
        """Update FPS counter."""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def on_closing(self):
        """Handle window closing."""
        self.running = False
        self.root.quit()
    
    def run(self):
        """Run the demo."""
        print("🚀 Starting MARK-I Real-Time Rectangles Demo")
        print("=" * 50)
        print("👁️ This demo shows MARK-I's Eye updating rectangles in REAL-TIME!")
        print("🔴 RED: Critical regions")
        print("🟡 YELLOW: Important regions") 
        print("🟢 GREEN: Monitor regions")
        print("📊 Watch the FPS counter - it should be 10+ for real-time!")
        print("🖼️ Close the window or press Ctrl+C to stop")
        print("-" * 50)
        
        # Start capture
        self.start_capture_thread()
        
        # Run GUI
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        
        self.running = False
        print("\n🎉 Demo completed!")
        print(f"📊 Final FPS: {self.current_fps:.1f}")
        
        if self.current_fps >= 15:
            print("✅ EXCELLENT: True real-time performance achieved!")
        elif self.current_fps >= 10:
            print("✅ GOOD: Real-time capable")
        elif self.current_fps >= 5:
            print("⚠️ ACCEPTABLE: Near real-time")
        else:
            print("❌ NEEDS IMPROVEMENT: Too slow for real-time")

def main():
    """Run the real-time rectangles demo."""
    demo = RealtimeRectanglesDemo()
    demo.run()

if __name__ == "__main__":
    main()