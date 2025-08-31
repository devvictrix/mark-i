import logging
import tkinter as tk
from typing import Optional, Dict, Any

import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np
import cv2

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.panels.visual_log_panel")

MAX_VISUAL_LOG_PREVIEW_SIZE = (300, 200)

class VisualLogPanel(ctk.CTkFrame):
    """
    A dedicated panel to display the real-time visual "thought process" of the AI,
    including objectives, thoughts, tactics, and before/after screenshots.
    """

    def __init__(self, master: Any, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # Updated row for log textbox

        # --- References to prevent garbage collection ---
        self._before_image_ref: Optional[ctk.CTkImage] = None
        self._after_image_ref: Optional[ctk.CTkImage] = None

        # --- State Display ---
        state_frame = ctk.CTkFrame(self, fg_color="transparent")
        state_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        state_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(state_frame, text="Objective:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        self.objective_label = ctk.CTkLabel(state_frame, text="N/A", anchor="w")
        self.objective_label.grid(row=0, column=1, sticky="ew")

        # NEW: Thought display
        ctk.CTkLabel(state_frame, text="Thought:", font=ctk.CTkFont(weight="bold", slant="italic")).grid(row=1, column=0, sticky="nw")
        self.thought_label = ctk.CTkLabel(state_frame, text="Waiting for command...", anchor="w", wraplength=400, justify="left", text_color=("gray20", "gray80"), font=ctk.CTkFont(slant="italic"))
        self.thought_label.grid(row=1, column=1, sticky="ew", pady=(2, 5))

        ctk.CTkLabel(state_frame, text="Action:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="nw")
        self.tactic_label = ctk.CTkLabel(state_frame, text="N/A", anchor="w", wraplength=400, justify="left")
        self.tactic_label.grid(row=2, column=1, sticky="ew")

        # --- Visual Display ---
        visual_frame = ctk.CTkFrame(self)
        visual_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=10)
        visual_frame.grid_columnconfigure(0, weight=1)
        visual_frame.grid_columnconfigure(1, weight=1)

        before_frame = ctk.CTkFrame(visual_frame, fg_color="transparent")
        before_frame.grid(row=0, column=0, padx=5)
        ctk.CTkLabel(before_frame, text="Observation (Before Action)").pack()
        self.before_image_label = ctk.CTkLabel(before_frame, text="", fg_color=("gray85", "gray25"))
        self.before_image_label.pack()

        after_frame = ctk.CTkFrame(visual_frame, fg_color="transparent")
        after_frame.grid(row=0, column=1, padx=5)
        ctk.CTkLabel(after_frame, text="Observation (After Action)").pack()
        self.after_image_label = ctk.CTkLabel(after_frame, text="", fg_color=("gray85", "gray25"))
        self.after_image_label.pack()

        # --- Verification and Log ---
        self.verification_label = ctk.CTkLabel(self, text="Observation Text:", font=ctk.CTkFont(size=14))
        self.verification_label.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        self.log_textbox = ctk.CTkTextbox(self, state="disabled", wrap="word", font=ctk.CTkFont(family="Consolas", size=11))
        self.log_textbox.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        
        self.clear_visuals()

    def _update_image_label(self, label: ctk.CTkLabel, image_np: Optional[np.ndarray]):
        image_ref_attr = "_before_image_ref" if label is self.before_image_label else "_after_image_ref"

        if image_np is None:
            label.configure(image=None, text="")
            setattr(self, image_ref_attr, None)
            return
        
        try:
            img_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            pil_img.thumbnail(MAX_VISUAL_LOG_PREVIEW_SIZE, Image.Resampling.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            label.configure(image=ctk_image, text="")
            setattr(self, image_ref_attr, ctk_image)
        except Exception as e:
            logger.error(f"Error updating visual log image: {e}")
            label.configure(image=None, text="ERR")
            setattr(self, image_ref_attr, None)

    def clear_visuals(self):
        """Resets the panel to its initial state."""
        self.objective_label.configure(text="N/A")
        self.thought_label.configure(text="Waiting for command...")
        self.tactic_label.configure(text="N/A")
        self._update_image_label(self.before_image_label, None)
        self._update_image_label(self.after_image_label, None)
        self.verification_label.configure(text="Observation Text: PENDING", text_color="gray")
        
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", tk.END)
        self.log_textbox.configure(state="disabled")

    def add_log_message(self, message: str):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert(tk.END, message + '\n')
        self.log_textbox.see(tk.END)
        self.log_textbox.configure(state="disabled")

    def update_state(self, update_data: Dict[str, Any]):
        """The main entry point for the AppController to update this panel."""
        update_type = update_data.get("type")
        data = update_data.get("data", {})

        if update_type == "task_start":
            self.clear_visuals()
            self.objective_label.configure(text=data.get('command', 'N/A'))
            self.add_log_message(f"Starting task: {data.get('command')}")
        elif update_type == "agent_thought":
            self.thought_label.configure(text=data.get("thought", "..."))
            self.tactic_label.configure(text=data.get("action", "..."))
            self._update_image_label(self.after_image_label, None)
            self.verification_label.configure(text="Observation Text: PENDING", text_color="gray")
            self.add_log_message(f"Thought: {data.get('thought')}")
            self.add_log_message(f"Action: {data.get('action')}")
        elif update_type == "tactic_before_image":
            self._update_image_label(self.before_image_label, data.get("image_np"))
        elif update_type == "tactic_after_image":
            observation_text = data.get("observation_text", "No textual observation.")
            self.verification_label.configure(text=f"Observation Text: {observation_text}", text_color=("gray10", "gray90"))
            self.add_log_message(f"Observation: {observation_text}")
        elif update_type == "task_end":
            self.add_log_message(f"Task finished. Status: {data.get('status')}")
            if data.get('status') == 'success':
                self.thought_label.configure(text=data.get('message'))
            else:
                self.thought_label.configure(text=f"Failure: {data.get('message')}")