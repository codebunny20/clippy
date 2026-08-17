import customtkinter as ctk
import tkinter as tk
from logic import ClipboardHistoryManager


class ClipboardViewer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Clippy - Clipboard History")
        self.geometry("760x500")
        self.minsize(680, 440)
        self.configure(fg_color="#0f172a")
        self.is_pinned = False

        self.history = ClipboardHistoryManager(max_items=100)
        self.poll_interval_ms = 500
        self.visible_indices = []
        self.help_window = None

        # === Top Bar ===
        top_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=14)
        top_frame.pack(fill="x", padx=14, pady=(14, 8))

        title_block = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_block.pack(side="left", padx=12, pady=10)

        title_label = ctk.CTkLabel(
            title_block,
            text="Clippy",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f8fafc",
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_block,
            text="Clipboard timeline",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        subtitle_label.pack(anchor="w")

        actions = ctk.CTkFrame(top_frame, fg_color="transparent")
        actions.pack(side="right", padx=10, pady=10)

        self.pin_btn = ctk.CTkButton(
            actions,
            text="Pin",
            width=86,
            fg_color="#334155",
            hover_color="#475569",
            command=self.toggle_pin,
        )
        self.pin_btn.pack(side="right", padx=(8, 0))

        refresh_btn = ctk.CTkButton(
            actions,
            text="Refresh",
            width=90,
            fg_color="#0ea5e9",
            hover_color="#0284c7",
            command=self.refresh_history,
        )
        refresh_btn.pack(side="right", padx=(8, 0))

        clear_btn = ctk.CTkButton(
            actions,
            text="Clear",
            width=80,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.clear_history,
        )
        clear_btn.pack(side="right")

        help_btn = ctk.CTkButton(
            actions,
            text="Help",
            width=70,
            fg_color="#6b7280",
            hover_color="#4b5563",
            command=self.show_help,
        )
        help_btn.pack(side="right", padx=(8, 0))

        # === Main Layout ===
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

        history_panel = ctk.CTkFrame(main_frame, fg_color="#111827", corner_radius=14)
        history_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        history_header = ctk.CTkFrame(history_panel, fg_color="transparent")
        history_header.pack(fill="x", padx=12, pady=(12, 8))

        history_label = ctk.CTkLabel(
            history_header,
            text="History",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e2e8f0",
        )
        history_label.pack(side="left")

        self.count_label = ctk.CTkLabel(
            history_header,
            text="0 items",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        self.count_label.pack(side="right")

        search_frame = ctk.CTkFrame(history_panel, fg_color="transparent")
        search_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="Search history...",
            fg_color="#0b1220",
            border_color="#334155",
            text_color="#e2e8f0",
        )
        self.search_entry.pack(fill="x")

        # Left: List of clipboard items
        self.listbox = tk.Listbox(
            history_panel,
            height=20,
            bg="#0b1220",
            fg="#e2e8f0",
            selectbackground="#0ea5e9",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            font=("Segoe UI", 11),
        )
        self.listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.listbox.bind("<<ListboxSelect>>", self.show_preview)

        self.empty_state_label = ctk.CTkLabel(
            history_panel,
            text="No clipboard items yet",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=13),
            anchor="center",
        )
        self.empty_state_label.pack_forget()

        preview_panel = ctk.CTkFrame(main_frame, fg_color="#111827", corner_radius=14)
        preview_panel.grid(row=0, column=1, sticky="nsew")

        preview_header = ctk.CTkFrame(preview_panel, fg_color="transparent")
        preview_header.pack(fill="x", padx=12, pady=(12, 8))

        preview_label = ctk.CTkLabel(
            preview_header,
            text="Preview",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e2e8f0",
        )
        preview_label.pack(side="left")

        self.copy_btn = ctk.CTkButton(
            preview_header,
            text="Copy",
            width=76,
            fg_color="#22c55e",
            hover_color="#16a34a",
            command=self.copy_selected,
        )
        self.copy_btn.pack(side="right", padx=(8, 0))

        self.delete_btn = ctk.CTkButton(
            preview_header,
            text="Delete",
            width=76,
            fg_color="#f97316",
            hover_color="#ea580c",
            command=self.delete_selected,
        )
        self.delete_btn.pack(side="right", padx=(8, 0))

        self.pin_item_btn = ctk.CTkButton(
            preview_header,
            text="Pin Item",
            width=88,
            fg_color="#6366f1",
            hover_color="#4f46e5",
            command=self.toggle_selected_pin,
        )
        self.pin_item_btn.pack(side="right")

        # Right: Preview box
        self.preview = ctk.CTkTextbox(
            preview_panel,
            width=250,
            fg_color="#0b1220",
            border_width=0,
            text_color="#f8fafc",
            font=ctk.CTkFont(size=13),
            corner_radius=10,
        )
        self.preview.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            anchor="w",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(fill="x", padx=16, pady=(0, 10))

        self.bind("<Return>", self.on_enter_pressed)
        self.bind("<Delete>", self.on_delete_pressed)
        self.bind("<Control-f>", self.on_focus_search)
        self.bind("<Control-l>", self.on_clear_search)
        self.bind("<Escape>", self.on_escape_pressed)

        # Load initial items
        self.load_items(fallback_to_first=True)
        self.after(100, self.check_clipboard)

    def load_items(self, selected_index=None, fallback_to_first=False):
        self.listbox.delete(0, tk.END)
        query = self.search_var.get() if hasattr(self, "search_var") else ""
        self.visible_indices = self.history.get_filtered_indices(query)
        all_items = self.history.get_history()
        for index in self.visible_indices:
            item = all_items[index]
            prefix = "[PIN] " if item.pinned else ""
            short_text = item.text[:36] + ("..." if len(item.text) > 36 else "")
            display = prefix + short_text
            self.listbox.insert(tk.END, display)
        total_count = len(all_items)
        visible_count = len(self.visible_indices)
        if query.strip():
            self.count_label.configure(text=f"{visible_count}/{total_count} shown")
        else:
            self.count_label.configure(text=f"{total_count} item" if total_count == 1 else f"{total_count} items")

        if visible_count == 0:
            self.preview.delete("1.0", "end")
            self.preview.insert("end", "No item selected")
            self.pin_item_btn.configure(text="Pin Item")
            self.update_action_buttons(False)
            self.empty_state_label.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            self.listbox.pack_forget()
            return

        self.empty_state_label.pack_forget()
        self.listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        if selected_index is not None and selected_index in self.visible_indices:
            self.select_visible_index(self.visible_indices.index(selected_index))
        elif fallback_to_first:
            self.select_first_item()
        else:
            self.update_action_buttons(False)

    def update_preview(self, text):
        self.preview.delete("1.0", "end")
        self.preview.insert("end", text)

    def update_action_buttons(self, has_selection):
        button_state = "normal" if has_selection else "disabled"
        self.copy_btn.configure(state=button_state)
        self.delete_btn.configure(state=button_state)
        self.pin_item_btn.configure(state=button_state)

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.attributes("-topmost", self.is_pinned)
        self.pin_btn.configure(text="Unpin" if self.is_pinned else "Pin")
        self.set_status("Pinned on top" if self.is_pinned else "Pin disabled")

    def set_status(self, message):
        self.status_label.configure(text=message)

    def copy_selected(self):
        selected_index = self.get_selected_history_index()
        if selected_index is None:
            self.set_status("Select an item to copy")
            return

        try:
            text = self.history.get_item(selected_index).text
            self.clipboard_clear()
            self.clipboard_append(text)
            self.set_status("Copied selected item to clipboard")
        except Exception:
            self.set_status("Clipboard is unavailable right now")

    def delete_selected(self):
        selected_index = self.get_selected_history_index()
        if selected_index is None:
            self.set_status("Select an item to delete")
            return

        self.history.delete_item(selected_index)
        next_index = min(selected_index, len(self.history.get_history()) - 1)
        self.load_items(selected_index=next_index, fallback_to_first=True)
        self.set_status("Selected item deleted")

    def toggle_selected_pin(self):
        selected_index = self.get_selected_history_index()
        if selected_index is None:
            self.set_status("Select an item to pin")
            return

        selected_text = self.history.get_item(selected_index).text
        is_now_pinned = self.history.toggle_pinned(selected_index)
        self.load_items(selected_index=self.find_history_index_by_text(selected_text), fallback_to_first=True)
        if is_now_pinned:
            self.set_status("Selected item pinned")
        else:
            self.set_status("Selected item unpinned")

    def on_search_change(self, *_):
        self.load_items(selected_index=self.get_selected_history_index(), fallback_to_first=True)

    def get_selected_history_index(self):
        selection = self.listbox.curselection()
        if not selection:
            return None

        visible_index = selection[0]
        if visible_index < 0 or visible_index >= len(self.visible_indices):
            return None
        return self.visible_indices[visible_index]

    def find_history_index_by_text(self, text):
        for index, item in enumerate(self.history.get_history()):
            if item.text == text:
                return index
        return None

    def show_selected_preview(self):
        selected_index = self.get_selected_history_index()
        if selected_index is None:
            self.preview.delete("1.0", "end")
            self.preview.insert("end", "No item selected")
            self.pin_item_btn.configure(text="Pin Item")
            self.update_action_buttons(False)
            return

        item = self.history.get_item(selected_index)
        self.update_preview(item.text)
        self.pin_item_btn.configure(text="Unpin Item" if item.pinned else "Pin Item")
        self.update_action_buttons(True)

    def select_visible_index(self, visible_index):
        if visible_index < 0 or visible_index >= self.listbox.size():
            self.update_action_buttons(False)
            return

        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(visible_index)
        self.listbox.activate(visible_index)
        self.listbox.see(visible_index)
        self.show_selected_preview()

    def select_first_item(self):
        if self.listbox.size() == 0:
            self.preview.delete("1.0", "end")
            self.preview.insert("end", "No item selected")
            self.pin_item_btn.configure(text="Pin Item")
            self.update_action_buttons(False)
            return

        self.select_visible_index(0)

    def refresh_history(self):
        try:
            if self.history.poll_system_clipboard(self):
                self.load_items(selected_index=0, fallback_to_first=True)
                self.set_status("Refreshed and captured new clipboard text")
            elif self.listbox.size() > 0:
                self.show_selected_preview()
                self.set_status("No new clipboard text")
            else:
                self.set_status("Clipboard is empty")
        except Exception:
            self.set_status("Clipboard is unavailable right now")

    def clear_history(self):
        self.history.clear()
        self.load_items()
        self.preview.delete("1.0", "end")
        self.set_status("History cleared")

    def check_clipboard(self):
        try:
            if self.history.poll_system_clipboard(self):
                self.load_items(selected_index=0, fallback_to_first=True)
                self.set_status("New clipboard text captured")
        except Exception:
            self.set_status("Clipboard check failed; retrying")
        self.after(self.poll_interval_ms, self.check_clipboard)

    def on_enter_pressed(self, event=None):
        if not self.can_use_history_shortcuts():
            return None
        self.copy_selected()
        return "break"

    def on_delete_pressed(self, event=None):
        if not self.can_use_history_shortcuts():
            return None
        self.delete_selected()
        return "break"

    def on_focus_search(self, event=None):
        self.search_entry.focus()
        self.search_entry.icursor("end")
        return "break"

    def on_clear_search(self, event=None):
        self.search_var.set("")
        self.search_entry.focus()
        self.set_status("Search cleared")
        return "break"

    def on_escape_pressed(self, event=None):
        focused_widget = self.focus_get()
        if focused_widget is not None and focused_widget.winfo_class() == "TEntry":
            self.search_entry.selection_clear()
        self.listbox.selection_clear(0, tk.END)
        self.preview.delete("1.0", "end")
        self.pin_item_btn.configure(text="Pin Item")
        self.update_action_buttons(False)
        self.set_status("Selection cleared")
        return "break"

    def can_use_history_shortcuts(self):
        focused_widget = self.focus_get()
        if focused_widget is None:
            return True

        widget_class = focused_widget.winfo_class()
        return widget_class not in {"Entry", "Text", "TEntry"}

    def show_help(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.focus()
            return

        help_window = ctk.CTkToplevel(self)
        help_window.title("Clippy Help")
        help_window.geometry("430x320")
        help_window.transient(self)
        help_window.grab_set()
        help_window.resizable(False, False)
        help_window.configure(fg_color="#111827")
        help_window.protocol("WM_DELETE_WINDOW", self.close_help)
        self.help_window = help_window

        help_label = ctk.CTkLabel(
            help_window,
            text="Keyboard Shortcuts",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#f8fafc",
        )
        help_label.pack(pady=(18, 10))

        shortcuts = [
            ("Enter", "Copy the selected item to the clipboard"),
            ("Delete", "Delete the selected item from history"),
            ("Ctrl + F", "Focus the search box"),
            ("Esc", "Clear the current selection"),
            ("Ctrl + L", "Clear the search field"),
        ]

        for key, explanation in shortcuts:
            row = ctk.CTkFrame(help_window, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=6)

            key_label = ctk.CTkLabel(row, text=key, width=14, anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
            key_label.pack(side="left")

            desc_label = ctk.CTkLabel(row, text=explanation, anchor="w", text_color="#cbd5e1")
            desc_label.pack(side="left", fill="x", expand=True)

        close_btn = ctk.CTkButton(help_window, text="Close", command=self.close_help)
        close_btn.pack(pady=(12, 18))
        close_btn.focus()

    def close_help(self):
        if self.help_window is None:
            return

        if self.help_window.winfo_exists():
            self.help_window.destroy()
        self.help_window = None

    def show_preview(self, event):
        self.show_selected_preview()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = ClipboardViewer()
    app.mainloop()
