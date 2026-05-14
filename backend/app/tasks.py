import shutil
import logging
from datetime import datetime, timezone

from celery import Celery

from backend.app.config import settings
from backend.app.storage import storage
from backend.app.tex_utils import extract_zip, find_main_tex, compile_tex

logger = logging.getLogger(__name__)

celery_app = Celery(
    "agenttex_compiler",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)

_task_meta_key = "agenttex:task:{task_id}"


def _get_redis():
    from redis import Redis
    return Redis.from_url(settings.redis_url, decode_responses=True)


def set_task_meta(task_id: str, **kwargs) -> None:
    import json
    r = _get_redis()
    key = _task_meta_key.format(task_id=task_id)
    data = r.hgetall(key)
    data.update(kwargs)
    r.hset(key, mapping=data)


def get_task_meta(task_id: str) -> dict:
    r = _get_redis()
    key = _task_meta_key.format(task_id=task_id)
    data = r.hgetall(key)
    return data if data else {}


def get_all_tasks(status: str | None = None, limit: int = 50) -> list[dict]:
    """Get all tasks from Redis, optionally filtered by status."""
    r = _get_redis()
    keys = r.keys(_task_meta_key.format(task_id="*"))
    tasks = []
    for key in keys:
        data = r.hgetall(key)
        if data:
            if status and data.get("status") != status:
                continue
            tasks.append(data)
    # Sort by created_at descending
    tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    return tasks[:limit]


def get_task_stats() -> dict:
    """Get compilation statistics."""
    r = _get_redis()
    keys = r.keys(_task_meta_key.format(task_id="*"))
    total = len(keys)
    success = 0
    failed = 0
    pending = 0
    running = 0
    for key in keys:
        data = r.hgetall(key)
        s = data.get("status", "")
        if s == "success":
            success += 1
        elif s == "failed":
            failed += 1
        elif s == "running":
            running += 1
        else:
            pending += 1
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "pending": pending,
        "running": running,
    }


@celery_app.task(bind=True, soft_time_limit=settings.compile_timeout_soft, time_limit=settings.compile_timeout_hard)
def compile_task(self, task_id: str) -> dict:
    set_task_meta(task_id, status="running")

    try:
        storage.ensure_dirs()

        upload = storage.upload_path(task_id)
        project_dir = storage.project_path(task_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        extract_zip(upload, project_dir)

        main_tex = find_main_tex(project_dir)
        if main_tex is None:
            set_task_meta(
                task_id,
                status="failed",
                error="No .tex file found in the project",
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
            return {"status": "failed", "error": "No .tex file found"}

        success, error = compile_tex(project_dir, main_tex)

        if success:
            pdf_name = main_tex.stem + ".pdf"
            pdf_src = project_dir / pdf_name
            pdf_dest = storage.output_path(task_id)

            if pdf_src.exists():
                shutil.copy2(pdf_src, pdf_dest)
                set_task_meta(
                    task_id,
                    status="success",
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
                r = _get_redis()
                r.set("agenttex:latest_task_id", task_id)
                return {"status": "success"}
            else:
                set_task_meta(
                    task_id,
                    status="failed",
                    error="Compilation succeeded but PDF not found",
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
                return {"status": "failed", "error": "PDF not found after compilation"}
        else:
            set_task_meta(
                task_id,
                status="failed",
                error=error[-2000:] if len(error) > 2000 else error,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
            return {"status": "failed", "error": error[-2000:]}

    except Exception as e:
        logger.exception("Compilation task failed")
        set_task_meta(
            task_id,
            status="failed",
            error=str(e),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        return {"status": "failed", "error": str(e)}
