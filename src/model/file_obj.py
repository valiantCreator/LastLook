import os
from dataclasses import dataclass
from .types import FileType, SyncStatus

@dataclass
class FileObj:
    id: str                 # Unique ID (using path for MVP)
    filename: str
    path: str
    size: int               # Bytes
    date_modified: float    # Timestamp
    file_type: FileType
    status: SyncStatus = SyncStatus.MISSING

    @property
    def formatted_size(self) -> str:
        """Helper to show size in human-readable MB/GB"""
        size_in_bytes = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.2f} PB"

    @staticmethod
    def determine_type(filename: str) -> FileType:
        """Categorizes file based on extension for icon rendering."""
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.arw', '.cr2', '.dng', '.nef', '.raf']:
            return FileType.IMAGE
        elif ext in ['.mp4', '.mov', '.mxf', '.avi', '.braw', '.r3d']:
            return FileType.VIDEO
        elif ext in ['.wav', '.mp3', '.aac', '.m4a']:
            return FileType.AUDIO
        return FileType.OTHER