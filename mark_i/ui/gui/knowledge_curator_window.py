import logging
import tkinter as tk
from tkinter import messagebox
from typing import Any, Callable, List, Dict
import copy

import customtkinter as ctk
from PIL import Image, ImageDraw

from mark_i.core.logging_setup import APP_ROOT_LOGGER_NAME

logger = logging.getLogger(f"{APP_ROOT_LOGGER_NAME}.ui.gui.knowledge_curator_window")

class KnowledgeCuratorWindow(ctk.CTkToplevel):
    """
    A GUI window for users to review, edit, and confirm knowledge candidates
    discovered by the KnowledgeDiscoveryEngine.
    """

    def __init__(self, master: Any, knowledge_candidates: List[Dict[str, Any]], screenshot_pil: Image.Image, save_callback: Callable[[List[Dict[str, Any]]], None], knowledge_base=None):
        super().__init__(master)
        self.title("Mark-I: Knowledge Discovery Curator")
        self.transient(master)
        self.grab_set()
        self.attributes("-topmost", True)
        self.geometry("800x600")
        self.minsize(600, 450)

        self.save_callback = save_callback
        self.knowledge_base = knowledge_base
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

        self.btn_ignore = ctk.CTkButton(
            button_frame, 
            text="Add to Ignore List", 
            command=self.ignore_candidate,
            fg_color="orange",
            hover_color="darkorange"
        )
        self.btn_ignore.pack(side="left", padx=5)

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

    def ignore_candidate(self):
        """Adds the current candidate to the perceptual ignore list."""
        if not (0 <= self.current_candidate_index < len(self.original_candidates)):
            return
            
        if not self.knowledge_base:
            messagebox.showerror("Error", "Knowledge base not available for ignore list operations.", parent=self)
            return
            
        candidate = self.original_candidates[self.current_candidate_index]
        description = candidate.get("description", "")
        
        if not description:
            messagebox.showwarning("No Description", "This candidate has no description to add to the ignore list.", parent=self)
            return
        
        # Add to knowledge base ignore list
        success = self.knowledge_base.add_to_perceptual_ignore_list(description)
        if success:
            messagebox.showinfo("Added to Ignore List", 
                              f"'{description}' will now be ignored during analysis.", parent=self)
            logger.info(f"User added to ignore list: {description}")
            self.next_candidate()
        else:
            messagebox.showerror("Error", "Failed to add item to ignore list.", parent=self)

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


class IgnoreListManagerWindow(ctk.CTkToplevel):
    """
    A dedicated window for viewing and managing the perceptual ignore list.
    """
    
    def __init__(self, master: Any, knowledge_base):
        super().__init__(master)
        self.title("Mark-I: Perceptual Ignore List Manager")
        self.transient(master)
        self.grab_set()
        self.attributes("-topmost", True)
        self.geometry("600x500")
        self.minsize(400, 300)
        
        self.knowledge_base = knowledge_base
        
        self._setup_ui()
        self._refresh_ignore_list()
        
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
        # Main frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header_label = ctk.CTkLabel(
            self.main_frame, 
            text="Perceptual Ignore List", 
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.header_label.grid(row=0, column=0, sticky="w", pady=(0, 15))
        
        # List frame with scrollbar
        list_frame = ctk.CTkFrame(self.main_frame)
        list_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollable text widget for ignore list
        self.ignore_list_text = ctk.CTkTextbox(
            list_frame,
            wrap="word",
            font=ctk.CTkFont(size=12)
        )
        self.ignore_list_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Button frame
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.grid(row=2, column=0, sticky="ew")
        
        # Add new item button
        self.btn_add = ctk.CTkButton(
            button_frame,
            text="Add New Item",
            command=self.add_new_item,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.btn_add.pack(side="left", padx=5, pady=10)
        
        # Clear all button
        self.btn_clear_all = ctk.CTkButton(
            button_frame,
            text="Clear All",
            command=self.clear_all_items,
            fg_color="red",
            hover_color="darkred"
        )
        self.btn_clear_all.pack(side="left", padx=5, pady=10)
        
        # Refresh button
        self.btn_refresh = ctk.CTkButton(
            button_frame,
            text="Refresh",
            command=self._refresh_ignore_list
        )
        self.btn_refresh.pack(side="right", padx=5, pady=10)
        
        # Close button
        self.btn_close = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.close_window
        )
        self.btn_close.pack(side="right", padx=5, pady=10)
    
    def _refresh_ignore_list(self):
        """Refreshes the display of the ignore list."""
        try:
            ignore_list = self.knowledge_base.get_perceptual_ignore_list()
            
            # Clear the text widget
            self.ignore_list_text.delete("1.0", tk.END)
            
            if not ignore_list:
                self.ignore_list_text.insert("1.0", "No items in ignore list.\n\nUse the 'Add New Item' button to add descriptions of visual elements you want the AI to ignore during analysis.")
            else:
                content = f"Currently ignoring {len(ignore_list)} items:\n\n"
                for i, item in enumerate(ignore_list, 1):
                    content += f"{i}. {item}\n\n"
                
                content += "\nTo remove an item, delete its text and click 'Save Changes'."
                self.ignore_list_text.insert("1.0", content)
                
        except Exception as e:
            logger.error(f"Error refreshing ignore list: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load ignore list: {e}", parent=self)
    
    def add_new_item(self):
        """Opens a dialog to add a new item to the ignore list."""
        dialog = ctk.CTkInputDialog(
            text="Enter a description of the visual element to ignore:",
            title="Add to Ignore List"
        )
        description = dialog.get_input()
        
        if description and description.strip():
            success = self.knowledge_base.add_to_perceptual_ignore_list(description.strip())
            if success:
                messagebox.showinfo("Success", f"Added '{description.strip()}' to ignore list.", parent=self)
                self._refresh_ignore_list()
            else:
                messagebox.showerror("Error", "Failed to add item to ignore list.", parent=self)
    
    def clear_all_items(self):
        """Clears all items from the ignore list after confirmation."""
        ignore_list = self.knowledge_base.get_perceptual_ignore_list()
        if not ignore_list:
            messagebox.showinfo("Nothing to Clear", "The ignore list is already empty.", parent=self)
            return
            
        if messagebox.askyesno(
            "Confirm Clear All", 
            f"Are you sure you want to remove all {len(ignore_list)} items from the ignore list?\n\nThis action cannot be undone.", 
            parent=self
        ):
            success = self.knowledge_base.clear_perceptual_ignore_list()
            if success:
                messagebox.showinfo("Success", "All items removed from ignore list.", parent=self)
                self._refresh_ignore_list()
            else:
                messagebox.showerror("Error", "Failed to clear ignore list.", parent=self)
    
    def close_window(self):
        self.grab_release()
        self.destroy()