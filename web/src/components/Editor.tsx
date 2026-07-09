import { useState } from 'react'
import { parseScript } from '../api'
import type { SlideItem } from '../types'
import Timeline from './Timeline'

interface Props {
  onSlidesChange: (slides: SlideItem[], title: string) => void
  onSlideSelect: (index: number) => void
  currentSlide: number
}

export default function Editor({ onSlidesChange, onSlideSelect, currentSlide }: Props) {
  const [content, setContent] = useState('')
  const [title, setTitleLocal] = useState('')
  const [loading, setLoading] = useState(false)

  const handleParse = async () => {
    if (!content.trim()) return
    setLoading(true)
    try {
      const result = await parseScript(content, title)
      onSlidesChange(result.slides, result.title)
    } catch (err) {
      console.error('解析失败:', err)
      alert('解析失败，请检查后端是否已启动')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="editor">
      <h3>📝 文案编辑</h3>
      <div className="field">
        <label>视频标题</label>
        <input
          type="text"
          value={title}
          onChange={e => setTitleLocal(e.target.value)}
          placeholder="输入视频标题"
          className="input"
        />
      </div>
      <div className="field">
        <label>文案内容</label>
        <p className="hint">用 # 开头标记标题，## 开头标记小标题，空行分隔场景</p>
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder={`# AI Agent 是什么\n\n## 从工具到智能体\n传统的AI工具只能执行单一任务，而AI Agent能够自主感知环境...\n\n## 核心架构\nAgent = LLM + 记忆 + 规划 + 工具调用`}
          rows={16}
          className="textarea"
        />
      </div>
      <button
        onClick={handleParse}
        disabled={loading || !content.trim()}
        className="btn btn-primary"
      >
        {loading ? '解析中...' : '🔍 解析生成场景'}
      </button>

      <Timeline onSlideSelect={onSlideSelect} currentSlide={currentSlide} />
    </div>
  )
}
