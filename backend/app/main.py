import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Query, Form
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


# --- Dashboard ---

@app.get("/")
async def dashboard():
    html = DASHBOARD_HTML
    return HTMLResponse(content=html)


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgentTeX</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f5;color:#333;min-height:100vh}
.header{background:#4a90d9;color:#fff;padding:20px 32px;display:flex;align-items:center;justify-content:space-between}
.header h1{font-size:22px;font-weight:600}
.header .subtitle{font-size:13px;opacity:0.8}
.upload-btn{background:#fff;color:#4a90d9;border:none;padding:8px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;display:flex;align-items:center;gap:6px}
.upload-btn:hover{background:#e8f0fe}
.container{max-width:1200px;margin:24px auto;padding:0 24px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat-card{background:#fff;border-radius:8px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.08);cursor:pointer;transition:all 0.2s}
.stat-card:hover{box-shadow:0 4px 12px rgba(0,0,0,0.12)}
.stat-card.active{outline:2px solid #4a90d9}
.stat-card .label{font-size:12px;color:#888;text-transform:uppercase;letter-spacing:0.5px}
.stat-card .value{font-size:28px;font-weight:700;margin-top:4px}
.stat-card.success .value{color:#2ecc71}
.stat-card.failed .value{color:#e74c3c}
.stat-card.running .value{color:#f39c12}
.stat-card.total .value{color:#4a90d9}
.toolbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.section-title{font-size:16px;font-weight:600;color:#555}
.section-title .count{font-weight:400;color:#999;font-size:13px;margin-left:4px}
.task-list{display:flex;flex-direction:column;gap:8px}
.task-card{background:#fff;border-radius:10px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.08);border-left:4px solid #ddd;transition:all 0.2s}
.task-card:hover{box-shadow:0 4px 12px rgba(0,0,0,0.12)}
.task-card.success{border-left-color:#2ecc71}
.task-card.failed{border-left-color:#e74c3c}
.task-card.running{border-left-color:#f39c12}
.task-card.pending{border-left-color:#bdc3c7}
.task-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.task-name{font-size:15px;font-weight:600;color:#333;cursor:pointer;padding:2px 6px;border-radius:4px;border:1px solid transparent;transition:all 0.15s;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.task-name:hover{border-color:#d0d8e8;background:#f0f4fa}
.task-name.unnamed{color:#999;font-weight:400;font-style:italic}
.task-id-tag{font-family:'SF Mono','Fira Code',monospace;font-size:11px;color:#999;cursor:pointer;padding:1px 6px;border-radius:3px;background:#f5f5f5}
.task-id-tag:hover{color:#4a90d9;background:#e8f0fe}
.badge{padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.3px}
.badge.success{background:#e8f8ef;color:#27ae60}
.badge.failed{background:#fde8e8;color:#e74c3c}
.badge.running{background:#fef5e7;color:#f39c12}
.badge.pending{background:#f0f0f0;color:#888}
.task-meta{display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.task-time{font-size:12px;color:#999}
.task-actions{display:flex;gap:6px;flex-wrap:wrap}
.task-actions a,.task-actions button{font-size:12px;color:#4a90d9;text-decoration:none;padding:4px 10px;border:1px solid #d0d8e8;border-radius:4px;background:#fff;cursor:pointer;transition:all 0.15s;display:inline-flex;align-items:center;gap:4px}
.task-actions a:hover,.task-actions button:hover{background:#4a90d9;color:#fff;border-color:#4a90d9}
.task-actions button.danger{color:#e74c3c;border-color:#f0c0c0}
.task-actions button.danger:hover{background:#e74c3c;color:#fff;border-color:#e74c3c}
.error-detail{margin-top:8px;padding:8px;background:#f8f8f8;border-radius:4px;font-size:11px;color:#c0392b;max-height:80px;overflow-y:auto;font-family:monospace;white-space:pre-wrap;word-break:break-all}
.empty{text-align:center;padding:60px 20px;color:#999}
.empty p{font-size:14px;margin-top:8px}
.spin{display:inline-block;animation:spin 1s linear infinite}
@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
.modal-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:100;align-items:center;justify-content:center}
.modal-overlay.active{display:flex}
.modal{background:#fff;border-radius:12px;padding:32px;max-width:640px;width:90%;max-height:85vh;overflow-y:auto}
.modal h3{margin-bottom:16px;font-size:18px}
.modal .close-btn{margin-top:16px;background:none;border:1px solid #ddd;padding:6px 20px;border-radius:4px;cursor:pointer;color:#666}
.modal .close-btn:hover{background:#f5f5f5}
.modal .drop-area{border:2px dashed #ccc;border-radius:8px;padding:40px 20px;color:#888;cursor:pointer;transition:border-color 0.2s;text-align:center}
.modal .drop-area:hover,.modal .drop-area.dragging{border-color:#4a90d9;color:#4a90d9}
.modal input[type=file]{display:none}
.modal .progress{margin-top:16px;height:6px;background:#eee;border-radius:3px;overflow:hidden}
.modal .progress-bar{height:100%;background:#4a90d9;transition:width 0.3s;width:0}
.modal .error-msg{color:#e74c3c;font-size:13px;margin-top:8px}
.modal .name-input{width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px;margin-bottom:12px;transition:border-color 0.2s}
.modal .name-input:focus{outline:none;border-color:#4a90d9}
.log-content{background:#1e1e1e;color:#d4d4d4;padding:16px;border-radius:8px;font-family:'SF Mono','Fira Code',monospace;font-size:12px;line-height:1.6;max-height:60vh;overflow-y:auto;white-space:pre-wrap;word-break:break-all}
.log-content .log-err{color:#f48771}
.log-content .log-warn{color:#dcdcaa}
.file-list{list-style:none;max-height:50vh;overflow-y:auto}
.file-list li{padding:8px 12px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;font-size:13px}
.file-list li:last-child{border-bottom:none}
.file-list .fname{font-family:'SF Mono','Fira Code',monospace;color:#333}
.file-list .fsize{color:#999;font-size:12px}
.confirm-actions{display:flex;gap:12px;justify-content:flex-end}
.confirm-actions button{padding:8px 20px;border-radius:6px;border:1px solid #ddd;cursor:pointer;font-size:14px;transition:all 0.15s}
.confirm-actions .btn-cancel{background:#fff;color:#666}
.confirm-actions .btn-delete{background:#e74c3c;color:#fff;border-color:#e74c3c}
.toast{position:fixed;bottom:24px;right:24px;background:#333;color:#fff;padding:10px 20px;border-radius:8px;font-size:13px;opacity:0;transition:opacity 0.3s;z-index:200}
.toast.show{opacity:1}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>AgentTeX</h1>
    <div class="subtitle">Upload .zip, compile with XeLaTeX, preview PDF</div>
  </div>
  <button class="upload-btn" onclick="openModal('upload')">+ Upload Project</button>
</div>

<div class="container">
  <div class="stats" id="stats"></div>
  <div class="toolbar">
    <div class="section-title" id="sectionTitle">Recent Compilations <span class="count" id="taskCount"></span></div>
  </div>
  <div class="task-list" id="tasks"></div>
  <div class="empty" id="empty" style="display:none">
    <div style="font-size:48px;margin-bottom:8px">📄</div>
    <p>No compilations yet. Upload a project to get started.</p>
  </div>
</div>

<!-- Upload Modal -->
<div class="modal-overlay" id="uploadModal">
  <div class="modal">
    <h3>Upload Project</h3>
    <input type="text" class="name-input" id="projectName" placeholder="Project name (optional)" maxlength="100">
    <div class="drop-area" id="dropArea" onclick="document.getElementById('fileInput').click()">
      <div>Drop .zip here or click to browse</div>
    </div>
    <input type="file" id="fileInput" accept=".zip" onchange="handleFile(this.files[0])">
    <div class="progress" id="progressWrap" style="display:none"><div class="progress-bar" id="progressBar"></div></div>
    <div class="error-msg" id="uploadError"></div>
    <button class="close-btn" onclick="closeModal('upload')">Close</button>
  </div>
</div>

<!-- Log Modal -->
<div class="modal-overlay" id="logModal">
  <div class="modal" style="max-width:800px">
    <h3>Compilation Log</h3>
    <div class="log-content" id="logContent">Loading...</div>
    <button class="close-btn" onclick="closeModal('log')">Close</button>
  </div>
</div>

<!-- Files Modal -->
<div class="modal-overlay" id="filesModal">
  <div class="modal">
    <h3>Project Files</h3>
    <ul class="file-list" id="fileList"></ul>
    <button class="close-btn" onclick="closeModal('files')">Close</button>
  </div>
</div>

<!-- Delete Confirm Modal -->
<div class="modal-overlay" id="deleteModal">
  <div class="modal" style="max-width:420px">
    <h3>Delete Task</h3>
    <p style="font-size:14px;color:#555;margin-bottom:16px;line-height:1.6">Are you sure you want to delete this task and all its files? This cannot be undone.</p>
    <div class="confirm-actions">
      <button class="btn-cancel" onclick="closeModal('delete')">Cancel</button>
      <button class="btn-delete" id="confirmDeleteBtn">Delete</button>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
let allTasks = [], currentFilter = null, deleteTargetId = null;

function timeAgo(iso) {
  if (!iso) return '';
  const d = Date.now() - new Date(iso).getTime(), s = Math.floor(d/1000);
  if (s<60) return s+'s ago';
  const m = Math.floor(s/60);
  if (m<60) return m+'m ago';
  const h = Math.floor(m/60);
  if (h<24) return h+'h ago';
  return Math.floor(h/24)+'d ago';
}
function fmtTime(iso) { return iso ? new Date(iso).toLocaleString() : '-'; }
function toast(msg) { const el=document.getElementById('toast'); el.textContent=msg; el.classList.add('show'); setTimeout(()=>el.classList.remove('show'),2500); }
function esc(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function copyId(id) { navigator.clipboard.writeText(id).then(()=>toast('Task ID copied')); }
function openModal(n) { document.getElementById(n+'Modal').classList.add('active'); }
function closeModal(n) { document.getElementById(n+'Modal').classList.remove('active'); }

async function viewLog(id) {
  openModal('log');
  document.getElementById('logContent').textContent='Loading...';
  try {
    const r=await fetch('/api/tasks/'+id+'/log'), d=await r.json();
    document.getElementById('logContent').innerHTML=(d.log||'No log').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/^(!.*)$/gm,'<span class="log-err">$1</span>')
      .replace(/^(Error:.*)$/gm,'<span class="log-err">$1</span>');
  } catch(e) { document.getElementById('logContent').textContent='Failed'; }
}

async function viewFiles(id) {
  openModal('files');
  document.getElementById('fileList').innerHTML='<li>Loading...</li>';
  try {
    const r=await fetch('/api/tasks/'+id+'/files'), d=await r.json(), fs=d.files||[];
    if(!fs.length){document.getElementById('fileList').innerHTML='<li>No files</li>';return;}
    document.getElementById('fileList').innerHTML=fs.map(f=>{
      const sz=f.size<1024?f.size+' B':f.size<1048576?(f.size/1024).toFixed(1)+' KB':(f.size/1048576).toFixed(1)+' MB';
      return '<li><span class="fname">'+esc(f.path)+'</span><span class="fsize">'+sz+'</span></li>';
    }).join('');
  } catch(e) { document.getElementById('fileList').innerHTML='<li>Failed</li>'; }
}

function confirmDelete(id) { deleteTargetId=id; openModal('delete'); }
document.getElementById('confirmDeleteBtn').onclick=async function(){
  if(!deleteTargetId)return;
  try {
    const r=await fetch('/api/tasks/'+deleteTargetId,{method:'DELETE'});
    if(r.ok){toast('Deleted');closeModal('delete');refresh();}else toast('Failed');
  }catch(e){toast('Failed');}
  deleteTargetId=null;
};

async function renameTask(id) {
  const newName = prompt('Enter project name:', '');
  if (newName === null) return;
  try {
    await fetch('/api/tasks/'+id+'/rename?name='+encodeURIComponent(newName), {method:'PUT'});
    toast(newName ? 'Renamed to "'+newName+'"' : 'Name cleared');
    refresh();
  } catch(e) { toast('Rename failed'); }
}

function filterByStatus(s) { currentFilter=currentFilter===s?null:s; renderTasks(); }

function renderTasks() {
  let tasks=allTasks;
  if(currentFilter) tasks=tasks.filter(t=>t.status===currentFilter);
  document.querySelectorAll('.stat-card').forEach(el=>el.classList.toggle('active',el.dataset.filter===currentFilter));
  const grid=document.getElementById('tasks'), empty=document.getElementById('empty');
  document.getElementById('taskCount').textContent='('+tasks.length+')';
  if(!tasks.length){grid.innerHTML='';empty.style.display='block';return;}
  empty.style.display='none';
  grid.innerHTML=tasks.map(t=>{
    const cls=t.status,id=t.task_id||'',name=t.name||'';
    const displayName = name ? esc(name) : 'Untitled';
    const nameClass = name ? 'task-name' : 'task-name unnamed';
    let actions='',errorHtml='';
    if(cls==='success') {
      actions='<a href="/tasks/'+id+'/view" target="_blank">Preview</a><a href="/tasks/'+id+'/pdf" download>Download</a><button onclick="viewLog(\''+id+'\')">Log</button><button onclick="viewFiles(\''+id+'\')">Files</button><button onclick="renameTask(\''+id+'\')">Rename</button><button class="danger" onclick="confirmDelete(\''+id+'\')">Delete</button>';
    } else if(cls==='failed') {
      errorHtml='<div class="error-detail">'+esc(t.error).slice(0,500)+'</div>';
      actions='<button onclick="viewLog(\''+id+'\')">Full Log</button><button onclick="viewFiles(\''+id+'\')">Files</button><button onclick="renameTask(\''+id+'\')">Rename</button><button class="danger" onclick="confirmDelete(\''+id+'\')">Delete</button>';
    } else if(cls==='running') {
      actions='<button onclick="renameTask(\''+id+'\')">Rename</button>';
    } else {
      actions='<button onclick="renameTask(\''+id+'\')">Rename</button><button class="danger" onclick="confirmDelete(\''+id+'\')">Delete</button>';
    }
    return '<div class="task-card '+cls+'"><div class="task-top"><span class="'+nameClass+'" onclick="renameTask(\''+id+'\')" title="Click to rename">'+displayName+'</span><span class="badge '+cls+'">'+(cls==='running'?'<span class="spin">⟳</span> ':'')+cls+'</span></div><div class="task-meta"><span class="task-id-tag" onclick="copyId(\''+id+'\')" title="Click to copy">'+id.slice(0,8)+'...</span><span class="task-time">'+fmtTime(t.created_at)+(t.finished_at?' &middot; '+timeAgo(t.finished_at):'')+'</span></div>'+errorHtml+'<div class="task-actions">'+actions+'</div></div>';
  }).join('');
}

async function refresh() {
  try {
    const r=await fetch('/api/tasks?limit=200'), d=await r.json();
    allTasks=d.tasks||[];
    const st={total:allTasks.length,success:0,failed:0,running:0,pending:0};
    allTasks.forEach(t=>{if(st[t.status]!==undefined)st[t.status]++;});
    document.getElementById('stats').innerHTML=[
      ['total','Total',st.total,null],
      ['success','Success',st.success,'success'],
      ['running','Running',st.running+st.pending,'running'],
      ['failed','Failed',st.failed,'failed'],
    ].map(([c,l,v,f])=>'<div class="stat-card '+c+'" data-filter="'+(f||'')+'" onclick="filterByStatus(\''+(f||'')+'\')"><div class="label">'+l+'</div><div class="value">'+v+'</div></div>').join('');
    renderTasks();
    if(allTasks.some(t=>t.status==='running'||t.status==='pending'))setTimeout(refresh,2000);
  }catch(e){console.error(e);}
}

const dropArea=document.getElementById('dropArea');
dropArea.addEventListener('dragover',e=>{e.preventDefault();dropArea.classList.add('dragging');});
dropArea.addEventListener('dragleave',()=>dropArea.classList.remove('dragging'));
dropArea.addEventListener('drop',e=>{e.preventDefault();dropArea.classList.remove('dragging');if(e.dataTransfer.files[0])handleFile(e.dataTransfer.files[0]);});

async function handleFile(file) {
  if(!file||!file.name.endsWith('.zip')){document.getElementById('uploadError').textContent='Please select a .zip file';return;}
  const form=new FormData();
  form.append('file',file);
  form.append('name',document.getElementById('projectName').value);
  document.getElementById('progressWrap').style.display='block';
  document.getElementById('progressBar').style.width='30%';
  document.getElementById('uploadError').textContent='';
  try {
    const r=await fetch('/compile',{method:'POST',body:form});
    if(!r.ok){const e=await r.json().catch(()=>({detail:r.statusText}));throw new Error(e.detail||'Upload failed');}
    document.getElementById('progressBar').style.width='100%';
    setTimeout(()=>{closeModal('upload');document.getElementById('projectName').value='';refresh();},500);
  }catch(e){document.getElementById('uploadError').textContent=e.message;document.getElementById('progressBar').style.width='0';}
}

refresh();
</script>
</body>
</html>
"""


# --- Compile API ---

@app.post("/compile")
async def create_compile_task(file: UploadFile = File(...), name: str = Form("")):
    # Validate file size
    contents = await file.read()
    if len(contents) > settings.max_zip_size:
        raise HTTPException(status_code=400, detail=f"File too large, max {settings.max_zip_size // (1024*1024)}MB")

    task_id = str(uuid.uuid4())

    # Save uploaded zip
    upload_path = storage.upload_path(task_id)
    upload_path.write_bytes(contents)

    # Store initial metadata
    set_task_meta(
        task_id,
        status="pending",
        error="",
        created_at=datetime.now(timezone.utc).isoformat(),
        finished_at="",
    )
    # Ensure task_id and name are in the metadata hash (for dashboard display)
    r = _get_redis()
    r.hset("agenttex:task:" + task_id, mapping={"task_id": task_id, "name": name.strip()[:100] if name else ""})

    # Dispatch Celery task
    compile_task.delay(task_id)

    return {"task_id": task_id, "status": "pending"}


# --- Task status & PDF endpoints ---

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": meta.get("task_id", task_id),
        "status": meta.get("status", "unknown"),
        "name": meta.get("name") or None,
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

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
    )


@app.get("/tasks/{task_id}/view")
async def view_pdf(task_id: str, request: Request):
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")

    status = meta.get("status")
    if status == "success":
        # Desktop: native PDF viewer (supports text selection, download)
        # Mobile: PDF.js canvas rendering
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


@app.get("/api/tasks/{task_id}/log")
async def api_compile_log(task_id: str):
    """Get compilation log."""
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")
    log_path = storage.project_path(task_id) / "compile.log"
    if log_path.exists():
        return {"task_id": task_id, "log": log_path.read_text(errors="replace")}
    return {"task_id": task_id, "log": meta.get("error", "No log available")}


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
            files.append({"path": str(p.relative_to(project_dir)), "size": p.stat().st_size})
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


@app.delete("/api/tasks/{task_id}")
async def api_delete_task(task_id: str):
    """Delete a compilation task and its files."""
    import shutil
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")
    # Remove files
    for path in [storage.upload_path(task_id), storage.project_path(task_id), storage.output_path(task_id)]:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
    # Remove Redis metadata
    r = _get_redis()
    r.delete("agenttex:task:" + task_id)
    return {"deleted": task_id}


@app.put("/api/tasks/{task_id}/rename")
async def api_rename_task(task_id: str, name: str = ""):
    """Rename a task."""
    meta = get_task_meta(task_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Task not found")
    r = _get_redis()
    r.hset("agenttex:task:" + task_id, "name", name.strip()[:100])
    return {"task_id": task_id, "name": name.strip()}


@app.get("/api/stats")
async def api_stats():
    """Service statistics."""
    stats = get_task_stats()
    return stats


# --- Serve frontend static files (production) ---

static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
