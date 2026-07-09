import { useState, useEffect, useRef } from 'react'
import { startRender, getRenderStatus } from '../api'
import type { SlideItem, RenderStatus } from '../types'

interface Props {
  slides: SlideItem[]
  title: string
}

export default function ExportPanel({ slides, title }: Props) {
  const [voice, setVoice] = useState('xiaoxiao')
  const [taskId, setTaskId] = useState('')
  const [status, setStatus] = useState<RenderStatus | null>(null)
  const [exporting, setExporting] = useState(false)
  const intervalRef = useRef<number>(0)

  const VOICES = [
    { id: 'xiaoxiao', name: '晓晓 (女) — 温暖自然' },
    { id: 'yunyang', name: '云扬 (男) — 专业可靠' },
    { id: 'yunxi', name: '云希 (男) — 阳光活泼' },
  ]

  useEffect(() => {
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [])

  const pollStatus = (id: string) => {
    intervalRef.current = window.setInterval(async () => {
      try {
        const s = await getRenderStatus(id)
        setStatus(s)
        if (s.status === 'done' || s.status === 'error') {
          clearInterval(intervalRef.current)
          setExporting(false)
        }
      } catch {
        clearInterval(intervalRef.current)
        setExporting(false)
      }
    }, 2000)
  }

  const handleExport = async () => {
    if (slides.length === 0) return
    setExporting(true)
    try {
      const result = await startRender(slides, title, voice)
      setTaskId(result.task_id)
      pollStatus(result.task_id)
    } catch (err) {
      console.error('导出失败:', err)
      alert('导出失败，请确认后端已启动')
      setExporting(false)
    }
  }

  return (
    <div className="export-panel">
      <h3>🎬 导出视频</h3>

      <div className="field">
        <label>配音音色</label>
        <select value={voice} onChange={e => setVoice(e.target.value)} className="select">
          {VOICES.map(v => (
            <option key={v.id} value={v.id}>{v.name}</option>
          ))}
        </select>
      </div>

      <div style={{ marginTop: 16 }}>
        <p style={{ fontSize: 12, color: '#8b949e', marginBottom: 8 }}>
          场景数: {slides.length} | 标题: {title || '未设置'}
        </p>
      </div>

      <button
        onClick={handleExport}
        disabled={exporting || slides.length === 0}
        className="btn btn-primary"
        style={{ width: '100%', marginTop: 12 }}
      >
        {exporting ? '⏳ 生成中...' : '🚀 生成视频'}
      </button>

      {status && (
        <div style={{ marginTop: 16, padding: 12, background: '#161b22', borderRadius: 8 }}>
          <StatusBar status={status} />
        </div>
      )}
    </div>
  )
}

function StatusBar({ status }: { status: RenderStatus }) {
  const labels: Record<string, string> = {
    queued: '排队中...',
    generating_audio: '🎤 生成配音...',
    rendering_frames: '🎨 渲染动画帧...',
    compositing: '🎬 合成视频...',
    done: '✅ 完成!',
    error: '❌ 出错',
  }

  return (
    <div>
      <p style={{ fontSize: 14, fontWeight: 600 }}>{labels[status.status] || status.status}</p>
      <div style={{ background: '#30363d', borderRadius: 4, height: 6, marginTop: 8 }}>
        <div style={{
          width: `${status.progress}%`, height: 6,
          background: 'linear-gradient(90deg, #00c8ff, #6366f1)',
          borderRadius: 4, transition: 'width 1s ease',
        }} />
      </div>
      {status.output_path && (
        <p style={{ fontSize: 12, color: '#8b949e', marginTop: 8 }}>
          文件: {status.output_path}
        </p>
      )}
      {status.error && (
        <p style={{ fontSize: 12, color: '#f85149', marginTop: 8 }}>
          {status.error}
        </p>
      )}
    </div>
  )
}
