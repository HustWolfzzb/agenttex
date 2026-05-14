import { useState, useEffect, useCallback } from 'react'
import { listTasks, type TaskInfo } from '../api'

interface Props {
  refreshKey: number
  onSelect: (taskId: string) => void
  selectedId: string | null
}

function timeAgo(dateStr: string): string {
  if (!dateStr) return ''
  const diff = Date.now() - new Date(dateStr).getTime()
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ago`
}

const STATUS_ICON: Record<string, string> = {
  pending: '○',
  running: '⟳',
  success: '✓',
  failed: '✗',
}

const STATUS_CLASS: Record<string, string> = {
  pending: 'status-pending',
  running: 'status-running',
  success: 'status-success',
  failed: 'status-failed',
}

export default function TaskList({ refreshKey, onSelect, selectedId }: Props) {
  const [tasks, setTasks] = useState<TaskInfo[]>([])
  const [hasRunning, setHasRunning] = useState(false)

  const fetchTasks = useCallback(async () => {
    try {
      const res = await listTasks(undefined, 100)
      setTasks(res.tasks)
      setHasRunning(res.tasks.some((t) => t.status === 'running' || t.status === 'pending'))
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    fetchTasks()
  }, [refreshKey, fetchTasks])

  // Auto-poll running tasks every 2s
  useEffect(() => {
    if (!hasRunning) return
    const timer = setInterval(fetchTasks, 2000)
    return () => clearInterval(timer)
  }, [hasRunning, fetchTasks])

  if (tasks.length === 0) {
    return (
      <div className="card">
        <h2>Tasks</h2>
        <p className="muted">No compilation tasks yet</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2>Tasks</h2>
      <div className="task-list">
        {tasks.map((task) => (
          <div
            key={task.task_id}
            className={`task-row ${STATUS_CLASS[task.status]} ${selectedId === task.task_id ? 'selected' : ''}`}
            onClick={() => onSelect(task.task_id)}
          >
            <span className="task-icon">{STATUS_ICON[task.status]}</span>
            <span className="task-id">{task.task_id.slice(0, 8)}</span>
            <span className={`task-status ${STATUS_CLASS[task.status]}`}>{task.status}</span>
            <span className="task-time">{timeAgo(task.created_at)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
