import { useEffect, useState } from 'react'
import { getTask, type TaskInfo } from '../api'

interface Props {
  taskId: string | null
}

export default function PdfViewer({ taskId }: Props) {
  const [task, setTask] = useState<TaskInfo | null>(null)

  useEffect(() => {
    if (!taskId) { setTask(null); return }
    const poll = async () => {
      try { setTask(await getTask(taskId)) } catch { /* ignore */ }
    }
    poll()
    const timer = setInterval(poll, 2000)
    return () => clearInterval(timer)
  }, [taskId])

  if (!taskId) {
    return (
      <div className="card viewer-empty">
        <span className="viewer-empty-icon">◇</span>
        <p className="muted">Select a completed task to preview</p>
      </div>
    )
  }

  if (!task) return null

  if (task.status === 'pending' || task.status === 'running') {
    return (
      <div className="card">
        <h2>PDF Preview</h2>
        <div className="compiling">
          <div className="compile-ring" />
          <p>Compiling...</p>
        </div>
      </div>
    )
  }

  if (task.status === 'failed') {
    return (
      <div className="card">
        <h2>PDF Preview</h2>
        <div className="error-box">
          <p className="error-text">Compilation Failed</p>
          <pre className="error-log">{task.error}</pre>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="viewer-header">
        <h2>PDF Preview</h2>
        <a href={`/tasks/${taskId}/pdf`} download className="download-btn">
          Download PDF
        </a>
      </div>
      <iframe src={`/tasks/${taskId}/pdf`} className="pdf-frame" title="PDF Preview" />
    </div>
  )
}
