from enum import Enum, auto

class FileType(Enum):
    IMAGE = auto()
    VIDEO = auto()
    AUDIO = auto()
    OTHER = auto()

class SyncStatus(Enum):
    MISSING = "missing"           # Exists in Source, NOT in Destination (Red)
    SYNCED = "synced"             # Exists in both (Name + Size match) (Green)
    TRANSFERRING = "transferring" # Currently copying (Blue Spinner)
    VERIFYING = "verifying"       # Orange / Microscope (New!)
    ERROR = "error"               # Red Warning (New!)
    PENDING = "pending"           # Queued for transfer

class AppTheme(Enum):
    LIGHT = "Light"
    DARK = "Dark"