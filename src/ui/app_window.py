import customtkinter as ctk
import tkinter.filedialog as filedialog
import os
import concurrent.futures
from PIL import Image
from .panels import FileListPanel, InspectorPanel
from ..core.scanner import Scanner
from ..core.engine import TransferEngine
from ..model.file_obj import SyncStatus
from ..utils.assets import get_asset_path

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LastLook - Professional DIT Tool")
        self.geometry("1200x800")
        ctk.set_appearance_mode("Dark")
        
        self.source_path = None
        self.dest_path = None
        self.source_files = []
        self.selected_ids = set() 
        self.highlighted_id = None 
        self.transfer_engine = TransferEngine()
        self.night_shift_on = False
        
        # PERFORMANCE: Background Scanner Thread
        self.scan_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        try:
            self.icon_folder = ctk.CTkImage(Image.open(get_asset_path("folder.png")), size=(24, 24))
            self.icon_disk = ctk.CTkImage(Image.open(get_asset_path("disk.png")), size=(24, 24))
        except Exception as e:
            print(f"Warning: Icons failed to load: {e}")
            self.icon_folder = None
            self.icon_disk = None

        # --- LAYOUT ---
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=0) 
        self.grid_rowconfigure(1, weight=1)    

        # --- HEADER ---
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew")
        
        self.btn_source = ctk.CTkButton(
            self.header, 
            text=" Select Source", 
            image=self.icon_folder,
            command=self.select_source,
            font=("Arial", 13, "bold")
        )
        self.btn_source.pack(side="left", padx=20, pady=10)

        self.btn_dest = ctk.CTkButton(
            self.header, 
            text=" Select Destination", 
            image=self.icon_disk,
            command=self.select_dest, 
            fg_color="#2b4b6b",
            font=("Arial", 13, "bold")
        )
        self.btn_dest.pack(side="left", padx=10, pady=10)

        self.btn_night_shift = ctk.CTkSwitch(self.header, text="Eye Guard", command=self.toggle_night_shift)
        self.btn_night_shift.pack(side="right", padx=20, pady=10)

        # --- PANELS ---
        self.panel_source = FileListPanel(self, title="SOURCE MEDIA", on_select_missing=self.select_all_missing, on_background_click=self.deselect_all)
        self.panel_source.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.panel_dest = FileListPanel(self, title="DESTINATION BACKUP", is_dest=True, on_background_click=self.deselect_all)
        self.panel_dest.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        self.panel_inspector = InspectorPanel(self)
        self.panel_inspector.grid(row=1, column=2, sticky="ns", padx=5, pady=5)

        # --- FOOTER ---
        self.footer = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.footer.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.btn_transfer = ctk.CTkButton(self.footer, text="TRANSFER SELECTION", 
                                          width=300, 
                                          fg_color="#c42b1c", 
                                          state="disabled",
                                          command=self.start_transfer)
        self.btn_transfer.pack(side="right", padx=20, pady=15)
        
        self.lbl_status = ctk.CTkLabel(self.footer, text="Ready.")
        self.lbl_status.pack(side="left", padx=20)

    def select_source(self):
        path = filedialog.askdirectory()
        if path:
            self.source_path = path
            self.panel_source.lbl_title.configure(text=f"SOURCE: {os.path.basename(path)}")
            self.selected_ids.clear() 
            self.highlighted_id = None
            self.refresh_view()

    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_path = path
            self.panel_dest.lbl_title.configure(text=f"DEST: {os.path.basename(path)}")
            self.panel_dest.update_storage(path)
            self.refresh_view()

    def refresh_view(self):
        """Starts the Async Scan Process"""
        if not self.source_path: return

        # UI Feedback: Show user we are working
        self.lbl_status.configure(text="Scanning directories...")
        
        # Offload the heavy 'os.scandir' logic to a thread
        self.scan_executor.submit(self._threaded_scan, self.source_path, self.dest_path)

    def _threaded_scan(self, src, dst):
        """Runs in Background"""
        try:
            # 1. Heavy Disk I/O
            files = Scanner.scan_directory(src)
            
            # 2. Heavy Comparison Logic
            if dst:
                files = Scanner.compare_directories(files, dst)
            
            # 3. Return to Main Thread
            self.after(0, lambda: self._on_scan_complete(files))
        except Exception as e:
            print(f"Scan Error: {e}")
            self.after(0, lambda: self.lbl_status.configure(text="Scan Error"))

    def _on_scan_complete(self, files):
        """Runs on Main Thread - Updates UI with results"""
        self.source_files = files
        self.lbl_status.configure(text="Ready.")

        # Trigger the optimized renderer (which we fixed in the previous step)
        self.panel_source.render_files(
            self.source_files, 
            on_row_click=self.on_file_click, 
            on_row_toggle=self.on_file_toggle,
            selected_ids=self.selected_ids
        )

        if self.dest_path:
            self.panel_dest.render_files(
                self.source_files,
                on_row_click=self.on_file_click, 
                on_row_toggle=None, 
                selected_ids=set() 
            )

        self.update_ui_state()

    def on_file_click(self, file_obj):
        if self.highlighted_id == file_obj.id:
            self.deselect_all()
            return

        self.highlighted_id = file_obj.id
        self.panel_inspector.show_file(file_obj)
        self.panel_source.highlight_file(file_obj.id)
        if self.dest_path:
            self.panel_dest.highlight_file(file_obj.id)

    def deselect_all(self):
        self.highlighted_id = None
        self.panel_source.highlight_file(None)
        if self.dest_path: self.panel_dest.highlight_file(None)
        
        if len(self.selected_ids) == 0:
            self.panel_inspector.clear_view()
        else:
            self.update_ui_state()

    def on_file_toggle(self, file_obj, is_checked):
        if is_checked:
            self.selected_ids.add(file_obj.id)
        else:
            self.selected_ids.discard(file_obj.id)
        
        self.update_ui_state()

    def select_all_missing(self):
        count = 0
        for f in self.source_files:
            if f.status == SyncStatus.MISSING:
                self.selected_ids.add(f.id)
                count += 1
        
        # We don't need to re-scan, just re-render visuals
        # Using the cached file list is instant
        self.panel_source.render_files(
            self.source_files,
            on_row_click=self.on_file_click,
            on_row_toggle=self.on_file_toggle,
            selected_ids=self.selected_ids
        )
        self.update_ui_state()

    def update_ui_state(self):
        total_size = 0
        warning_msg = None
        is_blocked = False

        if len(self.selected_ids) > 0:
            total_size = sum(f.size for f in self.source_files if f.id in self.selected_ids)

        if self.dest_path:
            dest_free_space = self.panel_dest.free_space
            if total_size > dest_free_space:
                is_blocked = True
                self.panel_dest.set_alert_mode(True)
                
                def fmt(b): 
                    for u in ['B','KB','MB','GB']: 
                        if b<1024: return f"{b:.2f}{u}"
                        b/=1024
                    return f"{b:.2f}TB"
                
                deficit = total_size - dest_free_space
                warning_msg = (f"REQUIRED: {fmt(total_size)}\n"
                               f"AVAILABLE: {fmt(dest_free_space)}\n"
                               f"FREE UP: {fmt(deficit)}")
            else:
                self.panel_dest.set_alert_mode(False)

        if len(self.selected_ids) > 0:
            self.panel_inspector.show_batch(len(self.selected_ids), total_size, warning_msg)
        elif self.highlighted_id:
            file_obj = next((f for f in self.source_files if f.id == self.highlighted_id), None)
            if file_obj: self.panel_inspector.show_file(file_obj)
        else:
            self.panel_inspector.clear_view()

        if len(self.selected_ids) > 0 and self.dest_path:
            if is_blocked:
                self.btn_transfer.configure(state="disabled", text="INSUFFICIENT DISK SPACE", fg_color="#550000")
            else:
                self.btn_transfer.configure(state="normal", text=f"TRANSFER {len(self.selected_ids)} FILES", fg_color="#c42b1c")
        else:
            self.btn_transfer.configure(state="disabled", text="SELECT FILES TO TRANSFER")

    def start_transfer(self):
        files_to_transfer = [
            f for f in self.source_files 
            if f.id in self.selected_ids and f.status == SyncStatus.MISSING
        ]
        
        if not files_to_transfer:
            self.lbl_status.configure(text="Selected files are already synced!")
            return

        self.btn_transfer.configure(state="disabled", text="TRANSFERRING...")
        
        # Pass the new Update callback that expects a file object
        self.transfer_engine.run_transfer(
            files=files_to_transfer,
            dest_folder=self.dest_path,
            on_progress=self.update_progress, # Use method instead of lambda
            on_complete=self.on_transfer_complete
        )

    def on_transfer_complete(self):
        self.lbl_status.configure(text="Transfer Complete. Verifying...")
        self.selected_ids.clear() 
        self.refresh_view()
        self.panel_dest.update_storage(self.dest_path)

    # --- NEW UPDATE METHOD ---
    def update_progress(self, msg, file_obj=None):
        """Thread-safe UI update"""
        # Always run on main thread
        self.after(0, lambda: self._apply_update(msg, file_obj))

    def _apply_update(self, msg, file_obj):
        self.lbl_status.configure(text=msg)
        if file_obj:
            # Force the Source row to redraw (showing the Spinner/Check)
            self.panel_source.refresh_row(file_obj)

    def toggle_night_shift(self):
        self.night_shift_on = not self.night_shift_on
        if self.night_shift_on:
            ctk.set_appearance_mode("Dark")
            self.header.configure(fg_color="#2e1c05") 
            self.footer.configure(fg_color="#2e1c05")
        else:
            self.header.configure(fg_color=["gray90", "gray20"])
            self.footer.configure(fg_color=["gray90", "gray20"])