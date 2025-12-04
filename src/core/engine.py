import shutil
import threading
import os
from typing import List, Callable, Optional
from ..model.file_obj import FileObj, SyncStatus
from .hashing import HashEngine

class TransferEngine:
    def __init__(self):
        self._is_running = False
        self._stop_flag = False

    def run_transfer(self, 
                     files: List[FileObj], 
                     dest_folder: str, 
                     on_progress: Callable[[str, Optional[FileObj]], None], 
                     on_complete: Callable[[], None]):
        
        if self._is_running: return

        self._is_running = True
        self._stop_flag = False
        
        thread = threading.Thread(
            target=self._transfer_worker,
            args=(files, dest_folder, on_progress, on_complete),
            daemon=True
        )
        thread.start()

    def stop(self):
        self._stop_flag = True

    def _transfer_worker(self, files: List[FileObj], dest_folder, on_progress, on_complete):
        try:
            total = len(files)
            for index, file_obj in enumerate(files):
                if self._stop_flag: break

                # 1. COPY PHASE
                # Notify UI: Message AND the File Object
                on_progress(f"[{index+1}/{total}] Copying: {file_obj.filename}...", file_obj)
                file_obj.status = SyncStatus.TRANSFERRING
                
                source_path = file_obj.path
                dest_path = os.path.join(dest_folder, file_obj.filename)

                try:
                    shutil.copy2(source_path, dest_path)
                    
                    # 2. VERIFICATION PHASE (The New Logic)
                    on_progress(f"[{index+1}/{total}] Verifying: {file_obj.filename}...", file_obj)
                    file_obj.status = SyncStatus.VERIFYING
                    
                    # A. Quick Size Check first (Fail fast)
                    if os.path.getsize(dest_path) != file_obj.size:
                        raise ValueError("File size mismatch")

                    # B. Deep Hash Check (The 'Paranoia' Check)
                    src_hash = HashEngine.calculate_md5(source_path)
                    dst_hash = HashEngine.calculate_md5(dest_path)

                    if src_hash and dst_hash and src_hash == dst_hash:
                        file_obj.status = SyncStatus.SYNCED
                    else:
                        raise ValueError(f"Checksum Mismatch! Src: {src_hash} != Dst: {dst_hash}")

                except Exception as e:
                    print(f"Transfer Error {file_obj.filename}: {e}")
                    file_obj.status = SyncStatus.ERROR
                    on_progress(f"Error on {file_obj.filename}", file_obj)

                # Final update for this file (Success or Error)
                on_progress(f"[{index+1}/{total}] Finished: {file_obj.filename}", file_obj)

        except Exception as e:
            print(f"Critical Worker Error: {e}")
        finally:
            self._is_running = False
            on_complete()