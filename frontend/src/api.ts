export interface TaskInfo {
  task_id: string
  status: 'pending' | 'running' | 'success' | 'failed'
  error: string | null
  created_at: string
  finished_at: string | null
}

export interface TaskListResponse {
  tasks: TaskInfo[]
  count: number
}

export interface TaskStats {
  total: number
  success: number
  failed: number
  pending: number
  running: number
}

const BASE = ''

export async function uploadZip(file: File): Promise<{ task_id: string; status: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/compile`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

export async function getTask(taskId: string): Promise<TaskInfo> {
  const res = await fetch(`${BASE}/tasks/${taskId}`)
  if (!res.ok) throw new Error('Task not found')
  return res.json()
}

export async function listTasks(status?: string, limit = 50): Promise<TaskListResponse> {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  params.set('limit', String(limit))
  const res = await fetch(`${BASE}/api/tasks?${params}`)
  if (!res.ok) throw new Error('Failed to fetch tasks')
  return res.json()
}

export async function getStats(): Promise<TaskStats> {
  const res = await fetch(`${BASE}/api/stats`)
  if (!res.ok) throw new Error('Failed to fetch stats')
  return res.json()
}
