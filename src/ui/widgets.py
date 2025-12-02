import customtkinter as ctk
from PIL import Image
from ..model.file_obj import FileObj, SyncStatus
from ..utils.assets import get_asset_path

class FileRow(ctk.CTkFrame):
    # Cache images at the class level so we don't reload from disk 1000 times
    IMG_CHECK = None
    IMG_ERROR = None

    def __init__(self, master, file_obj: FileObj, on_click=None, on_toggle=None):
        super().__init__(master)
        self.file_obj = file_obj
        self.on_click = on_click
        self.on_toggle = on_toggle
        
        # Load Images Once (Singleton Pattern)
        if FileRow.IMG_CHECK is None:
            try:
                FileRow.IMG_CHECK = ctk.CTkImage(Image.open(get_asset_path("check.png")), size=(20, 20))
                FileRow.IMG_ERROR = ctk.CTkImage(Image.open(get_asset_path("error.png")), size=(20, 20))
            except Exception as e:
                print(f"Warning: Could not load icons: {e}")

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
        self.grid_columnconfigure(2, weight=1) 

        # 0. Checkbox
        self.checkbox = ctk.CTkCheckBox(self, text="", width=24, command=self._handle_toggle)
        self.checkbox.grid(row=0, column=0, padx=(10, 5), pady=5)

        # 1. Icon (Image or Text Fallback)
        self.lbl_icon = ctk.CTkLabel(self, text="", width=30)
        
        if file_obj.status == SyncStatus.SYNCED and FileRow.IMG_CHECK:
            self.lbl_icon.configure(image=FileRow.IMG_CHECK)
        elif file_obj.status == SyncStatus.MISSING and FileRow.IMG_ERROR:
            self.lbl_icon.configure(image=FileRow.IMG_ERROR)
        else:
            # Fallback to text (or Spinner for transferring)
            icon_text = "✅" if file_obj.status == SyncStatus.SYNCED else "❌"
            if file_obj.status == SyncStatus.TRANSFERRING: icon_text = "⏳"
            self.lbl_icon.configure(text=icon_text)
            
        self.lbl_icon.grid(row=0, column=1, padx=5, pady=5)

        # 2. Filename
        self.lbl_name = ctk.CTkLabel(self, text=file_obj.filename, anchor="w", font=("Arial", 12, "bold"))
        self.lbl_name.grid(row=0, column=2, sticky="ew", padx=5)

        # 3. Size
        self.lbl_size = ctk.CTkLabel(self, text=file_obj.formatted_size, width=80, anchor="e", text_color="gray")
        self.lbl_size.grid(row=0, column=3, padx=10)

        # Click Event Bindings
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
        if is_selected:
            self.configure(fg_color="#2b4b6b", border_width=1, border_color="#3b8ed0")
        else:
            self.configure(fg_color=self.default_color, border_width=0)
    
    def set_checked(self, is_checked: bool):
        if is_checked:
            self.checkbox.select()
        else:
            self.checkbox.deselect()