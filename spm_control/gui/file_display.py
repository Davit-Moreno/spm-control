from spm_control.gui.modes import page_helpers
import customtkinter as ctk


class FileDisplay:
    def __init__(self, panel):
        self.panel = panel
        self._create_widgets()

    def _create_widgets(self):
        self.path_display = page_helpers.createFrame(
            self.panel,
            "path_display",
            [0, 0, 1, 0.5],
            outline=True
        )

        self.path_entry = ctk.CTkEntry(
            self.path_display,
            placeholder_text="Selected file path",
            text_color="#67E8F9"
        )
        self.path_entry.pack(fill="both", expand=True, padx=3, pady=3)
        self.path_entry.configure(state="readonly")

        self.secondary_display = page_helpers.createFrame(
            self.panel,
            "secondary_display",
            [0, 0.5, 1, 0.5],
            outline=True
        )

        self.secondary_entry = ctk.CTkEntry(
            self.secondary_display,
            placeholder_text="Compared file path",
            text_color="#67E8F9"
        )
        self.secondary_entry.pack(fill="both", expand=True, padx=3, pady=3)
        self.secondary_entry.configure(state="readonly")
        # Only shows the compared file, the getter below still reads the main path

    def set_path(self, file_path):
        self.path_entry.configure(state="normal")
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, str(file_path))
        self.path_entry.configure(state="readonly")

    def set_secondary_path(self, file_path):
        self.secondary_entry.configure(state="normal")
        self.secondary_entry.delete(0, "end")
        self.secondary_entry.insert(0, str(file_path))
        self.secondary_entry.configure(state="readonly")

    def get_path(self):
        return self.path_entry.get().strip()