import sys
import os

def get_asset_path(filename: str) -> str:
    """Returns absolute path to an asset (image/icon)."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "assets", filename)

def get_ffmpeg_path() -> str:
    """Returns path to the ffmpeg executable."""
    filename = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
    return get_asset_path(filename)