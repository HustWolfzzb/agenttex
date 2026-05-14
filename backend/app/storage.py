from pathlib import Path
from backend.app.config import settings


class Storage:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or settings.data_dir

    def ensure_dirs(self) -> None:
        for d in ("uploads", "projects", "output"):
            (self.base_dir / d).mkdir(parents=True, exist_ok=True)

    def upload_path(self, task_id: str) -> Path:
        return self.base_dir / "uploads" / f"{task_id}.zip"

    def project_path(self, task_id: str) -> Path:
        return self.base_dir / "projects" / task_id

    def output_path(self, task_id: str) -> Path:
        return self.base_dir / "output" / f"{task_id}.pdf"

    def compile_log_path(self, task_id: str) -> Path:
        return self.base_dir / "projects" / task_id / "compile.log"


storage = Storage()
