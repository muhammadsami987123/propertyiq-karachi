import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_validate_data_script_passes():
    """The full Karachi dataset must pass schema + referential-integrity checks."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate_data.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
