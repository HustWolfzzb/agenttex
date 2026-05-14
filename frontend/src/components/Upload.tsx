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
    setProgress(30)
    try {
      const result = await uploadZip(file)
      setProgress(100)
      setTimeout(() => {
        setUploading(false)
        setProgress(0)
        onUploaded(result.task_id)
      }, 500)
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

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(true)
  }

  const onDragLeave = () => setDragging(false)

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="card">
      <h2>Upload</h2>
      <div
        className={`dropzone ${dragging ? 'dragging' : ''}`}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => inputRef.current?.click()}
      >
        {uploading ? (
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
            <span>{progress}%</span>
          </div>
        ) : (
          <p>Drop .zip here or click to browse</p>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".zip"
          onChange={onChange}
          style={{ display: 'none' }}
        />
      </div>
      {error && <p className="error-text">{error}</p>}
    </div>
  )
}
