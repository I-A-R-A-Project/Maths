import os
from pathlib import Path


def maths_data_dir() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = root / "IARA" / "Maths"
    path.mkdir(parents=True, exist_ok=True)
    return path
