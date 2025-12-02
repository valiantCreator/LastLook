import os
from typing import List, Dict
from ..model.file_obj import FileObj, SyncStatus

class Scanner:
    @staticmethod
    def scan_directory(path: str) -> List[FileObj]:
        """
        Scans a directory and returns a list of FileObj instances.
        Uses os.scandir for better performance on large directories.
        """
        results = []
        if not path or not os.path.exists(path):
            return results

        try:
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_file() and not entry.name.startswith('.'):
                        stat = entry.stat()
                        file_obj = FileObj(
                            id=entry.path, # Using path as ID for MVP
                            filename=entry.name,
                            path=entry.path,
                            size=stat.st_size,
                            date_modified=stat.st_mtime,
                            file_type=FileObj.determine_type(entry.name),
                            status=SyncStatus.MISSING # Default to Missing
                        )
                        results.append(file_obj)
        except PermissionError:
            print(f"Permission denied accessing {path}")
        
        return results

    @staticmethod
    def compare_directories(source_files: List[FileObj], dest_path: str) -> List[FileObj]:
        """
        The 'Heartbeat' Logic. 
        Iterates through source files and checks if they exist in the destination 
        with matching file size.
        """
        # Create a map of destination files for O(1) lookup speed
        dest_map = {} # Key: Filename, Value: Size
        
        if os.path.exists(dest_path):
            try:
                with os.scandir(dest_path) as it:
                    for entry in it:
                        if entry.is_file():
                            dest_map[entry.name] = entry.stat().st_size
            except Exception as e:
                print(f"Error scanning destination: {e}")

        # Compare logic
        for src_file in source_files:
            dest_size = dest_map.get(src_file.filename)
            
            # MATCH CONDITION: Filename exists AND Size matches
            if dest_size is not None and dest_size == src_file.size:
                src_file.status = SyncStatus.SYNCED
            else:
                src_file.status = SyncStatus.MISSING
                
        return source_files