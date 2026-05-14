import { useState, useEffect } from 'react'
import Upload from './components/Upload'
import TaskList from './components/TaskList'
import PdfViewer from './components/PdfViewer'
import { getStats, type TaskStats } from './api'

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0)
  const [selectedTask, setSelectedTask] = useState<string | null>(null)
  const [stats, setStats] = useState<TaskStats | null>(null)

  const handleUploaded = (taskId: string) => {
    setSelectedTask(taskId)
    setRefreshKey((k) => k + 1)
  }

  useEffect(() => {
    const loadStats = async () => {
      try {
        const s = await getStats()
        setStats(s)
      } catch { /* ignore */ }
    }
    loadStats()
    const t = setInterval(loadStats, 5000)
    return () => clearInterval(t)
  }, [refreshKey])

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-icon">Tx</div>
          <div>
            <h1>AgentTeX</h1>
            <span className="subtitle">Agent-oriented TeX Compiler</span>
          </div>
        </div>
        <a href="/docs" target="_blank" rel="noreferrer" className="api-link">
          API Docs
        </a>
      </header>

      <div className="layout">
        <div className="sidebar">
          <Upload onUploaded={handleUploaded} />

          {stats && (
            <div className="stats-bar">
              <div className="stat-item">
                <div className="stat-value s-success">{stats.success}</div>
                <div className="stat-label">Success</div>
              </div>
              <div className="stat-item">
                <div className="stat-value s-failed">{stats.failed}</div>
                <div className="stat-label">Failed</div>
              </div>
              <div className="stat-item">
                <div className="stat-value s-active">{stats.running + stats.pending}</div>
                <div className="stat-label">Active</div>
              </div>
            </div>
          )}

          <TaskList
            refreshKey={refreshKey}
            onSelect={setSelectedTask}
            selectedId={selectedTask}
          />
        </div>
        <div className="main">
          <PdfViewer taskId={selectedTask} />
        </div>
      </div>
    </div>
  )
}
