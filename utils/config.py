"""Load project configuration while preserving explicit shell overrides."""
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_project_env(path: Path | None = None) -> None:
    load_dotenv(path or PROJECT_ROOT / '.env', override=False)
