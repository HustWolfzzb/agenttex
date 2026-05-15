import re
import subprocess
import zipfile
from pathlib import Path

from backend.app.config import settings


def find_main_tex(project_dir: Path) -> Path | None:
    """Find the main .tex file by priority: main.tex > document.tex > root .tex > subdirectory .tex."""
    # Priority 1: main.tex in root
    main = project_dir / "main.tex"
    if main.exists():
        return main

    # Priority 2: document.tex in root
    doc = project_dir / "document.tex"
    if doc.exists():
        return doc

    # Priority 3: any .tex in root
    root_tex_files = sorted(project_dir.glob("*.tex"))
    if root_tex_files:
        return root_tex_files[0]

    # Priority 4: any .tex in subdirectories
    sub_tex_files = sorted(project_dir.rglob("*.tex"))
    if sub_tex_files:
        return sub_tex_files[0]

    return None


def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    """Extract a zip with security checks (path traversal + file count)."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()

        # Security: prevent path traversal
        for name in names:
            if ".." in name or name.startswith("/"):
                raise ValueError(f"Unsafe path in zip: {name}")

        # Security: prevent zip bomb
        if len(names) > settings.max_file_count:
            raise ValueError(
                f"Too many files in zip: {len(names)} > {settings.max_file_count}"
            )

        zf.extractall(dest_dir)


def extract_title(tex_path: Path) -> str | None:
    """Extract \\title{...} from a .tex file. Returns the title string or None."""
    try:
        content = tex_path.read_text(errors="replace")
        # Match \title{...} handling nested braces
        match = re.search(r'\\title\s*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}', content)
        if match:
            title = match.group(1).strip()
            # Remove common LaTeX commands from title
            title = re.sub(r'\\(?:textrm|textbf|textit|textsf|texttt)\{([^}]*)\}', r'\1', title)
            title = re.sub(r'\\\\', ' ', title)
            title = title.strip()
            return title if title else None
    except Exception:
        pass
    return None


def compile_tex(project_dir: Path, main_tex: Path) -> tuple[bool, str]:
    """Run latexmk with XeLaTeX. Returns (success, error_message)."""
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
        return True, ""

    # Take last 50 lines for error message
    last_lines = "\n".join(full_log.strip().splitlines()[-50:])
    return False, last_lines
