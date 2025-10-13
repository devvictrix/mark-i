"""
MARK-I Eye Debug Window
Real-time visual debugging tool to see what MARK-I's Eye perceives.
"""

import logging
import threading
import time
from typing import Dict, List, Any, Optional, Tuple
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import numpy as np
import json

from mark_i.engines.capture_engine import CaptureEngine
from mark_i.engines.gemini_analyzer import GeminiAnalyzer
from mark_i.engines.cv_analyzer import CVAnalyzer
from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.eye_debug_window")

class EyeDebugWindow:
    """Real-time visual debugging window for MARK-I's Eye system."""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.window = None
        self.is_running = False
        self.capture_thread = None
        
        # Initialize engines
        self.capture_engine = CaptureEngine()
        self.gemini_analyzer = None  # Initialize when needed
        self.cv_analyzer = CVAnalyzer()
        
        # UI elements
        self.canvas = None
        self.info_text = None
        self.current_image = None
        self.detected_objects = []
        
        # Settings
        self.update_interval = 2.0  # seconds
        self.show_bounding_boxes = True
        self.show_confidence = True
        self.analysis_enabled = True
        
        logger.info("EyeDebugWindow initialized")
    
    def create_window(self):
        """Create the Eye Debug window."""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("MARK-I Eye Debug - What I See")
        self.window.geometry("1200x800")
        
        # Configure grid
        self.window.grid_columnconfigure(0, weight=2)
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Top control panel
        self._create_control_panel()
        
        # Main content area
        self._create_main_content()
        
        # Start the eye monitoring
        self.start_monitoring()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("Eye Debug window created")
    
    def _create_control_panel(self):
        """Create the control panel with settings."""
        control_frame = ctk.CTkFrame(self.window)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # Title
        title_label = ctk.CTkLabel(control_frame, text="👁️ MARK-I Eye Debug", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, padx=10, pady=5)
        
        # Controls
        controls_frame = ctk.CTkFrame(control_frame)
        controls_frame.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Update interval
        ctk.CTkLabel(controls_frame, text="Update:").grid(row=0, column=0, padx=5)
        self.interval_var = tk.StringVar(value="2.0")
        interval_entry = ctk.CTkEntry(controls_frame, textvariable=self.interval_var, width=60)
        interval_entry.grid(row=0, column=1, padx=5)
        ctk.CTkLabel(controls_frame, text="sec").grid(row=0, column=2, padx=5)
        
        # Checkboxes
        self.bbox_var = tk.BooleanVar(value=True)
        bbox_check = ctk.CTkCheckBox(controls_frame, text="Bounding Boxes", 
                                    variable=self.bbox_var)
        bbox_check.grid(row=0, column=3, padx=10)
        
        self.confidence_var = tk.BooleanVar(value=True)
        conf_check = ctk.CTkCheckBox(controls_frame, text="Confidence", 
                                    variable=self.confidence_var)
        conf_check.grid(row=0, column=4, padx=10)
        
        self.analysis_var = tk.BooleanVar(value=True)
        analysis_check = ctk.CTkCheckBox(controls_frame, text="AI Analysis", 
                                        variable=self.analysis_var)
        analysis_check.grid(row=0, column=5, padx=10)
        
        self.cv_analysis_var = tk.BooleanVar(value=True)
        cv_analysis_check = ctk.CTkCheckBox(controls_frame, text="CV Analysis", 
                                           variable=self.cv_analysis_var)
        cv_analysis_check.grid(row=0, column=6, padx=10)
        
        # Update button
        update_btn = ctk.CTkButton(controls_frame, text="Update Now", 
                                  command=self.force_update, width=100)
        update_btn.grid(row=0, column=7, padx=10)
    
    def _create_main_content(self):
        """Create the main content area with image and info panels."""
        # Left panel - Image display
        image_frame = ctk.CTkFrame(self.window)
        image_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Canvas for image display
        self.canvas = tk.Canvas(image_frame, bg="black")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Right panel - Object information
        info_frame = ctk.CTkFrame(self.window)
        info_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        
        # Info title
        info_title = ctk.CTkLabel(info_frame, text="🔍 Detected Objects", 
                                 font=ctk.CTkFont(size=16, weight="bold"))
        info_title.pack(pady=10)
        
        # Scrollable text area for object info
        self.info_text = ctk.CTkTextbox(info_frame, wrap="word")
        self.info_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(info_frame, text="Status: Initializing...")
        self.status_label.pack(pady=5)
    
    def start_monitoring(self):
        """Start the eye monitoring thread."""
        if not self.is_running:
            self.is_running = True
            self.capture_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.capture_thread.start()
            logger.info("Eye monitoring started")
    
    def stop_monitoring(self):
        """Stop the eye monitoring thread."""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        logger.info("Eye monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop that captures and analyzes screen."""
        while self.is_running:
            try:
                # Update settings from UI
                self.update_interval = float(self.interval_var.get())
                self.show_bounding_boxes = self.bbox_var.get()
                self.show_confidence = self.confidence_var.get()
                self.analysis_enabled = self.analysis_var.get()
                self.cv_analysis_enabled = self.cv_analysis_var.get()
                
                # Capture screen
                self._capture_and_analyze()
                
                # Wait for next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self._update_status(f"Error: {str(e)}")
                time.sleep(1.0)
    
    def _capture_and_analyze(self):
        """Capture screen and analyze what the Eye sees."""
        try:
            # Update status
            self._update_status("Capturing screen...")
            
            # Capture full screen
            screen_region = {
                "name": "eye_debug_capture",
                "x": 0,
                "y": 0,
                "width": self.capture_engine.get_primary_screen_width(),
                "height": self.capture_engine.get_primary_screen_height()
            }
            
            captured_image = self.capture_engine.capture_region(screen_region)
            if captured_image is None:
                self._update_status("❌ Screen capture failed")
                return
            
            # Convert to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(captured_image, cv2.COLOR_BGR2RGB))
            self.current_image = pil_image.copy()
            
            # Analyze with AI and/or CV if enabled
            ai_objects = []
            cv_objects = []
            
            if self.analysis_enabled:
                self._update_status("🧠 Analyzing with AI...")
                ai_objects = self._analyze_image_ai(pil_image)
            
            if self.cv_analysis_enabled:
                self._update_status("👁️ Analyzing with Computer Vision...")
                cv_objects = self._analyze_image_cv(captured_image)
            
            # Combine results
            self.detected_objects = ai_objects + cv_objects
            
            # Update display in main thread
            if self.window:
                self.window.after_idle(self._update_display)
                self._update_status("✅ Updated")
            
        except Exception as e:
            logger.error(f"Error in capture and analyze: {e}")
            self._update_status(f"❌ Error: {str(e)}")
    
    def _analyze_image_ai(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Analyze the image with AI to detect objects."""
        try:
            # Initialize Gemini analyzer if needed
            if self.gemini_analyzer is None:
                from mark_i.core.app_config import VALIDATED_CONFIG
                self.gemini_analyzer = GeminiAnalyzer(VALIDATED_CONFIG.GEMINI_API_KEY)
            
            # Analysis prompt
            analysis_prompt = """
            Analyze this screenshot and identify all visible objects and UI elements.
            
            For each object you can clearly see, provide:
            1. Object type (button, text, window, icon, image, etc.)
            2. Object description/label
            3. Approximate bounding box coordinates (x, y, width, height) as percentages of image size
            4. Confidence level (1-10)
            5. Color description
            6. Whether it's interactive/clickable
            
            Respond in JSON format:
            {
                "objects": [
                    {
                        "type": "button",
                        "description": "Save button",
                        "bbox": {"x": 10, "y": 20, "width": 15, "height": 5},
                        "confidence": 8,
                        "color": "blue background, white text",
                        "interactive": true,
                        "source": "AI"
                    }
                ],
                "total_objects": 5,
                "overall_description": "Desktop with file manager window open"
            }
            
            Note: bbox coordinates are percentages (0-100) of image dimensions.
            """
            
            # Convert PIL to numpy array for the analyzer
            image_np = np.array(image)
            image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            response = self.gemini_analyzer.query_vision_model(
                prompt=analysis_prompt,
                image_data=image_bgr,
                expect_json=True
            )
            
            if response and response.get("status") == "success":
                json_content = response.get("json_content", {})
                objects = json_content.get("objects", [])
                # Mark as AI-detected
                for obj in objects:
                    obj["source"] = "AI"
                logger.info(f"AI detected {len(objects)} objects")
                return objects
            else:
                logger.warning(f"AI analysis failed: {response.get('error_message', 'Unknown error')}")
                return []
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return []
    
    def _analyze_image_cv(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze the image with Computer Vision to detect objects."""
        try:
            # Run comprehensive CV analysis
            cv_results = self.cv_analyzer.analyze_image_comprehensive(image)
            
            if "error" in cv_results:
                logger.error(f"CV analysis error: {cv_results['error']}")
                return []
            
            # Convert CV detections to our format
            cv_objects = []
            detections = cv_results.get("detections", {})
            
            # Process shapes
            for shape in detections.get("shapes", []):
                bbox = shape.get("bbox", {})
                # Convert pixel coordinates to percentages
                img_height, img_width = image.shape[:2]
                cv_objects.append({
                    "type": f"shape_{shape.get('shape_type', 'unknown')}",
                    "description": f"{shape.get('shape_type', 'unknown').title()} shape",
                    "bbox": {
                        "x": round(bbox.get("x", 0) * 100 / img_width, 1),
                        "y": round(bbox.get("y", 0) * 100 / img_height, 1),
                        "width": round(bbox.get("width", 0) * 100 / img_width, 1),
                        "height": round(bbox.get("height", 0) * 100 / img_height, 1)
                    },
                    "confidence": shape.get("confidence", 5),
                    "color": "detected by computer vision",
                    "interactive": False,
                    "source": "CV",
                    "area": shape.get("area", 0),
                    "vertices": shape.get("vertices", 0)
                })
            
            # Process text regions
            for text_region in detections.get("text_regions", []):
                bbox = text_region.get("bbox", {})
                cv_objects.append({
                    "type": "text_region",
                    "description": "Potential text area",
                    "bbox": {
                        "x": round(bbox.get("x", 0) * 100 / img_width, 1),
                        "y": round(bbox.get("y", 0) * 100 / img_height, 1),
                        "width": round(bbox.get("width", 0) * 100 / img_width, 1),
                        "height": round(bbox.get("height", 0) * 100 / img_height, 1)
                    },
                    "confidence": text_region.get("confidence", 5),
                    "color": "detected by computer vision",
                    "interactive": True,
                    "source": "CV",
                    "area": text_region.get("area", 0),
                    "aspect_ratio": text_region.get("aspect_ratio", 1.0)
                })
            
            # Process UI elements
            for ui_element in detections.get("ui_elements", []):
                bbox = ui_element.get("bbox", {})
                ui_type = ui_element.get("ui_type", "unknown")
                cv_objects.append({
                    "type": f"ui_{ui_type}",
                    "description": f"Potential {ui_type}",
                    "bbox": {
                        "x": round(bbox.get("x", 0) * 100 / img_width, 1),
                        "y": round(bbox.get("y", 0) * 100 / img_height, 1),
                        "width": round(bbox.get("width", 0) * 100 / img_width, 1),
                        "height": round(bbox.get("height", 0) * 100 / img_height, 1)
                    },
                    "confidence": ui_element.get("confidence", 5),
                    "color": "detected by computer vision",
                    "interactive": ui_type in ["button", "text_field"],
                    "source": "CV",
                    "area": ui_element.get("area", 0),
                    "aspect_ratio": ui_element.get("aspect_ratio", 1.0)
                })
            
            logger.info(f"CV detected {len(cv_objects)} objects")
            return cv_objects
            
        except Exception as e:
            logger.error(f"Error in CV analysis: {e}")
            return []
    
    def _update_display(self):
        """Update the visual display with current image and detected objects."""
        if not self.current_image:
            return
        
        try:
            # Create a copy for drawing
            display_image = self.current_image.copy()
            draw = ImageDraw.Draw(display_image)
            
            # Draw bounding boxes and labels if enabled
            if self.show_bounding_boxes and self.detected_objects:
                self._draw_detections(draw, display_image)
            
            # Resize image to fit canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Calculate scaling to fit canvas while maintaining aspect ratio
                img_ratio = display_image.width / display_image.height
                canvas_ratio = canvas_width / canvas_height
                
                if img_ratio > canvas_ratio:
                    # Image is wider, scale by width
                    new_width = canvas_width - 20
                    new_height = int(new_width / img_ratio)
                else:
                    # Image is taller, scale by height
                    new_height = canvas_height - 20
                    new_width = int(new_height * img_ratio)
                
                display_image = display_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and display
            photo = ImageTk.PhotoImage(display_image)
            
            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(canvas_width//2, canvas_height//2, image=photo, anchor="center")
            
            # Keep a reference to prevent garbage collection
            self.canvas.image = photo
            
            # Update object information
            self._update_object_info()
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
    
    def _draw_detections(self, draw: ImageDraw.Draw, image: Image.Image):
        """Draw bounding boxes and labels for detected objects."""
        try:
            # Try to load a font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            img_width, img_height = image.size
            
            for i, obj in enumerate(self.detected_objects):
                # Get bounding box (convert from percentages)
                bbox = obj.get("bbox", {})
                x = int(bbox.get("x", 0) * img_width / 100)
                y = int(bbox.get("y", 0) * img_height / 100)
                width = int(bbox.get("width", 10) * img_width / 100)
                height = int(bbox.get("height", 10) * img_height / 100)
                
                # Choose color based on object type and source
                source = obj.get("source", "AI")
                color = self._get_color_for_type(obj.get("type", "unknown"), source)
                
                # Draw bounding box
                draw.rectangle([x, y, x + width, y + height], outline=color, width=2)
                
                # Draw label
                source = obj.get("source", "AI")
                label = f"[{source}] {obj.get('type', 'unknown')}"
                if self.show_confidence:
                    confidence = obj.get("confidence", 0)
                    label += f" ({confidence}/10)"
                
                # Draw label background
                label_bbox = draw.textbbox((0, 0), label, font=font)
                label_width = label_bbox[2] - label_bbox[0]
                label_height = label_bbox[3] - label_bbox[1]
                
                draw.rectangle([x, y - label_height - 4, x + label_width + 4, y], 
                             fill=color, outline=color)
                draw.text((x + 2, y - label_height - 2), label, fill="white", font=font)
                
        except Exception as e:
            logger.error(f"Error drawing detections: {e}")
    
    def _get_color_for_type(self, obj_type: str, source: str = "AI") -> str:
        """Get color for object type, with different shades for AI vs CV."""
        # Base colors for AI detections
        ai_colors = {
            "button": "#FF6B6B",      # Red
            "text": "#4ECDC4",        # Teal
            "window": "#45B7D1",      # Blue
            "icon": "#96CEB4",        # Green
            "image": "#FFEAA7",       # Yellow
            "menu": "#DDA0DD",        # Plum
            "input": "#98D8C8",       # Mint
            "link": "#F7DC6F",        # Light Yellow
        }
        
        # Darker colors for CV detections
        cv_colors = {
            "shape_": "#8B4513",      # Brown for shapes
            "text_region": "#4169E1", # Royal Blue for text regions
            "ui_button": "#DC143C",   # Crimson for UI buttons
            "ui_text_field": "#2E8B57", # Sea Green for text fields
            "ui_window": "#191970",   # Midnight Blue for windows
            "ui_icon": "#228B22",     # Forest Green for icons
            "ui_unknown": "#696969",  # Dim Gray for unknown UI
        }
        
        if source == "CV":
            # Check for CV-specific types
            for cv_type, color in cv_colors.items():
                if obj_type.lower().startswith(cv_type):
                    return color
            return "#808080"  # Gray default for CV
        else:
            # AI detection colors
            for ai_type, color in ai_colors.items():
                if ai_type in obj_type.lower():
                    return color
            return "#FFFFFF"  # White default for AI
    
    def _update_object_info(self):
        """Update the object information panel."""
        try:
            self.info_text.delete("1.0", "end")
            
            if not self.detected_objects:
                self.info_text.insert("1.0", "No objects detected.\n\nEither AI analysis is disabled or no objects were found in the current view.")
                return
            
            # Separate AI and CV detections
            ai_objects = [obj for obj in self.detected_objects if obj.get("source") == "AI"]
            cv_objects = [obj for obj in self.detected_objects if obj.get("source") == "CV"]
            
            info_text = f"🔍 Found {len(self.detected_objects)} objects:\n"
            info_text += f"   🧠 AI: {len(ai_objects)} objects\n"
            info_text += f"   👁️ CV: {len(cv_objects)} objects\n\n"
            
            # Show AI detections first
            if ai_objects:
                info_text += "🧠 AI DETECTIONS:\n"
                for i, obj in enumerate(ai_objects, 1):
                    info_text += f"#{i} {obj.get('type', 'Unknown').upper()}\n"
                    info_text += f"   📝 {obj.get('description', 'No description')}\n"
                    info_text += f"   🎯 Confidence: {obj.get('confidence', 0)}/10\n"
                    info_text += f"   🎨 Color: {obj.get('color', 'Unknown')}\n"
                    info_text += f"   🖱️ Interactive: {'Yes' if obj.get('interactive') else 'No'}\n"
                    
                    bbox = obj.get('bbox', {})
                    info_text += f"   📍 Position: ({bbox.get('x', 0):.1f}%, {bbox.get('y', 0):.1f}%)\n"
                    info_text += f"   📏 Size: {bbox.get('width', 0):.1f}% × {bbox.get('height', 0):.1f}%\n"
                    info_text += "\n"
            
            # Show CV detections
            if cv_objects:
                info_text += "👁️ COMPUTER VISION DETECTIONS:\n"
                for i, obj in enumerate(cv_objects, 1):
                    info_text += f"#{i} {obj.get('type', 'Unknown').upper()}\n"
                    info_text += f"   📝 {obj.get('description', 'No description')}\n"
                    info_text += f"   🎯 Confidence: {obj.get('confidence', 0)}/10\n"
                    
                    # Show CV-specific info
                    if obj.get('area'):
                        info_text += f"   📐 Area: {obj.get('area')} pixels\n"
                    if obj.get('aspect_ratio'):
                        info_text += f"   📊 Aspect Ratio: {obj.get('aspect_ratio')}\n"
                    if obj.get('vertices'):
                        info_text += f"   🔺 Vertices: {obj.get('vertices')}\n"
                    
                    bbox = obj.get('bbox', {})
                    info_text += f"   📍 Position: ({bbox.get('x', 0):.1f}%, {bbox.get('y', 0):.1f}%)\n"
                    info_text += f"   📏 Size: {bbox.get('width', 0):.1f}% × {bbox.get('height', 0):.1f}%\n"
                    info_text += "\n"
            
            self.info_text.insert("1.0", info_text)
            
        except Exception as e:
            logger.error(f"Error updating object info: {e}")
            self.info_text.delete("1.0", "end")
            self.info_text.insert("1.0", f"Error displaying object info: {str(e)}")
    
    def _update_status(self, status: str):
        """Update the status label safely from any thread."""
        try:
            if self.status_label and self.window:
                # Use after_idle to safely update from background thread
                self.window.after_idle(lambda: self._safe_update_status(status))
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def _safe_update_status(self, status: str):
        """Safely update status label in main thread."""
        try:
            if self.status_label:
                self.status_label.configure(text=f"Status: {status}")
        except Exception as e:
            logger.error(f"Error in safe status update: {e}")
    
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
            logger.info("Eye Debug window closed")
        except Exception as e:
            logger.error(f"Error closing Eye Debug window: {e}")
    
    def show(self):
        """Show the Eye Debug window."""
        if not self.window:
            self.create_window()
        else:
            self.window.deiconify()
            self.window.lift()