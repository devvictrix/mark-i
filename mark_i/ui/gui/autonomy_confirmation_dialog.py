import logging
import tkinter as tk
from typing import Any, Callable

import customtkinter as ctk

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.autonomy_confirmation_dialog")


class AutonomyConfirmationDialog(ctk.CTkToplevel):
    """
    A simple, non-blocking dialog to ask the user for confirmation
    for an AI-proposed autonomous action.
    """

    def __init__(self, master: Any, plan_text: str, confirmation_callback: Callable[[bool], None]):
        """
        Initializes the confirmation dialog.

        Args:
            master: The parent widget.
            plan_text: The human-readable plan to display to the user.
            confirmation_callback: The function to call with the result (True for Allow, False for Deny).
        """
        super().__init__(master)
        self.confirmation_callback = confirmation_callback

        self.title("Mark-I: Assistant Suggestion")
        self.transient(master)
        self.attributes("-topmost", True)
        self.geometry("450x220")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self._on_deny)  # Closing the window is the same as denying

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.main_frame, text="MARK-I proposes the following action:", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="ew", pady=(0, 5))

        plan_display_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Proposed Plan")
        plan_display_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        ctk.CTkLabel(plan_display_frame, text=plan_text, wraplength=380, justify="left").pack(padx=5, pady=5)

        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.btn_deny = ctk.CTkButton(button_frame, text="Deny", command=self._on_deny, fg_color="firebrick1", hover_color="firebrick3")
        self.btn_deny.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="e")

        self.btn_allow = ctk.CTkButton(button_frame, text="Allow", command=self._on_allow, font=ctk.CTkFont(weight="bold"))
        self.btn_allow.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="w")

        self.after(100, self._center_on_screen)
        self.lift()
        self.focus_force()

    def _center_on_screen(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = self.winfo_width()
        win_h = self.winfo_height()
        x_pos = (screen_w // 2) - (win_w // 2)
        y_pos = (screen_h // 2) - (win_h // 2)
        self.geometry(f"+{max(0, x_pos)}+{max(0, y_pos)}")

    def _on_allow(self):
        logger.info("User ALLOWED the autonomous action.")
        self.confirmation_callback(True)
        self.destroy()

    def _on_deny(self):
        logger.info("User DENIED the autonomous action.")
        self.confirmation_callback(False)
        self.destroy()
