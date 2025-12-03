import customtkinter as ctk
import shutil
import tkinter
import concurrent.futures
from typing import List
from .widgets import FileRow
from ..model.file_obj import FileObj, SyncStatus, FileType
from ..core.thumbnails import ThumbnailGenerator

class FileListPanel(ctk.CTkFrame):
    def __init__(self, master, title, is_dest=False, on_select_missing=None, on_background_click=None):
        super().__init__(master)
        self.is_dest = is_dest
        self.rows = [] 
        self.on_select_missing = on_select_missing
        self.on_background_click = on_background_click

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
        
        if self.on_background_click:
            self.scroll_frame.bind("<Button-1>", lambda e: self.on_background_click())
            try:
                self.scroll_frame._parent_canvas.bind("<Button-1>", lambda e: self.on_background_click())
            except:
                pass 

        # Footer
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
        
        # STATE MANAGEMENT
        self.current_image = None
        self.active_file_id = None
        self.thumbnail_cache = {} # MEMORY CACHE: {file_path: CTkImage}
        
        # THREAD POOL: 1 Worker to process thumbnails one by one without freezing UI
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # UI LAYOUT
        self.preview_box = ctk.CTkFrame(self, height=150, fg_color="#1a1a1a")
        self.preview_box.pack(fill="x", padx=20, pady=10)
        self._create_preview_label()

        self.info_label = ctk.CTkLabel(self, text="", justify="left", anchor="w")
        self.info_label.pack(fill="x", padx=20, pady=20)

    def _create_preview_label(self):
        self.lbl_preview = ctk.CTkLabel(self.preview_box, text="No Selection")
        self.lbl_preview.place(relx=0.5, rely=0.5, anchor="center")

    def _rebuild_label(self):
        try:
            self.lbl_preview.destroy()
        except:
            pass
        self._create_preview_label()

    def show_file(self, file_obj: FileObj):
        self.active_file_id = file_obj.id

        # 1. Reset UI (Safe Mode)
        try:
            self.lbl_preview.configure(image=None, text=file_obj.file_type.name)
            self.current_image = None
        except tkinter.TclError:
            self._rebuild_label()
            self.lbl_preview.configure(text=file_obj.file_type.name)

        # 2. THUMBNAIL LOGIC
        if file_obj.file_type == FileType.VIDEO:
            # CHECK CACHE FIRST (Instant Load)
            if file_obj.path in self.thumbnail_cache:
                self._apply_image(self.thumbnail_cache[file_obj.path])
            else:
                # CACHE MISS: Offload to Thread
                try:
                    self.lbl_preview.configure(text="Generating...", image=None)
                    self.executor.submit(self._threaded_generation, file_obj.path, file_obj.id)
                except Exception:
                    self._rebuild_label()
                    self.lbl_preview.configure(text="Generating...")
        
        # 3. METADATA
        details = (
            f"FILENAME:\n{file_obj.filename}\n\n"
            f"SIZE:\n{file_obj.formatted_size}\n\n"
            f"STATUS:\n{file_obj.status.value.upper()}\n\n"
            f"PATH:\n{file_obj.path}"
        )
        self.info_label.configure(text=details)

    def _threaded_generation(self, path, requested_id):
        """Runs on Background Thread - Extracts Raw PIL Image"""
        if self.active_file_id != requested_id:
            return # Cancel if user clicked away
            
        try:
            pil_image = ThumbnailGenerator.generate_thumbnail(path)
            
            # Send result back to Main Thread for UI Update
            if pil_image:
                self.after(0, lambda: self._on_thumbnail_ready(path, requested_id, pil_image))
            else:
                self.after(0, lambda: self._on_thumbnail_failed(requested_id))
        except Exception as e:
            print(f"BG Thread Error: {e}")

    def _on_thumbnail_ready(self, path, requested_id, pil_image):
        """Runs on Main Thread - Converts to CTkImage and updates UI"""
        # Create CTkImage (must be on main thread)
        ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(200, 110))
        
        # Store in Cache
        self.thumbnail_cache[path] = ctk_img

        # Update UI only if user is still looking at this file
        if self.active_file_id == requested_id:
            self._apply_image(ctk_img)

    def _on_thumbnail_failed(self, requested_id):
        if self.active_file_id == requested_id:
            try:
                self.lbl_preview.configure(text="No Preview", image=None)
            except: 
                pass

    def _apply_image(self, ctk_img):
        try:
            self.current_image = ctk_img # Anchor
            self.lbl_preview.configure(image=self.current_image, text="")
        except tkinter.TclError:
            self._rebuild_label()
            self.current_image = ctk_img
            self.lbl_preview.configure(image=self.current_image, text="")

    def show_batch(self, count, total_size_bytes):
        self.active_file_id = None
        try:
            self.lbl_preview.configure(image=None, text=f"{count} Items")
            self.current_image = None
        except tkinter.TclError:
            self._rebuild_label()
            self.lbl_preview.configure(image=None, text=f"{count} Items")

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
        self.active_file_id = None
        try:
            self.lbl_preview.configure(image=None, text="No Selection")
            self.current_image = None
            self.info_label.configure(text="")
        except tkinter.TclError:
            pass