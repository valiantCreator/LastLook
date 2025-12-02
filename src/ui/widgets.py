import customtkinter as ctk
from ..model.file_obj import FileObj, SyncStatus

class FileRow(ctk.CTkFrame):
    def __init__(self, master, file_obj: FileObj, on_click=None, on_toggle=None):
        super().__init__(master)
        self.file_obj = file_obj
        self.on_click = on_click
        self.on_toggle = on_toggle
        
        # Determine Color based on Status
        self.default_color = "transparent"
        if file_obj.status == SyncStatus.SYNCED:
            self.default_color = "#1c3a1c" # Faint Green
        elif file_obj.status == SyncStatus.MISSING:
            self.default_color = "#3a1c1c" # Faint Red
        elif file_obj.status == SyncStatus.TRANSFERRING:
            self.default_color = "#1c2e3a" # Faint Blue
            
        self.configure(fg_color=self.default_color, corner_radius=6)

        # Layout Grid
        self.grid_columnconfigure(2, weight=1) # Filename expands

        # 0. Checkbox (New!)
        self.checkbox = ctk.CTkCheckBox(self, text="", width=24, command=self._handle_toggle)
        self.checkbox.grid(row=0, column=0, padx=(10, 5), pady=5)

        # 1. Icon / Status
        icon_text = "✅" if file_obj.status == SyncStatus.SYNCED else "❌"
        if file_obj.status == SyncStatus.TRANSFERRING: icon_text = "⏳"
        
        self.lbl_icon = ctk.CTkLabel(self, text=icon_text, width=30)
        self.lbl_icon.grid(row=0, column=1, padx=5, pady=5)

        # 2. Filename
        self.lbl_name = ctk.CTkLabel(self, text=file_obj.filename, anchor="w", font=("Arial", 12, "bold"))
        self.lbl_name.grid(row=0, column=2, sticky="ew", padx=5)

        # 3. Size
        self.lbl_size = ctk.CTkLabel(self, text=file_obj.formatted_size, width=80, anchor="e", text_color="gray")
        self.lbl_size.grid(row=0, column=3, padx=10)

        # Click Event Bindings (Row Click = Select, Checkbox = Toggle)
        self.bind("<Button-1>", self._handle_click)
        self.lbl_icon.bind("<Button-1>", self._handle_click)
        self.lbl_name.bind("<Button-1>", self._handle_click)
        self.lbl_size.bind("<Button-1>", self._handle_click)

    def _handle_click(self, event):
        if self.on_click:
            self.on_click(self.file_obj)

    def _handle_toggle(self):
        if self.on_toggle:
            self.on_toggle(self.file_obj, self.checkbox.get())

    def set_selected(self, is_selected: bool):
        """Highlights the row Blue if selected (active focus)"""
        if is_selected:
            self.configure(fg_color="#2b4b6b", border_width=1, border_color="#3b8ed0")
        else:
            self.configure(fg_color=self.default_color, border_width=0)
    
    def set_checked(self, is_checked: bool):
        """Updates checkbox state programmatically"""
        if is_checked:
            self.checkbox.select()
        else:
            self.checkbox.deselect()