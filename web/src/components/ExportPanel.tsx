import { useState, useEffect, useRef } from 'react'
import { startRender, getRenderStatus } from '../api'
import type { SlideItem, RenderStatus } from '../types'

interface Props {
  slides: SlideItem[]
  title: string
}

const THEMES = [
  { id: 'deep', name: '深空蓝', color: '#0a0a2e' },
  { id: 'cosmic', name: '宇宙紫', color: '#1a0a2e' },
  { id: 'ocean', name: '海洋蓝', color: '#0a3d5c' },
  { id: 'sunset', name: '日落橙', color: '#3e1a2e' },
  { id: 'forest', name: '森林绿', color: '#1a3e1a' },
  { id: 'aurora', name: '极光', color: '#0d1e2e' },
  { id: 'slate', name: '暗石板', color: '#1a1a2e' },
  { id: 'violet', name: '紫罗兰', color: '#1e0a2e' },
]

const VOICES = [
  { id: 'xiaoxiao', name: '晓晓 (女) — 温暖自然' },
  { id: 'yunyang', name: '云扬 (男) — 专业可靠' },
  { id: 'yunxi', name: '云希 (男) — 阳光活泼' },
  { id: 'yunjian', name: '云健 (男) — 激情澎湃' },
  { id: 'xiaoyi', name: '晓伊 (女) — 活泼可爱' },
  { id: 'yunxia', name: '云夏 — 可爱童趣' },
]

export default function ExportPanel({ slides, title }: Props) {
  const [voice, setVoice] = useState('xiaoxiao')
  const [subtitles, setSubtitles] = useState(true)
  const [voiceover, setVoiceover] = useState(true)
  const [bgTheme, setBgTheme] = useState('deep')
  const [taskId, setTaskId] = useState('')
  const [status, setStatus] = useState<RenderStatus | null>(null)
  const [exporting, setExporting] = useState(false)
  const intervalRef = useRef<number>(0)

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
      const result = await startRender(slides, title, voice, {
        subtitles,
        voiceover,
        bgTheme,
      })
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

      {/* 配音音色 */}
      <div className="field">
        <label>🎙️ 配音音色</label>
        <select value={voice} onChange={e => setVoice(e.target.value)} className="select">
          {VOICES.map(v => (
            <option key={v.id} value={v.id}>{v.name}</option>
          ))}
        </select>
      </div>

      {/* 背景主题 */}
      <div className="field">
        <label>🎨 背景主题</label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {THEMES.map(t => (
            <button
              key={t.id}
              onClick={() => setBgTheme(t.id)}
              title={t.name}
              style={{
                width: 32, height: 32, borderRadius: 6,
                background: t.color,
                border: bgTheme === t.id ? '2px solid #00c8ff' : '2px solid #30363d',
                cursor: 'pointer', outline: 'none',
                boxShadow: bgTheme === t.id ? '0 0 8px rgba(0,200,255,0.4)' : 'none',
                transition: 'all 0.2s',
              }}
            />
          ))}
        </div>
      </div>

      {/* 可选开关 */}
      <div className="field">
        <label>⚙️ 生成选项</label>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <ToggleRow
            label="生成字幕"
            checked={subtitles}
            onChange={setSubtitles}
            disabled={!voiceover}
          />
          <ToggleRow
            label="生成配音"
            checked={voiceover}
            onChange={setVoiceover}
          />
        </div>
      </div>

      {/* 信息 */}
      <div style={{ marginTop: 16 }}>
        <p style={{ fontSize: 12, color: '#8b949e', marginBottom: 4 }}>
          场景: {slides.length} 页 | 标题: {title || '未设置'}
        </p>
        <p style={{ fontSize: 12, color: '#8b949e' }}>
          主题: {THEMES.find(t => t.id === bgTheme)?.name} | 音色: {VOICES.find(v => v.id === voice)?.name.split(' ')[0]}
        </p>
      </div>

      {/* 导出按钮 */}
      <button
        onClick={handleExport}
        disabled={exporting || slides.length === 0}
        className="btn btn-primary"
        style={{ width: '100%', marginTop: 12 }}
      >
        {exporting ? '⏳ 生成中...' : '🚀 生成视频'}
      </button>

      {/* 进度条 */}
      {status && (
        <div style={{ marginTop: 16, padding: 12, background: '#161b22', borderRadius: 8 }}>
          <StatusBar status={status} />
        </div>
      )}
    </div>
  )
}

/** Toggle 开关行 */
function ToggleRow({ label, checked, onChange, disabled }: {
  label: string
  checked: boolean
  onChange: (v: boolean) => void
  disabled?: boolean
}) {
  return (
    <label style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '6px 0', cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1,
    }}>
      <span style={{ fontSize: 14 }}>{label}</span>
      <div
        onClick={(e) => {
          if (disabled) return
          e.preventDefault()
          onChange(!checked)
        }}
        style={{
          width: 42, height: 24, borderRadius: 12,
          background: checked ? 'linear-gradient(135deg, #00c8ff, #6366f1)' : '#30363d',
          position: 'relative', cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'background 0.3s',
        }}
      >
        <div style={{
          width: 18, height: 18, borderRadius: '50%', background: '#fff',
          position: 'absolute', top: 3,
          left: checked ? 21 : 3,
          transition: 'left 0.25s cubic-bezier(0.16,1,0.3,1)',
        }} />
      </div>
    </label>
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
      <p style={{ fontSize: 14, fontWeight: 600 }}>
        {labels[status.status] || status.status}
      </p>
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
