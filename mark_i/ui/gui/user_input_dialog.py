import tkinter as tk
from typing import Any, Callable

import customtkinter as ctk

class UserInputDialog(ctk.CTkToplevel):
    """
    A simple modal dialog to get text input from the user, prompted by the AI.
    This is the GUI front-end for the `ask_user` tool.
    """
    def __init__(self, master: Any, title: str, prompt: str):
        super().__init__(master)
        self.title(title)
        self.transient(master)
        self.grab_set()
        self.attributes("-topmost", True)
        self.geometry("450x200")
        
        self._user_response: str = ""

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.main_frame, text=prompt, wraplength=400, justify="left").grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.entry = ctk.CTkEntry(self.main_frame)
        self.entry.grid(row=1, column=0, sticky="ew", pady=5)
        self.entry.bind("<Return>", self._on_submit)
        
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="e", pady=(10, 0))
        
        ctk.CTkButton(button_frame, text="Cancel", command=self._on_cancel).pack(side="left", padx=(0, 5))
        ctk.CTkButton(button_frame, text="Submit", command=self._on_submit, font=ctk.CTkFont(weight="bold")).pack(side="left")

        self.after(100, self.entry.focus_set)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Center window
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self.wait_window(self)

    def _on_submit(self, event=None):
        self._user_response = self.entry.get().strip()
        self.grab_release()
        self.destroy()

    def _on_cancel(self):
        self._user_response = ""
        self.grab_release()
        self.destroy()

    def get_input(self) -> str:
        return self._user_response