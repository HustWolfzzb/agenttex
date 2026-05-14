import { useState } from 'react'
import Upload from './components/Upload'
import TaskList from './components/TaskList'
import PdfViewer from './components/PdfViewer'

export default function App() {
  const [refreshKey, setRefreshKey] = useState(0)
  const [selectedTask, setSelectedTask] = useState<string | null>(null)

  const handleUploaded = (taskId: string) => {
    setSelectedTask(taskId)
    setRefreshKey((k) => k + 1)
  }

  return (
    <div className="app">
      <header className="header">
        <h1>AgentTeX</h1>
        <span className="subtitle">Agent-oriented TeX Compiler</span>
        <a href="/docs" target="_blank" rel="noreferrer" className="api-link">
          API Docs
        </a>
      </header>

      <div className="layout">
        <div className="sidebar">
          <Upload onUploaded={handleUploaded} />
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
