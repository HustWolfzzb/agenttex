import { useState, useRef } from 'react'
import { uploadZip } from '../api'

interface Props {
  onUploaded: (taskId: string) => void
}

export default function Upload({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = async (file: File) => {
    if (!file.name.endsWith('.zip')) {
      setError('Only .zip files are accepted')
      return
    }
    setError(null)
    setUploading(true)
    setProgress(20)
    try {
      const result = await uploadZip(file)
      setProgress(100)
      setTimeout(() => {
        setUploading(false)
        setProgress(0)
        onUploaded(result.task_id)
      }, 600)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Upload failed')
      setUploading(false)
      setProgress(0)
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="card">
      <h2>Upload</h2>
      <div
        className={`dropzone ${dragging ? 'dragging' : ''}`}
        onDrop={onDrop}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onClick={() => inputRef.current?.click()}
      >
        {uploading ? (
          <>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <div className="progress-label">Uploading... {progress}%</div>
          </>
        ) : (
          <>
            <span className="dropzone-icon">⬆</span>
            <p>Drop .zip or click to browse</p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".zip"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); if (inputRef.current) inputRef.current.value = '' }}
          style={{ display: 'none' }}
        />
      </div>
      {error && <p style={{ color: 'var(--error)', fontSize: 12, marginTop: 8 }}>{error}</p>}
    </div>
  )
}
