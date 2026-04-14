"""
trainer/io_utils.py — Safe I/O, folder helpers, timestamped paths
=================================================================
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional


def safe_read_json(path: Path) -> Optional[Dict[str, Any]]:
    """Read a JSON file safely. Returns None on any error."""
    try:
        if not Path(path).exists():
            return None
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [io_utils] ERROR reading {path}: {e}")
        return None


def safe_write_json(path: Path, data: Any, indent: int = 2) -> bool:
    """Write data to a JSON file safely. Returns True on success."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(data, indent=indent, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
    except Exception as e:
        print(f"  [io_utils] ERROR writing {path}: {e}")
        return False


def ensure_dirs(*paths) -> None:
    """Create directories (and parents) if they do not exist."""
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)


def timestamped_path(base_dir: Path, prefix: str, suffix: str = ".json") -> Path:
    """Return a Path of the form base_dir/prefix_YYYYMMDD_HHMMSS.suffix"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path(base_dir) / f"{prefix}_{ts}{suffix}"


def copy_json(src: Path, dst: Path) -> bool:
    """Copy src → dst. Creates dst parent dirs automatically."""
    try:
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"  [io_utils] ERROR copying {src} → {dst}: {e}")
        return False
