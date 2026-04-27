"""Trigger Excel formula recalculation via headless LibreOffice.

`openpyxl` writes cell values but does NOT execute formulas. To get computed
values, we re-save the file with LibreOffice (which auto-recalcs on save).

Tested working with LibreOffice 7+ on macOS via `soffice` CLI.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import os


def find_soffice() -> str:
    """Locate the LibreOffice CLI binary."""
    for candidate in [
        "/opt/homebrew/bin/soffice",
        "/usr/local/bin/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "soffice",
    ]:
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    raise RuntimeError(
        "LibreOffice (soffice) not found. Install via `brew install --cask libreoffice` "
        "or download from libreoffice.org."
    )


def recalc(xlsx_path: str | Path, output_dir: str | Path | None = None) -> Path:
    """Re-save xlsx_path through LibreOffice, forcing formula recalc.

    Returns the path to the recalculated file. Original is not modified.
    """
    src = Path(xlsx_path).resolve()
    out_dir = Path(output_dir).resolve() if output_dir else src.parent / "_recalc"
    out_dir.mkdir(parents=True, exist_ok=True)

    soffice = find_soffice()
    env = os.environ.copy()
    env.setdefault("HOME", str(Path.home()))

    result = subprocess.run(
        [
            soffice,
            "--headless",
            "--calc",
            "--convert-to", "xlsx",
            "--outdir", str(out_dir),
            str(src),
        ],
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"LibreOffice recalc failed: {result.stderr or result.stdout}"
        )

    out_path = out_dir / src.name
    if not out_path.exists():
        raise RuntimeError(f"Expected recalculated file at {out_path}, but not found.")

    return out_path
