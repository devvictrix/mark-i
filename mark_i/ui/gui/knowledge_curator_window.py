import logging
import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable, List, Dict, Optional
import copy

import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.knowledge_curator_window")

class KnowledgeCuratorWindow(ctk.CTkToplevel):
    """
    A GUI window for users to review, edit, and confirm knowledge candidates
    discovered by the KnowledgeDiscoveryEngine.
    """

    def __init__(self, master: Any, knowledge_candidates: List[Dict[str, Any]], screenshot_pil: Image.Image, save_callback: Callable[[List[Dict[str, Any]]], None]):
        super().__init__(master)
        self.title("Mark-I: Knowledge Discovery Curator")
        self.transient(master)
        self.grab_set()
        self.attributes("-topmost", True)
        self.geometry("800x600")
        self.minsize(600, 450)

        self.save_callback = save_callback
        self.original_candidates = copy.deepcopy(knowledge_candidates)
        self.screenshot_pil = screenshot_pil
        self.processed_candidates: List[Dict[str, Any]] = []

        self.current_candidate_index = 0

        self._setup_ui()
        self.load_candidate(self.current_candidate_index)

        self.protocol("WM_DELETE_WINDOW", self.close_window)
        self.after(100, self._center_on_master)

    def _center_on_master(self):
        self.update_idletasks()
        if self.master and self.master.winfo_exists():
            x = self.master.winfo_x() + (self.master.winfo_width() // 2) - (self.winfo_width() // 2)
            y = self.master.winfo_y() + (self.master.winfo_height() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        self.lift()

    def _setup_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.header_label = ctk.CTkLabel(self.main_frame, text="Review Discovered Knowledge (1/N)", font=ctk.CTkFont(size=16, weight="bold"))
        self.header_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # Left Panel for Image Context
        image_frame = ctk.CTkFrame(self.main_frame)
        image_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        image_frame.grid_rowconfigure(0, weight=1)
        image_frame.grid_columnconfigure(0, weight=1)
        self.image_preview_label = ctk.CTkLabel(image_frame, text="")
        self.image_preview_label.pack(fill="both", expand=True, padx=5, pady=5)

        # Right Panel for Details
        details_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        details_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        details_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(details_frame, text="Type:").grid(row=0, column=0, sticky="w", pady=2)
        self.type_label = ctk.CTkLabel(details_frame, text="N/A", anchor="w")
        self.type_label.grid(row=0, column=1, sticky="ew", pady=2)

        ctk.CTkLabel(details_frame, text="Description:").grid(row=1, column=0, sticky="nw", pady=2)
        self.description_label = ctk.CTkLabel(details_frame, text="N/A", wraplength=300, justify="left", anchor="w")
        self.description_label.grid(row=1, column=1, sticky="ew", pady=2)

        ctk.CTkLabel(details_frame, text="Suggested Name:").grid(row=2, column=0, sticky="w", pady=2)
        self.name_entry = ctk.CTkEntry(details_frame)
        self.name_entry.grid(row=2, column=1, sticky="ew", pady=2)

        self.value_label = ctk.CTkLabel(details_frame, text="Your Value:")
        self.value_entry = ctk.CTkEntry(details_frame, placeholder_text="Enter the value for this field...")

        # Navigation and Action Buttons
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_frame.grid_columnconfigure(1, weight=1)

        self.btn_skip = ctk.CTkButton(button_frame, text="Skip", command=self.skip_candidate)
        self.btn_skip.pack(side="left", padx=5)

        self.btn_approve = ctk.CTkButton(button_frame, text="Approve & Next", command=self.approve_candidate, font=ctk.CTkFont(weight="bold"))
        self.btn_approve.pack(side="right", padx=5)

    def load_candidate(self, index: int):
        self.header_label.configure(text=f"Review Discovered Knowledge ({index + 1}/{len(self.original_candidates)})")
        candidate = self.original_candidates[index]
        
        self.type_label.configure(text=str(candidate.get("type", "unknown")))
        self.description_label.configure(text=str(candidate.get("description", "No description.")))
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, str(candidate.get("name_suggestion", "")))

        if candidate.get("type") == "data_field":
            self.value_label.grid(row=3, column=0, sticky="w", pady=2)
            self.value_entry.grid(row=3, column=1, sticky="ew", pady=2)
            self.value_entry.delete(0, tk.END)
        else:
            self.value_label.grid_remove()
            self.value_entry.grid_remove()

        bbox = candidate.get("bounding_box")
        if isinstance(bbox, list) and len(bbox) == 4:
            img_copy = self.screenshot_pil.copy()
            draw = ImageDraw.Draw(img_copy)
            x, y, w, h = bbox
            draw.rectangle([x, y, x + w, y + h], outline="lime", width=3)
            
            preview_img = img_copy.crop((x - 50, y - 50, x + w + 50, y + h + 50))
            preview_img.thumbnail((400, 300), Image.Resampling.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=preview_img, dark_image=preview_img, size=preview_img.size)
            self.image_preview_label.configure(image=ctk_image, text="")
        else:
            self.image_preview_label.configure(image=None, text="No Bounding Box")

    def approve_candidate(self):
        if not (0 <= self.current_candidate_index < len(self.original_candidates)):
            return

        candidate = self.original_candidates[self.current_candidate_index]
        confirmed_name = self.name_entry.get().strip()

        if not confirmed_name:
            messagebox.showwarning("Name Required", "Please provide a name for this knowledge item.", parent=self)
            return

        processed_candidate = {"type": candidate["type"], "name": confirmed_name}

        if candidate.get("type") == "data_field":
            value = self.value_entry.get().strip()
            if not value:
                messagebox.showwarning("Value Required", "Please provide a value for this data field.", parent=self)
                return
            processed_candidate["value"] = value
        
        processed_candidate["description"] = candidate.get("description")
        self.processed_candidates.append(processed_candidate)
        self.next_candidate()

    def skip_candidate(self):
        if not (0 <= self.current_candidate_index < len(self.original_candidates)):
            return
        logger.info(f"User skipped knowledge candidate: {self.original_candidates[self.current_candidate_index].get('name_suggestion')}")
        self.next_candidate()

    def next_candidate(self):
        self.current_candidate_index += 1
        if self.current_candidate_index < len(self.original_candidates):
            self.load_candidate(self.current_candidate_index)
        else:
            self.finish_curation()
        
    def finish_curation(self):
        if self.processed_candidates:
            if messagebox.askyesno("Save Knowledge?", f"You have approved {len(self.processed_candidates)} new knowledge items. Save them to your knowledge_base.json?", parent=self):
                self.save_callback(self.processed_candidates)
        else:
            messagebox.showinfo("Curation Complete", "No new knowledge items were approved.", parent=self)
        self.close_window()

    def close_window(self):
        self.grab_release()
        self.destroy()