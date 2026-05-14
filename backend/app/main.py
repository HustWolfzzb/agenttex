import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.storage import storage
from backend.app.tasks import (
    compile_task, get_task_meta, set_task_meta, _get_redis,
    get_all_tasks, get_task_stats,
)

app = FastAPI(
    title="AgentTeX",
    description="Agent-oriented TeX Compiler",
    version="1.0.0",
)

storage.ensure_dirs()


# --- Existing APIs ---

@app.post("/compile")
async def create_compile_task(file: UploadFile = File(...)):
    contents = await file.read()
    if len(contents) > settings.max_zip_size:
        raise HTTPException(status_code=400, detail=f"File too large, max {settings.max_zip_size // (1024*1024)}MB")

    task_id = str(uuid.uuid4())
    upload_path = storage.upload_path(task_id)
    upload_path.write_bytes(contents)

    set_task_meta(
        task_id,
        task_id=task_id,
        status="pending",
        error="",
        created_at=datetime.now(timezone.utc).isoformat(),
        finished_at="",
    )

    compile_task.delay(task_id)
    return {"task_id": task_id, "status": "pending"}


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": meta.get("task_id", task_id),
        "status": meta.get("status", "unknown"),
        "error": meta.get("error") or None,
        "created_at": meta.get("created_at", ""),
        "finished_at": meta.get("finished_at") or None,
    }


@app.get("/tasks/{task_id}/pdf")
async def download_pdf(task_id: str):
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="PDF not found")

    status = meta.get("status")
    if status != "success":
        if status in ("pending", "running"):
            raise HTTPException(status_code=400, detail="Task not finished")
        raise HTTPException(status_code=404, detail="PDF not found")

    pdf_path = storage.output_path(task_id)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(path=str(pdf_path), media_type="application/pdf")


@app.get("/tasks/{task_id}/view")
async def view_pdf(task_id: str, request: Request):
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")

    status = meta.get("status")
    if status == "success":
        ua = request.headers.get("user-agent", "").lower()
        is_mobile = any(k in ua for k in ("mobile", "android", "iphone", "ipad"))

        if is_mobile:
            html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PDF Viewer</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<style>
body {{ margin:0; padding:0; background:#525659; }}
#pages {{ max-width:800px; margin:0 auto; padding:8px; }}
#pages canvas {{ width:100%; display:block; margin-bottom:8px; }}
#loading {{ color:#fff; text-align:center; padding:40px; font-family:sans-serif; }}
</style>
</head><body>
<div id="loading">Loading PDF...</div>
<div id="pages"></div>
<script>
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
pdfjsLib.getDocument('/tasks/{task_id}/pdf').promise.then(function(pdf) {{
  document.getElementById('loading').remove();
  var container = document.getElementById('pages');
  var pages = [];
  for (var i = 1; i <= pdf.numPages; i++) pages.push(i);
  pages.reduce(function(chain, num) {{
    return chain.then(function() {{
      return pdf.getPage(num).then(function(page) {{
        var vp = page.getViewport({{ scale: 2 }});
        var canvas = document.createElement('canvas');
        canvas.width = vp.width;
        canvas.height = vp.height;
        container.appendChild(canvas);
        return page.render({{ canvasContext: canvas.getContext('2d'), viewport: vp }}).promise;
      }});
    }});
  }}, Promise.resolve());
}});
</script>
</body></html>"""
        else:
            html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><title>PDF Viewer</title>
<style>body{{margin:0;padding:0;}} iframe{{width:100vw;height:100vh;border:none;}}</style>
</head><body><iframe src="/tasks/{task_id}/pdf"></iframe></body></html>"""
        return HTMLResponse(content=html)
    elif status in ("pending", "running"):
        html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Compiling...</title>
<meta http-equiv="refresh" content="3"></head>
<body><h2>Compiling, please wait...</h2><p>Auto-refreshing every 3 seconds.</p></body></html>"""
        return HTMLResponse(content=html)
    else:
        error = meta.get("error", "Unknown error")
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Compile Failed</title></head>
<body><h2>Compilation Failed</h2><pre>{error}</pre></body></html>"""
        return HTMLResponse(content=html, status_code=400)


@app.get("/latest/view")
async def view_latest(request: Request):
    r = _get_redis()
    task_id = r.get("agenttex:latest_task_id")
    if not task_id:
        raise HTTPException(status_code=404, detail="No compiled PDF yet")
    return await view_pdf(task_id, request)


@app.get("/latest/pdf")
async def download_latest():
    r = _get_redis()
    task_id = r.get("agenttex:latest_task_id")
    if not task_id:
        raise HTTPException(status_code=404, detail="No compiled PDF yet")
    return await download_pdf(task_id)


# --- Agent-friendly APIs ---

@app.get("/api/tasks")
async def api_list_tasks(
    status: str | None = Query(None, description="Filter by status: pending/running/success/failed"),
    limit: int = Query(50, ge=1, le=200),
):
    """List all compilation tasks. Agent-friendly JSON endpoint."""
    tasks = get_all_tasks(status=status, limit=limit)
    return {"tasks": tasks, "count": len(tasks)}


@app.get("/api/tasks/{task_id}/files")
async def api_list_files(task_id: str):
    """List files in the compiled project."""
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")

    project_dir = storage.project_path(task_id)
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project files not found")

    files = []
    for p in sorted(project_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(project_dir)
            files.append({
                "path": str(rel),
                "size": p.stat().st_size,
            })
    return {"task_id": task_id, "files": files}


@app.get("/api/tasks/{task_id}/files/{file_path:path}")
async def api_read_file(task_id: str, file_path: str):
    """Read a source file from the compiled project."""
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")

    full_path = storage.project_path(task_id) / file_path
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Security: ensure path doesn't escape project dir
    try:
        full_path.resolve().relative_to(storage.project_path(task_id).resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    # Only allow text-readable file types
    text_extensions = {".tex", ".bib", ".cls", ".sty", ".bst", ".md", ".txt", ".log", ".aux", ".bbl", ".blg", ".fls", ".fdb_latexmk"}
    if full_path.suffix.lower() not in text_extensions:
        raise HTTPException(status_code=400, detail=f"Cannot read {full_path.suffix} files")

    content = full_path.read_text(errors="replace")
    return {"task_id": task_id, "path": file_path, "content": content}


@app.get("/api/tasks/{task_id}/log")
async def api_compile_log(task_id: str):
    """Get full compilation log for Agent error diagnosis."""
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")

    log_path = storage.project_path(task_id) / "compile.log"
    if not log_path.exists():
        # Fallback to error field in metadata
        error = meta.get("error", "")
        return {"task_id": task_id, "log": error, "source": "metadata"}

    log_content = log_path.read_text(errors="replace")
    return {"task_id": task_id, "log": log_content, "source": "compile.log"}


@app.get("/api/stats")
async def api_stats():
    """Service statistics."""
    stats = get_task_stats()
    return stats


# --- Serve frontend static files (production) ---

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
