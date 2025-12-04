import customtkinter as ctk
import shutil
import tkinter
import concurrent.futures
from typing import List, Generator
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
        
        # --- PERFORMANCE TRACKING ---
        self.current_file_hashes = [] 
        self.row_map = {} 
        self.active_highlight_id = None 
        
        # The Generator: Keeps track of where we are in the rendering loop
        self.render_generator: Generator = None
        # The Task ID: Allows us to cancel the loop if the user switches folders fast
        self.render_task_id = None
        
        # --- CAPACITY TRACKING ---
        self.free_space = 0
        self.total_space = 0

        # --- UI LAYOUT ---
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
        
        # Bind background click to deselect
        if self.on_background_click:
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

        # PRE-WARMER: Build 200 invisible rows on startup so the first click feels instant
        self.after(100, self._start_prewarm)

    def _start_prewarm(self):
        """Silently builds 200 rows in the background."""
        dummy = FileObj("dummy", "Init...", "", 0, 0.0, FileType.OTHER, SyncStatus.MISSING)
        # We re-use the generator logic but with a 'prewarm' flag
        self.render_generator = self._create_row_generator([dummy]*200, None, None, set(), prewarm=True)
        self._process_render_queue()

    def _handle_select_missing(self):
        if self.on_select_missing:
            self.on_select_missing()

    def update_storage(self, path):
        if not path: return
        try:
            total, used, free = shutil.disk_usage(path)
            self.free_space = free
            self.total_space = total
            self.progress_bar.set(used / total)
            color = "#1f6aa5" 
            if (used/total) > 0.9: color = "#c42b1c"
            self.progress_bar.configure(progress_color=color)
        except:
            self.progress_bar.set(0)
            self.free_space = 0

    def set_alert_mode(self, is_alert: bool):
        if is_alert:
            self.progress_bar.configure(progress_color="#c42b1c") 
        else:
            if self.total_space > 0:
                percent = (self.total_space - self.free_space) / self.total_space
                color = "#1f6aa5" if percent <= 0.9 else "#c42b1c"
                self.progress_bar.configure(progress_color=color)

    def render_files(self, files: List[FileObj], on_row_click, on_row_toggle, selected_ids):
        """
        THE TIME-SLICED RENDERER
        This function sets up the job, but doesn't do the heavy lifting immediately.
        It creates a 'Generator' that yields control back to the UI every few items.
        """
        
        # 1. STOP previous job: If user switches folders rapidly, cancel the old render
        if self.render_task_id:
            self.after_cancel(self.render_task_id)
            self.render_task_id = None

        # 2. Reset Lookups
        self.row_map = {} 
        self.active_highlight_id = None

        # 3. Create the Plan: Make a generator object
        self.render_generator = self._create_row_generator(files, on_row_click, on_row_toggle, selected_ids)
        
        # 4. Start the Engine: Process the first batch
        self._process_render_queue()

    def _create_row_generator(self, files, on_click, on_toggle, selected_ids, prewarm=False):
        """
        This is a Python Generator. It runs code until it hits 'yield', then pauses.
        This allows us to process 20 items, pause to let the UI draw, then resume.
        """
        count_files = len(files)
        count_rows = len(self.rows)
        
        # --- PHASE 1: UPDATE EXISTING ROWS (Recycling) ---
        # Instead of doing all 170 at once (which freezes the UI), we yield every 20.
        recycle_limit = min(count_files, count_rows)
        
        for i in range(recycle_limit):
            row = self.rows[i]
            row.on_click = on_click
            row.on_toggle = on_toggle
            
            # Smart Update: widgets.py will only repaint if data changed
            row.update_data(files[i]) 
            
            if not prewarm:
                # If row was hidden, show it
                if not row.winfo_viewable(): row.pack(fill="x", pady=2, padx=2)
                
                # Update checkbox state
                should_check = (selected_ids and files[i].id in selected_ids)
                row.set_checked(should_check)
                self.row_map[files[i].id] = row
            
            # THE MAGIC: Pause every 20 items to keep UI responsive
            if i % 20 == 0:
                yield 

        # --- PHASE 2: HIDE EXTRA ROWS ---
        # If new folder has fewer files, hide the leftovers
        if count_rows > count_files:
            for i in range(count_files, count_rows):
                self.rows[i].pack_forget()
                if i % 20 == 0: yield # Pause here too

        # --- PHASE 3: CREATE NEW ROWS ---
        # If new folder has MORE files, create new widgets
        if count_files > count_rows:
            for i in range(count_rows, count_files):
                row = FileRow(self.scroll_frame, files[i], on_click=on_click, on_toggle=on_toggle)
                if not prewarm:
                    row.pack(fill="x", pady=2, padx=2)
                    should_check = (selected_ids and files[i].id in selected_ids)
                    row.set_checked(should_check)
                    self.row_map[files[i].id] = row
                
                self.rows.append(row)
                if i % 20 == 0: yield # Pause here too

    def _process_render_queue(self):
        """
        This runs periodically (every 5ms).
        It grabs the next batch of work from the generator.
        """
        if not self.render_generator: return

        try:
            # Execute the next ~20 items (until the generator yields)
            # We call next() once, which runs the generator until it hits 'yield'
            next(self.render_generator)
            
            # Schedule the next batch ASAP (5ms delay allows Tkinter to redraw)
            self.render_task_id = self.after(5, self._process_render_queue)
            
        except StopIteration:
            # Generator is empty, work is done!
            self.render_generator = None
            self.render_task_id = None

    def highlight_file(self, file_id):
        # Optimization: Only touch the 2 rows that need changing
        if self.active_highlight_id and self.active_highlight_id in self.row_map:
            if self.active_highlight_id != file_id:
                self.row_map[self.active_highlight_id].set_selected(False)
        
        if file_id and file_id in self.row_map:
            self.row_map[file_id].set_selected(True)
            
        self.active_highlight_id = file_id

class InspectorPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, width=250)
        self.lbl_header = ctk.CTkLabel(self, text="INSPECTOR", font=("Arial", 12, "bold"), text_color="gray")
        self.lbl_header.pack(pady=20)
        
        self.current_image = None
        self.active_file_id = None
        self.thumbnail_cache = {} 
        # ThreadPool: Runs heavy FFmpeg tasks off the main thread
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        self.preview_box = ctk.CTkFrame(self, height=150, fg_color="#1a1a1a")
        self.preview_box.pack(fill="x", padx=20, pady=10)
        self._create_preview_label()

        self.info_label = ctk.CTkLabel(self, text="", justify="left", anchor="w")
        self.info_label.pack(fill="x", padx=20, pady=20)

    def _create_preview_label(self):
        self.lbl_preview = ctk.CTkLabel(self.preview_box, text="No Selection")
        self.lbl_preview.place(relx=0.5, rely=0.5, anchor="center")

    def _rebuild_label(self):
        """Fixes 'Sticky' labels by destroying and recreating the widget"""
        try:
            self.lbl_preview.destroy()
        except:
            pass
        self._create_preview_label()

    def show_file(self, file_obj: FileObj):
        self.active_file_id = file_obj.id

        try:
            self.lbl_preview.configure(image=None, text=file_obj.file_type.name, text_color=["black", "white"])
            self.current_image = None
        except tkinter.TclError:
            self._rebuild_label()
            self.lbl_preview.configure(text=file_obj.file_type.name)

        # 2. THUMBNAIL LOGIC
        if file_obj.file_type == FileType.VIDEO:
            if file_obj.path in self.thumbnail_cache:
                self._apply_image(self.thumbnail_cache[file_obj.path])
            else:
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
        self.info_label.configure(text=details, text_color=["black", "white"])

    def _threaded_generation(self, path, requested_id):
        if self.active_file_id != requested_id: return
        try:
            pil_image = ThumbnailGenerator.generate_thumbnail(path)
            if pil_image:
                self.after(0, lambda: self._on_thumbnail_ready(path, requested_id, pil_image))
            else:
                self.after(0, lambda: self._on_thumbnail_failed(requested_id))
        except Exception as e:
            print(f"BG Thread Error: {e}")

    def _on_thumbnail_ready(self, path, requested_id, pil_image):
        ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(200, 110))
        self.thumbnail_cache[path] = ctk_img
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
            self.current_image = ctk_img
            self.lbl_preview.configure(image=self.current_image, text="")
        except tkinter.TclError:
            self._rebuild_label()
            self.current_image = ctk_img
            self.lbl_preview.configure(image=self.current_image, text="")

    def show_batch(self, count, total_size_bytes, warning_msg=None):
        self.active_file_id = None
        text_color = "#c42b1c" if warning_msg else ["black", "white"]
        header_text = "⚠️ INSUFFICIENT SPACE" if warning_msg else f"{count} Items"

        self._rebuild_label()
        self.lbl_preview.configure(image=None, text=header_text, text_color=text_color)
        self.current_image = None

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
        
        if warning_msg:
            details += f"\n{warning_msg}"
            
        self.info_label.configure(text=details, text_color=text_color)

    def clear_view(self):
        self.active_file_id = None
        self._rebuild_label()
        self.lbl_preview.configure(image=None, text="No Selection", text_color=["black", "white"])
        self.current_image = None
        self.info_label.configure(text="")