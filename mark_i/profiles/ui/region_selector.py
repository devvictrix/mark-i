"""
Region Selector Component

Visual tool for selecting and defining screen regions through drag-and-drop interface.
Provides overlay system for showing defined regions and validation.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Optional, List, Callable, Tuple
import logging
from PIL import Image, ImageTk, ImageDraw
import threading
import time

from ..models.region import Region


class RegionSelector(ctk.CTkToplevel):
    """Visual region selection tool with drag-and-drop interface"""
    
    def __init__(self, parent=None, callback: Optional[Callable[[Region], None]] = None):
        super().__init__(parent)
        
        self.callback = callback
        self.logger = logging.getLogger("mark_i.profiles.ui.region_selector")
        
        # Selection state
        self.selecting = False
        self.start_x = 0
        self.start_y = 0
        self.current_x = 0
        self.current_y = 0
        self.selected_region: Optional[Region] = None
        
        # Screenshot and canvas
        self.screenshot: Optional[Image.Image] = None
        self.canvas_image: Optional[ImageTk.PhotoImage] = None
        self.selection_rect = None
        
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        
        # Take screenshot and display
        self._take_screenshot()
        
        self.logger.info("RegionSelector initialized")
    
    def _setup_window(self):
        """Configure the selector window"""
        self.title("Select Screen Region")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.configure(cursor="crosshair")
        
        # Make window transparent background
        self.attributes("-alpha", 0.3)
        
        # Get screen dimensions
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        
        self.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
    
    def _create_widgets(self):
        """Create selector widgets"""
        # Main canvas for selection
        self.canvas = tk.Canvas(
            self, 
            width=self.screen_width,
            height=self.screen_height,
            highlightthickness=0,
            cursor="crosshair"
        )
        
        # Instructions label
        self.instructions = ctk.CTkLabel(
            self,
            text="Click and drag to select a region. Press ESC to cancel.",
            font=("Arial", 16, "bold"),
            text_color="white",
            fg_color="black"
        )
        
        # Control buttons frame
        self.controls_frame = ctk.CTkFrame(self, fg_color="black")
        
        self.confirm_btn = ctk.CTkButton(
            self.controls_frame,
            text="Confirm Selection",
            command=self._confirm_selection,
            width=150,
            state="disabled"
        )
        
        self.cancel_btn = ctk.CTkButton(
            self.controls_frame,
            text="Cancel",
            command=self._cancel_selection,
            width=100
        )
        
        self.retake_btn = ctk.CTkButton(
            self.controls_frame,
            text="Retake Screenshot",
            command=self._retake_screenshot,
            width=150
        )
    
    def _setup_layout(self):
        """Setup widget layout"""
        self.canvas.pack(fill="both", expand=True)
        
        # Position instructions at top
        self.instructions.place(x=20, y=20)
        
        # Position controls at bottom center
        self.controls_frame.place(
            x=self.screen_width//2 - 200,
            y=self.screen_height - 80
        )
        
        self.retake_btn.pack(side="left", padx=5)
        self.confirm_btn.pack(side="left", padx=5)
        self.cancel_btn.pack(side="left", padx=5)
    
    def _bind_events(self):
        """Bind event handlers"""
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        
        self.bind("<Escape>", lambda e: self._cancel_selection())
        self.bind("<Return>", lambda e: self._confirm_selection())
        
        # Focus on canvas for key events
        self.canvas.focus_set()
    
    def _take_screenshot(self):
        """Take screenshot of current screen"""
        try:
            # Hide this window temporarily
            self.withdraw()
            
            # Wait a moment for window to hide
            self.after(100, self._capture_screen)
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            messagebox.showerror("Error", f"Failed to capture screen: {str(e)}")
            self._cancel_selection()
    
    def _capture_screen(self):
        """Capture the screen after hiding window"""
        try:
            import pyautogui
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            self.screenshot = screenshot
            
            # Convert to PhotoImage for display
            # Resize if too large for display
            display_image = self.screenshot.copy()
            if display_image.size[0] > 1920 or display_image.size[1] > 1080:
                display_image.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
            
            self.canvas_image = ImageTk.PhotoImage(display_image)
            
            # Show window again
            self.deiconify()
            self.attributes("-alpha", 0.8)
            
            # Display screenshot on canvas
            self.canvas.create_image(0, 0, anchor="nw", image=self.canvas_image)
            
            self.logger.info("Screenshot captured and displayed")
            
        except ImportError:
            self.logger.error("PyAutoGUI not available for screenshot")
            messagebox.showerror("Error", "PyAutoGUI is required for screen capture")
            self._cancel_selection()
        except Exception as e:
            self.logger.error(f"Failed to capture screen: {e}")
            messagebox.showerror("Error", f"Failed to capture screen: {str(e)}")
            self._cancel_selection()
    
    def _retake_screenshot(self):
        """Retake screenshot"""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        
        self.selected_region = None
        self.confirm_btn.configure(state="disabled")
        
        self._take_screenshot()
    
    def _on_mouse_down(self, event):
        """Handle mouse button down"""
        self.selecting = True
        self.start_x = event.x
        self.start_y = event.y
        self.current_x = event.x
        self.current_y = event.y
        
        # Remove previous selection
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        
        self.confirm_btn.configure(state="disabled")
    
    def _on_mouse_drag(self, event):
        """Handle mouse drag"""
        if not self.selecting:
            return
        
        self.current_x = event.x
        self.current_y = event.y
        
        # Update selection rectangle
        self._update_selection_rect()
    
    def _on_mouse_up(self, event):
        """Handle mouse button up"""
        if not self.selecting:
            return
        
        self.selecting = False
        self.current_x = event.x
        self.current_y = event.y
        
        # Finalize selection
        self._finalize_selection()
    
    def _update_selection_rect(self):
        """Update the selection rectangle display"""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        
        # Calculate rectangle coordinates
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)
        
        # Draw selection rectangle
        self.selection_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="red",
            width=2,
            fill="",
            dash=(5, 5)
        )
        
        # Update instructions with current dimensions
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        self.instructions.configure(
            text=f"Selection: {width}x{height} at ({x1}, {y1})"
        )
    
    def _finalize_selection(self):
        """Finalize the region selection"""
        # Calculate final coordinates
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)
        
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Validate selection size
        if width < 10 or height < 10:
            messagebox.showwarning("Invalid Selection", "Selection too small. Minimum size is 10x10 pixels.")
            return
        
        # Create region object
        self.selected_region = Region(
            name=f"Region_{int(time.time())}",
            x=x1,
            y=y1,
            width=width,
            height=height,
            description=f"Selected region {width}x{height} at ({x1}, {y1})"
        )
        
        # Enable confirm button
        self.confirm_btn.configure(state="normal")
        
        # Update instructions
        self.instructions.configure(
            text=f"Region selected: {width}x{height} at ({x1}, {y1}). Click Confirm to save."
        )
        
        self.logger.info(f"Region selected: {self.selected_region}")
    
    def _confirm_selection(self):
        """Confirm and return the selected region"""
        if not self.selected_region:
            messagebox.showwarning("No Selection", "Please select a region first.")
            return
        
        # Open region properties dialog
        dialog = RegionPropertiesDialog(self, self.selected_region)
        if dialog.result:
            self.selected_region = dialog.result
            
            # Call callback if provided
            if self.callback:
                self.callback(self.selected_region)
            
            self.destroy()
    
    def _cancel_selection(self):
        """Cancel region selection"""
        self.selected_region = None
        self.destroy()


class RegionPropertiesDialog(ctk.CTkToplevel):
    """Dialog for setting region properties after selection"""
    
    def __init__(self, parent, region: Region):
        super().__init__(parent)
        
        self.region = region
        self.result: Optional[Region] = None
        
        self.title("Region Properties")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._setup_layout()
        self._load_region_data()
        
        self.name_entry.focus()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        self.main_frame = ctk.CTkFrame(self)
        
        # Region info
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Region: {self.region.width}x{self.region.height} at ({self.region.x}, {self.region.y})",
            font=("Arial", 12, "bold")
        )
        
        # Region name
        self.name_label = ctk.CTkLabel(self.main_frame, text="Region Name:")
        self.name_entry = ctk.CTkEntry(self.main_frame, width=300)
        
        # Description
        self.desc_label = ctk.CTkLabel(self.main_frame, text="Description:")
        self.desc_text = ctk.CTkTextbox(self.main_frame, width=300, height=100)
        
        # Position adjustments
        self.pos_label = ctk.CTkLabel(self.main_frame, text="Position Adjustments:", 
                                     font=("Arial", 12, "bold"))
        
        self.x_label = ctk.CTkLabel(self.main_frame, text="X Offset:")
        self.x_entry = ctk.CTkEntry(self.main_frame, width=100)
        
        self.y_label = ctk.CTkLabel(self.main_frame, text="Y Offset:")
        self.y_entry = ctk.CTkEntry(self.main_frame, width=100)
        
        self.width_label = ctk.CTkLabel(self.main_frame, text="Width Adjustment:")
        self.width_entry = ctk.CTkEntry(self.main_frame, width=100)
        
        self.height_label = ctk.CTkLabel(self.main_frame, text="Height Adjustment:")
        self.height_entry = ctk.CTkEntry(self.main_frame, width=100)
        
        # Options
        self.options_label = ctk.CTkLabel(self.main_frame, text="Options:", 
                                         font=("Arial", 12, "bold"))
        
        self.ocr_var = ctk.BooleanVar()\n        self.ocr_check = ctk.CTkCheckBox(
            self.main_frame, text="Enable OCR for this region", 
            variable=self.ocr_var
        )
        
        self.monitor_var = ctk.BooleanVar()
        self.monitor_check = ctk.CTkCheckBox(
            self.main_frame, text="Monitor this region for changes", 
            variable=self.monitor_var
        )
        
        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.ok_button = ctk.CTkButton(
            self.button_frame, text="OK", width=100,
            command=self._on_ok
        )
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", width=100,
            command=self._on_cancel
        )
    
    def _setup_layout(self):
        """Setup dialog layout"""
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.info_label.pack(pady=(0, 15))
        
        self.name_label.pack(anchor="w", pady=(0, 5))
        self.name_entry.pack(anchor="w", pady=(0, 10))
        
        self.desc_label.pack(anchor="w", pady=(0, 5))
        self.desc_text.pack(anchor="w", pady=(0, 15))
        
        self.pos_label.pack(anchor="w", pady=(0, 10))
        
        # Position adjustments in grid
        pos_frame = ctk.CTkFrame(self.main_frame)
        pos_frame.pack(fill="x", pady=(0, 15))
        
        self.x_label.pack(in_=pos_frame, side="left", padx=(10, 5))
        self.x_entry.pack(in_=pos_frame, side="left", padx=(0, 20))
        
        self.y_label.pack(in_=pos_frame, side="left", padx=(0, 5))
        self.y_entry.pack(in_=pos_frame, side="left", padx=(0, 10))
        
        size_frame = ctk.CTkFrame(self.main_frame)
        size_frame.pack(fill="x", pady=(0, 15))
        
        self.width_label.pack(in_=size_frame, side="left", padx=(10, 5))
        self.width_entry.pack(in_=size_frame, side="left", padx=(0, 20))
        
        self.height_label.pack(in_=size_frame, side="left", padx=(0, 5))
        self.height_entry.pack(in_=size_frame, side="left", padx=(0, 10))
        
        self.options_label.pack(anchor="w", pady=(0, 10))
        self.ocr_check.pack(anchor="w", pady=2)
        self.monitor_check.pack(anchor="w", pady=(2, 15))
        
        self.button_frame.pack(fill="x")
        self.ok_button.pack(side="right", padx=(5, 0))
        self.cancel_button.pack(side="right", padx=(5, 5))
        
        # Bind keys
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())
    
    def _load_region_data(self):
        """Load region data into form"""
        self.name_entry.insert(0, self.region.name)
        self.desc_text.insert("1.0", self.region.description)
        
        # Set default adjustments to 0
        self.x_entry.insert(0, "0")
        self.y_entry.insert(0, "0")
        self.width_entry.insert(0, "0")
        self.height_entry.insert(0, "0")
        
        self.ocr_var.set(self.region.ocr_enabled)
    
    def _on_ok(self):
        """Handle OK button"""
        try:
            # Get form values
            name = self.name_entry.get().strip()
            if not name:
                messagebox.showwarning("Invalid Input", "Region name is required.")
                return
            
            description = self.desc_text.get("1.0", tk.END).strip()
            
            # Apply position adjustments
            x_offset = int(self.x_entry.get() or "0")
            y_offset = int(self.y_entry.get() or "0")
            width_adj = int(self.width_entry.get() or "0")
            height_adj = int(self.height_entry.get() or "0")
            
            # Update region
            self.region.name = name
            self.region.description = description
            self.region.x += x_offset
            self.region.y += y_offset
            self.region.width += width_adj
            self.region.height += height_adj
            self.region.ocr_enabled = self.ocr_var.get()
            
            # Validate final dimensions
            if self.region.width <= 0 or self.region.height <= 0:
                messagebox.showerror("Invalid Dimensions", "Region width and height must be positive.")
                return
            
            if self.region.x < 0 or self.region.y < 0:
                messagebox.showwarning("Invalid Position", "Region position cannot be negative.")
                # Allow but warn
            
            self.result = self.region
            self.destroy()
            
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for adjustments.")
    
    def _on_cancel(self):
        """Handle Cancel button"""
        self.result = None
        self.destroy()


class RegionOverlay(ctk.CTkToplevel):
    """Overlay window for displaying defined regions on screen"""
    
    def __init__(self, regions: List[Region], duration: int = 5):
        super().__init__()
        
        self.regions = regions
        self.duration = duration
        
        self._setup_overlay()
        self._draw_regions()
        
        # Auto-close after duration
        if duration > 0:
            self.after(duration * 1000, self.destroy)
    
    def _setup_overlay(self):
        """Setup overlay window"""
        self.title("Region Overlay")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.7)
        
        # Make window click-through
        self.overrideredirect(True)
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Create canvas
        self.canvas = tk.Canvas(
            self,
            width=screen_width,
            height=screen_height,
            highlightthickness=0,
            bg="black"
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Bind escape to close
        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()
    
    def _draw_regions(self):
        """Draw all regions on overlay"""
        colors = ["red", "blue", "green", "yellow", "orange", "purple", "cyan", "magenta"]
        
        for i, region in enumerate(self.regions):
            color = colors[i % len(colors)]
            
            # Draw region rectangle
            self.canvas.create_rectangle(
                region.x, region.y,
                region.x + region.width, region.y + region.height,
                outline=color,
                width=3,
                fill="",
                dash=(10, 5)
            )
            
            # Draw region label
            label_x = region.x + 5
            label_y = region.y + 5
            
            # Background for text
            self.canvas.create_rectangle(
                label_x - 2, label_y - 2,
                label_x + len(region.name) * 8 + 2, label_y + 16,
                fill="black",
                outline=color,
                width=1
            )
            
            # Region name text
            self.canvas.create_text(
                label_x, label_y,
                text=region.name,
                fill=color,
                font=("Arial", 12, "bold"),
                anchor="nw"
            )
            
            # Region info text
            info_text = f"{region.width}x{region.height}"
            if region.ocr_enabled:
                info_text += " (OCR)"
            
            self.canvas.create_text(
                label_x, label_y + 18,
                text=info_text,
                fill=color,
                font=("Arial", 10),
                anchor="nw"
            )


def show_region_overlay(regions: List[Region], duration: int = 5):
    """Show region overlay for specified duration"""
    if not regions:
        return
    
    overlay = RegionOverlay(regions, duration)
    return overlay


def select_screen_region(parent=None, callback: Optional[Callable[[Region], None]] = None) -> Optional[Region]:
    """Launch region selector and return selected region"""
    selector = RegionSelector(parent, callback)
    
    # If no callback provided, wait for result
    if not callback:
        parent.wait_window(selector)
        return selector.selected_region
    
    return None