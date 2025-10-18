from typing import Iterable, Tuple
from pathlib import Path
import shutil
from objdump_io.fs import ensure_dir, file_size
from objdump_io.shell import run


def _project_cache_dir() -> Path:
    """Return the project-local cache directory for JARs.

    The cache lives under the repository root at `.cache/jars`.
    """
    # objdump_io/ is under the repo root; go up one level
    repo_root = Path(__file__).resolve().parents[1]
    cache_dir = repo_root / ".cache" / "jars"
    ensure_dir(str(cache_dir))
    return cache_dir


def download_files(dest_dir: str, items: Iterable[Tuple[str, str]]) -> None:
    """Ensure files exist in dest_dir using a project-local cache.

    - If the file already exists in `dest_dir`, skip.
    - Otherwise, copy from `.cache/jars` if present.
    - If not cached, download once into the cache, then copy to `dest_dir`.
    Each item is (filename, url).
    """
    ensure_dir(dest_dir)
    cache_dir = _project_cache_dir()

    for name, url in items:
        dest = Path(dest_dir) / name
        # If already present at destination, nothing to do
        if (size := file_size(str(dest))) and size > 0:
            continue

        cached = cache_dir / name
        # If cached, copy from cache
        if (csize := file_size(str(cached))) and csize > 0:
            shutil.copy2(str(cached), str(dest))
            continue

        # Not cached: download into cache, retry once if needed
        tmp_path = cache_dir / (name + ".tmp")
        res = run(["curl", "-L", "-o", str(tmp_path), url])
        if res.code != 0 or not file_size(str(tmp_path)):
            run(["curl", "-L", "-o", str(tmp_path), url])

        # Move tmp into cache if download succeeded
        if (dlsize := file_size(str(tmp_path))) and dlsize > 0:
            tmp_path.rename(cached)
            shutil.copy2(str(cached), str(dest))
        else:
            # Fallback: attempt direct download to destination as last resort
            run(["curl", "-L", "-o", str(dest), url])


