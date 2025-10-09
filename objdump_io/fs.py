import os
from pathlib import Path
from typing import Optional


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def file_size(path: str) -> Optional[int]:
    try:
        return os.path.getsize(path)
    except OSError:
        return None


