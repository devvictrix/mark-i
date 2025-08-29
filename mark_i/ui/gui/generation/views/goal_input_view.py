import logging
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import time
from typing import Optional, Any, Callable

import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk, ImageGrab
import cv2

from mark_i.ui.gui.generation.wizard_state import WizardState
from mark_i.engines.capture_engine import CaptureEngine

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.generation.views.goal_input_view")

# Constants specific to this view
WIZARD_SCREENSHOT_PREVIEW_MAX_WIDTH = 350  # For the small preview on this page
WIZARD_SCREENSHOT_PREVIEW_MAX_HEIGHT = 200


class GoalInputView(ctk.CTkFrame):
    """
    UI View for the first page of the AI Profile Creator wizard:
    defining the automation goal and providing initial visual context.
    """

    def __init__(self, master: Any, controller: Any, state: WizardState, on_generate_plan: Callable[[str, Optional[np.ndarray]], None], on_state_change: Callable[[], None]):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        self.state = state
        self.on_generate_plan = on_generate_plan
        self.on_state_change = on_state_change  # Callback to notify controller of state changes (e.g., button enablement)

        self.capture_engine: CaptureEngine = self.controller.get_capture_engine()

        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.grid_columnconfigure(0, weight=1)  # Allow content to expand

        self._setup_ui()
        logger.debug("GoalInputView UI setup complete.")

    def _setup_ui(self):
        ctk.CTkLabel(self, text="AI Profile Creator: Step 1 - Define Your Automation Goal", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20), anchor="w")

        ctk.CTkLabel(self, text="Describe the task Mark-I should learn and automate in detail:", anchor="w").pack(fill="x", pady=(5, 2))
        self.goal_textbox = ctk.CTkTextbox(self, height=180, wrap="word", font=ctk.CTkFont(size=13))
        self.goal_textbox.pack(fill="x", pady=(0, 15))
        self.goal_textbox.insert(
            "0.0",
            self.state.user_goal_text
            or "Example: Open MyApp, log in with username 'testuser' and password 'password123', navigate to the 'Reports' section, then click the 'Generate Monthly Sales Report' button, and finally save the downloaded report as 'Sales_Report_ThisMonth.pdf' to the Desktop.",
        )
        self.goal_textbox.bind("<KeyRelease>", lambda e: self.on_state_change())  # Notify controller if text changes

        context_frame = ctk.CTkFrame(self, fg_color="transparent")
        context_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(context_frame, text="Optional: Initial Visual Context (helps AI understand the starting screen):", anchor="w").pack(fill="x", pady=(0, 5))

        btn_frame = ctk.CTkFrame(context_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkButton(btn_frame, text="Capture Full Screen", command=self._capture_full_screen_context, width=180).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_frame, text="Load Image from File", command=self._load_image_context, width=180).pack(side="left", padx=10)

        self.context_image_preview_label = ctk.CTkLabel(context_frame, text="No context image.", height=WIZARD_SCREENSHOT_PREVIEW_MAX_HEIGHT, fg_color=("gray85", "gray25"), corner_radius=6)
        self.context_image_preview_label.pack(fill="x", pady=(10, 0))

        self._update_context_image_preview()  # Display initial state
        self.goal_textbox.focus_set()

    def _capture_full_screen_context(self):
        logger.info("GoalInputView: Capturing full screen for context...")
        try:
            # Temporarily hide wizard window during capture
            self.master.master.attributes("-alpha", 0.0)  # Master is main_content_frame, master.master is ProfileCreationWizardWindow
            self.master.master.lower()
            self.master.master.update_idletasks()
            time.sleep(0.3)  # Give window time to hide fully

            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            captured_np_bgr = self.capture_engine.capture_region({"name": "wizard_full_screen_context", "x": 0, "y": 0, "width": screen_width, "height": screen_height})

            self.master.master.attributes("-alpha", 1.0)
            self.master.master.lift()
            self.master.master.focus_set()

            if captured_np_bgr is not None:
                self.state.current_full_context_np = captured_np_bgr
                self.state.current_full_context_pil = Image.fromarray(cv2.cvtColor(captured_np_bgr, cv2.COLOR_BGR2RGB))
                logger.info(f"GoalInputView: Full screen captured (Size: {self.state.current_full_context_pil.width}x{self.state.current_full_context_pil.height}).")
            else:
                self.state.current_full_context_np = None
                self.state.current_full_context_pil = None
                logger.error("GoalInputView: Full screen capture failed (returned None).")
        except Exception as e:
            self.state.current_full_context_np = None
            self.state.current_full_context_pil = None
            logger.error(f"GoalInputView: Error capturing full screen: {e}", exc_info=True)
            if self.master.master.winfo_exists():
                self.master.master.attributes("-alpha", 1.0)
                self.master.master.lift()
        self._update_context_image_preview()
        self.on_state_change()  # Notify controller of state change

    def _load_image_context(self):
        filepath = filedialog.askopenfilename(title="Select Context Image", filetypes=[("Image", "*.png *.jpg *.jpeg *.bmp")], parent=self.controller)
        if filepath:
            try:
                img_pil = Image.open(filepath)
                self.state.current_full_context_pil = img_pil.convert("RGB")
                img_np_rgb = np.array(self.state.current_full_context_pil)
                self.state.current_full_context_np = cv2.cvtColor(img_np_rgb, cv2.COLOR_RGB2BGR)
                logger.info(f"GoalInputView: Context image loaded: '{filepath}' (Size: {img_pil.width}x{img_pil.height}).")
            except Exception as e:
                self.state.current_full_context_pil = None
                self.state.current_full_context_np = None
                logger.error(f"GoalInputView: Error loading context image: {e}", exc_info=True)
        self._update_context_image_preview()
        self.on_state_change()  # Notify controller of state change

    def _update_context_image_preview(self):
        if not hasattr(self, "context_image_preview_label") or not self.context_image_preview_label.winfo_exists():
            return

        if self.state.current_full_context_pil:
            img_copy = self.state.current_full_context_pil.copy()

            # Adjust preview size to fit the label, maintaining aspect ratio
            preview_max_w = WIZARD_SCREENSHOT_PREVIEW_MAX_WIDTH
            preview_max_h = self.context_image_preview_label.winfo_reqheight() - 20  # Leave some vertical padding
            preview_max_h = max(50, preview_max_h)  # Ensure a minimum height

            img_copy.thumbnail((preview_max_w, preview_max_h), Image.Resampling.LANCZOS)

            ctk_img = ctk.CTkImage(light_image=img_copy, dark_image=img_copy, size=(img_copy.width, img_copy.height))
            self.context_image_preview_label.configure(
                image=ctk_img, text=f"Context: {self.state.current_full_context_pil.width}x{self.state.current_full_context_pil.height} (Loaded)", height=img_copy.height + 10
            )
        else:
            self.context_image_preview_label.configure(image=None, text="No context image selected.", height=WIZARD_SCREENSHOT_PREVIEW_MAX_HEIGHT)
        self.on_state_change()  # Notify controller of state change

    def trigger_generate_plan(self):
        """Called by the controller to get the goal and trigger plan generation."""
        user_goal_text = self.goal_textbox.get("0.0", "end-1c").strip()
        self.state.user_goal_text = user_goal_text
        self.on_generate_plan(user_goal_text, self.state.current_full_context_np)
        self.on_state_change()  # Update button state immediately after triggering plan generation
