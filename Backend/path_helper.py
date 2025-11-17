import os
import sys

def get_data_path(relative_path: str) -> str:
    """Resolve a resource path that works for dev runs and PyInstaller builds."""
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
