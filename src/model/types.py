from enum import Enum, auto

class FileType(Enum):
    IMAGE = auto()
    VIDEO = auto()
    AUDIO = auto()
    OTHER = auto()

class SyncStatus(Enum):
    MISSING = "missing"           # Exists in Source, NOT in Dest
    SYNCED = "synced"             # Exists in both (Name + Size match)
    TRANSFERRING = "transferring" # Currently copying
    PENDING = "pending"           # Queued for transfer

class AppTheme(Enum):
    LIGHT = "Light"
    DARK = "Dark"