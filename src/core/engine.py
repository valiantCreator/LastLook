import shutil
import threading
import os
import time
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

    def _format_speed(self, bytes_per_sec):
        return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"

    def _format_time(self, seconds):
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"

    def _transfer_worker(self, files: List[FileObj], dest_folder, on_progress, on_complete):
        try:
            # --- IMPROVEMENT: Calculate Total Batch Size for Global Progress ---
            total_files = len(files)
            total_bytes = sum(f.size for f in files)
            bytes_transferred_global = 0
            start_time_global = time.time()

            for index, file_obj in enumerate(files):
                if self._stop_flag: break

                # 1. COPY PHASE (Manual Loop for Speed Tracking)
                file_obj.status = SyncStatus.TRANSFERRING
                
                source_path = file_obj.path
                dest_path = os.path.join(dest_folder, file_obj.filename)

                try:
                    # IMPROVEMENT: Manual Copy Loop to measure speed
                    with open(source_path, 'rb') as fsrc:
                        with open(dest_path, 'wb') as fdst:
                            while True:
                                if self._stop_flag: break
                                
                                # Read 1MB Chunk
                                buf = fsrc.read(1024 * 1024) 
                                if not buf: break
                                
                                fdst.write(buf)
                                
                                # Math: Speed & ETA
                                chunk_size = len(buf)
                                bytes_transferred_global += chunk_size
                                
                                elapsed = time.time() - start_time_global
                                if elapsed > 0:
                                    speed = bytes_transferred_global / elapsed
                                    remaining_bytes = total_bytes - bytes_transferred_global
                                    eta = remaining_bytes / speed if speed > 0 else 0
                                    
                                    # Update UI string with Pulse Data
                                    msg = (f"[{index+1}/{total_files}] Copying {file_obj.filename} "
                                           f"({self._format_speed(speed)}) - ETA: {self._format_time(eta)}")
                                    
                                    # Limit updates to every 100ms to avoid flooding UI? 
                                    # For MVP we send every chunk (might be fast, but CTk handles it)
                                    on_progress(msg, file_obj)

                    if self._stop_flag: break

                    # CRITICAL: Restore metadata (timestamps) since we did a manual copy
                    shutil.copystat(source_path, dest_path)
                    
                    # 2. VERIFICATION PHASE
                    on_progress(f"[{index+1}/{total_files}] Verifying: {file_obj.filename}...", file_obj)
                    file_obj.status = SyncStatus.VERIFYING
                    
                    # A. Quick Size Check
                    if os.path.getsize(dest_path) != file_obj.size:
                        raise ValueError("File size mismatch")

                    # B. Deep Hash Check
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

                # Final update for this file
                on_progress(f"[{index+1}/{total_files}] Finished: {file_obj.filename}", file_obj)

        except Exception as e:
            print(f"Critical Worker Error: {e}")
        finally:
            self._is_running = False
            on_complete()