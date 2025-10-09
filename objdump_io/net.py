from typing import Iterable, Tuple
from pathlib import Path
from .fs import ensure_dir, file_size
from .shell import run


def download_files(dest_dir: str, items: Iterable[Tuple[str, str]]) -> None:
    """Download files with curl -L. Each item is (filename, url)."""
    ensure_dir(dest_dir)
    for name, url in items:
        dest = Path(dest_dir) / name
        size = file_size(str(dest))
        if size and size > 0:
            continue
        res = run(["curl", "-L", "-o", str(dest), url])
        # simple retry if empty or non-zero exit
        if res.code != 0 or not file_size(str(dest)):
            run(["curl", "-L", "-o", str(dest), url])


