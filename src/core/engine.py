import shutil
import threading
import os
from typing import List, Callable
from ..model.file_obj import FileObj, SyncStatus

class TransferEngine:
    def __init__(self):
        self._is_running = False

    def run_transfer(self, 
                     files: List[FileObj], 
                     dest_folder: str, 
                     on_progress: Callable[[str], None], 
                     on_complete: Callable[[], None]):
        """
        Starts the transfer process on a separate thread.
        """
        if self._is_running:
            return

        self._is_running = True
        
        # Spawn the worker thread
        thread = threading.Thread(
            target=self._transfer_worker,
            args=(files, dest_folder, on_progress, on_complete),
            daemon=True
        )
        thread.start()

    def _transfer_worker(self, 
                         files: List[FileObj], 
                         dest_folder: str, 
                         on_progress: Callable, 
                         on_complete: Callable):
        """
        The actual copy logic running in the background.
        """
        try:
            total = len(files)
            for index, file_obj in enumerate(files):
                # UI Update: "Copying A001.mp4..."
                on_progress(f"Copying {index + 1}/{total}: {file_obj.filename}")
                
                # Update status to TRANSFERRING
                file_obj.status = SyncStatus.TRANSFERRING
                
                source_path = file_obj.path
                dest_path = os.path.join(dest_folder, file_obj.filename)

                try:
                    # The Heavy Lifting: Copy with metadata (shutil.copy2)
                    shutil.copy2(source_path, dest_path)
                    
                    # Verify: Check if it actually arrived
                    if os.path.exists(dest_path) and os.path.getsize(dest_path) == file_obj.size:
                        file_obj.status = SyncStatus.SYNCED
                    else:
                        print(f"Verification failed for {file_obj.filename}")
                        
                except Exception as e:
                    print(f"Failed to copy {file_obj.filename}: {e}")

        except Exception as e:
            print(f"Critical Transfer Error: {e}")
        finally:
            self._is_running = False
            on_complete()