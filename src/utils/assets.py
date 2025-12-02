import sys
import os

def get_asset_path(filename: str) -> str:
    """
    Returns the absolute path to an asset.
    Works for dev (VS Code) and PyInstaller (One-File EXE).
    """
    if getattr(sys, 'frozen', False):
        # We are running in a bundle (PyInstaller)
        base_path = sys._MEIPASS
    else:
        # We are running in a normal Python environment
        base_path = os.path.abspath(".")

    return os.path.join(base_path, "assets", filename)