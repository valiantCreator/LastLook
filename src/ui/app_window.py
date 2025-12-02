import customtkinter as ctk
import tkinter.filedialog as filedialog
import os
from .panels import FileListPanel, InspectorPanel
from ..core.scanner import Scanner
from ..core.engine import TransferEngine
from ..model.file_obj import SyncStatus

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("LastLook - Professional DIT Tool")
        self.geometry("1200x800")
        ctk.set_appearance_mode("Dark")
        
        # State
        self.source_path = None
        self.dest_path = None
        self.source_files = []
        self.selected_ids = set() 
        self.transfer_engine = TransferEngine()
        self.night_shift_on = False

        # --- LAYOUT ---
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=0) 
        self.grid_rowconfigure(1, weight=1)    

        # --- HEADER ---
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew")
        
        self.btn_source = ctk.CTkButton(self.header, text="📂 Select Source", command=self.select_source)
        self.btn_source.pack(side="left", padx=20, pady=10)

        self.btn_dest = ctk.CTkButton(self.header, text="💾 Select Destination", command=self.select_dest, fg_color="#2b4b6b")
        self.btn_dest.pack(side="left", padx=10, pady=10)

        self.btn_night_shift = ctk.CTkSwitch(self.header, text="Eye Guard", command=self.toggle_night_shift)
        self.btn_night_shift.pack(side="right", padx=20, pady=10)

        # --- PANELS ---
        self.panel_source = FileListPanel(self, title="SOURCE MEDIA", on_select_missing=self.select_all_missing)
        self.panel_source.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.panel_dest = FileListPanel(self, title="DESTINATION BACKUP", is_dest=True)
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
            self.refresh_view()

    def select_dest(self):
        path = filedialog.askdirectory()
        if path:
            self.dest_path = path
            self.panel_dest.lbl_title.configure(text=f"DEST: {os.path.basename(path)}")
            self.panel_dest.update_storage(path)
            self.refresh_view()

    def refresh_view(self):
        if not self.source_path: return

        # 1. Scan & Compare
        self.source_files = Scanner.scan_directory(self.source_path)
        if self.dest_path:
            self.source_files = Scanner.compare_directories(self.source_files, self.dest_path)
            
        # 2. Render Source (With Checkbox Logic)
        self.panel_source.render_files(
            self.source_files, 
            on_row_click=self.on_file_click, 
            on_row_toggle=self.on_file_toggle,
            selected_ids=self.selected_ids
        )

        # 3. Render Destination (This was the missing part!)
        # We render the same file list to visualize the "Ghost" (Red) vs "Synced" (Green) status
        if self.dest_path:
            self.panel_dest.render_files(
                self.source_files,
                on_row_click=self.on_file_click,
                on_row_toggle=None, # Dest doesn't need checkboxes yet
                selected_ids=set()  # No visuals for selection on Dest yet
            )

        # 4. Update Footer State
        if len(self.selected_ids) > 0 and self.dest_path:
            self.btn_transfer.configure(state="normal", text=f"TRANSFER {len(self.selected_ids)} FILES")
        else:
            self.btn_transfer.configure(state="disabled", text="SELECT FILES TO TRANSFER")
            
        # 5. Update Inspector
        self.update_inspector()

    def on_file_click(self, file_obj):
        self.panel_inspector.show_file(file_obj)

    def on_file_toggle(self, file_obj, is_checked):
        if is_checked:
            self.selected_ids.add(file_obj.id)
        else:
            self.selected_ids.discard(file_obj.id)
        
        # Update UI text immediately
        if len(self.selected_ids) > 0 and self.dest_path:
            self.btn_transfer.configure(state="normal", text=f"TRANSFER {len(self.selected_ids)} FILES")
        else:
            self.btn_transfer.configure(state="disabled", text="SELECT FILES TO TRANSFER")
            
        self.update_inspector()

    def select_all_missing(self):
        """Utility: Check all boxes where status is MISSING"""
        count = 0
        for f in self.source_files:
            if f.status == SyncStatus.MISSING:
                self.selected_ids.add(f.id)
                count += 1
        self.refresh_view() 

    def update_inspector(self):
        if len(self.selected_ids) == 0:
            return 
        elif len(self.selected_ids) == 1:
            file_id = next(iter(self.selected_ids))
            file_obj = next((f for f in self.source_files if f.id == file_id), None)
            if file_obj: self.panel_inspector.show_file(file_obj)
        else:
            total_size = sum(f.size for f in self.source_files if f.id in self.selected_ids)
            self.panel_inspector.show_batch(len(self.selected_ids), total_size)

    def start_transfer(self):
        files_to_transfer = [
            f for f in self.source_files 
            if f.id in self.selected_ids and f.status == SyncStatus.MISSING
        ]
        
        if not files_to_transfer:
            self.lbl_status.configure(text="Selected files are already synced!")
            return

        self.btn_transfer.configure(state="disabled", text="TRANSFERRING...")
        
        self.transfer_engine.run_transfer(
            files=files_to_transfer,
            dest_folder=self.dest_path,
            on_progress=lambda msg: self.lbl_status.configure(text=msg),
            on_complete=self.on_transfer_complete
        )

    def on_transfer_complete(self):
        self.lbl_status.configure(text="Transfer Complete. Verifying...")
        self.selected_ids.clear() 
        self.refresh_view()
        self.panel_dest.update_storage(self.dest_path)

    def toggle_night_shift(self):
        self.night_shift_on = not self.night_shift_on
        if self.night_shift_on:
            ctk.set_appearance_mode("Dark")
            self.header.configure(fg_color="#2e1c05") 
            self.footer.configure(fg_color="#2e1c05")
        else:
            self.header.configure(fg_color=["gray90", "gray20"])
            self.footer.configure(fg_color=["gray90", "gray20"])