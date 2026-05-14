import subprocess
import zipfile
from pathlib import Path

from backend.app.config import settings


def find_main_tex(project_dir: Path) -> Path | None:
    """Find the main .tex file by priority."""
    main = project_dir / "main.tex"
    if main.exists():
        return main

    doc = project_dir / "document.tex"
    if doc.exists():
        return doc

    root_tex_files = sorted(project_dir.glob("*.tex"))
    if root_tex_files:
        return root_tex_files[0]

    sub_tex_files = sorted(project_dir.rglob("*.tex"))
    if sub_tex_files:
        return sub_tex_files[0]

    return None


def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """Extract a zip with security checks."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        for name in names:
            if ".." in name or name.startswith("/"):
                raise ValueError(f"Unsafe path in zip: {name}")
        if len(names) > settings.max_file_count:
            raise ValueError(f"Too many files in zip: {len(names)} > {settings.max_file_count}")
        zf.extractall(dest_dir)


def compile_tex(project_dir: Path, main_tex: Path) -> tuple[bool, str]:
    """Run latexmk with XeLaTeX. Returns (success, full_log)."""
    result = subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-xelatex",
            "-interaction=nonstopmode",
            "-file-line-error",
            main_tex.name,
        ],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=settings.compile_timeout_soft,
    )

    full_log = result.stdout + result.stderr

    # Save full log to file
    log_path = project_dir / "compile.log"
    log_path.write_text(full_log)

    if result.returncode == 0:
        return True, full_log

    return False, full_log
