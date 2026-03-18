from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = REPO_ROOT / "reports"


def ensure_repo_root_on_path() -> None:
    repo_root_str = str(REPO_ROOT)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def require_path(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Expected path to exist: {path}")
    return path


def project_path(*parts: str) -> Path:
    return REPO_ROOT.joinpath(*parts)


ensure_repo_root_on_path()
