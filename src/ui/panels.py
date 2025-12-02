import customtkinter as ctk
import shutil
from typing import List
from .widgets import FileRow
from ..model.file_obj import FileObj, SyncStatus

class FileListPanel(ctk.CTkFrame):
    def __init__(self, master, title, is_dest=False, on_select_missing=None, on_background_click=None):
        super().__init__(master)
        self.is_dest = is_dest
        self.rows = [] 
        self.on_select_missing = on_select_missing
        self.on_background_click = on_background_click # NEW Callback

        # Header
        self.lbl_title = ctk.CTkLabel(self, text=title, font=("Arial", 14, "bold"))
        self.lbl_title.pack(pady=(10, 5), padx=10, anchor="w")

        # Storage Bar
        self.progress_bar = ctk.CTkProgressBar(self, height=8)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        
        # Scrollable Area
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Files")
        self.scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        # BINDING THE VOID:
        # We bind to the canvas to catch clicks that miss the rows
        # We use a lambda to ignore the event object
        if self.on_background_click:
            self.scroll_frame.bind("<Button-1>", lambda e: self.on_background_click())
            # Depending on CTk version, we might need to bind to the canvas directly
            try:
                self.scroll_frame._parent_canvas.bind("<Button-1>", lambda e: self.on_background_click())
            except:
                pass 

        # Footer (Only for Source Pane)
        if not is_dest:
            self.btn_select_missing = ctk.CTkButton(
                self, 
                text="Select All Missing Files", 
                fg_color="transparent", 
                border_width=1, 
                text_color="gray",
                command=self._handle_select_missing
            )
            self.btn_select_missing.pack(fill="x", padx=10, pady=10)

    def _handle_select_missing(self):
        if self.on_select_missing:
            self.on_select_missing()

    def update_storage(self, path):
        if not path: return
        try:
            total, used, free = shutil.disk_usage(path)
            percent = used / total
            self.progress_bar.set(percent)
            color = "#1f6aa5" 
            if percent > 0.9: color = "#c42b1c"
            self.progress_bar.configure(progress_color=color)
        except:
            self.progress_bar.set(0)

    def render_files(self, files: List[FileObj], on_row_click, on_row_toggle, selected_ids):
        """Clears list and re-draws FileRows"""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.rows.clear()

        for file_obj in files:
            row = FileRow(self.scroll_frame, file_obj, on_click=on_row_click, on_toggle=on_row_toggle)
            row.pack(fill="x", pady=2, padx=2)
            
            if selected_ids and file_obj.id in selected_ids:
                row.set_checked(True)
            
            self.rows.append(row)
            
    def highlight_file(self, file_id):
        """Finds a row with this ID and highlights it visually"""
        for row in self.rows:
            if row.file_obj.id == file_id:
                row.set_selected(True)
            else:
                row.set_selected(False)

class InspectorPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=250)
        self.lbl_header = ctk.CTkLabel(self, text="INSPECTOR", font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_header.pack(pady=20)

        self.preview_box = ctk.CTkFrame(self, height=150, fg_color="#1a1a1a")
        self.preview_box.pack(fill="x", padx=20, pady=10)
        self.lbl_preview = ctk.CTkLabel(self.preview_box, text="No Selection")
        self.lbl_preview.place(relx=0.5, rely=0.5, anchor="center")

        self.info_label = ctk.CTkLabel(self, text="", justify="left", anchor="w")
        self.info_label.pack(fill="x", padx=20, pady=20)

    def show_file(self, file_obj: FileObj):
        self.lbl_preview.configure(text=file_obj.determine_type(file_obj.filename).name)
        details = (
            f"FILENAME:\n{file_obj.filename}\n\n"
            f"SIZE:\n{file_obj.formatted_size}\n\n"
            f"STATUS:\n{file_obj.status.value.upper()}\n\n"
            f"PATH:\n{file_obj.path}"
        )
        self.info_label.configure(text=details)

    def show_batch(self, count, total_size_bytes):
        self.lbl_preview.configure(text=f"{count} Items")
        size_str = f"{total_size_bytes} B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if total_size_bytes < 1024:
                size_str = f"{total_size_bytes:.2f} {unit}"
                break
            total_size_bytes /= 1024
        details = (
            f"BATCH SELECTION\n\n"
            f"ITEMS SELECTED:\n{count}\n\n"
            f"TOTAL SIZE:\n{size_str}\n\n"
        )
        self.info_label.configure(text=details)

    def clear_view(self):
        """Resets the inspector to empty state"""
        self.lbl_preview.configure(text="No Selection")
        self.info_label.configure(text="")